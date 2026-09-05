"""The cosmos-side worker process. Runs under the cosmos venv interpreter.

Why this exists
---------------
The plan was one process: a Ray actor started with
``runtime_env={"py_executable": <cosmos venv>/bin/python}``, importing cosmos
directly. The cluster makes that impossible:

    Ray requires a worker's python minor version to match the cluster's (3.12).
    cosmos requires 3.10 or 3.13. Natten ships cp310 wheels only for
    cu130_torch29, and the working venv here is 3.13.

There is no version satisfying both. So the Ray actor stays on the cluster's
python and drives *this* process, which runs on the cosmos python and holds the
model. The important property survives: the model loads once and serves many
tasks. Only the process boundary is different.

Protocol
--------
Requests arrive as JSON lines on stdin. Replies leave as JSON lines on a
dedicated file descriptor named by $COSMOS_RAY_RESULT_FD. *not* stdout,
because cosmos logs to stdout freely and would corrupt the stream. stdout and
stderr stay free for logs, which Ray captures for debugging.

    -> {"op": "init", ...engine kwargs...}      <- {"ok": true, "info": {...}}
    -> {"op": "run", "task_json": "..."}        <- {"ok": true, "row": {...}}
    -> {"op": "shutdown"}                       (process exits)
"""

from __future__ import annotations

import json
import os
import sys
import traceback


def _reply(out, payload: dict) -> None:
    out.write(json.dumps(payload) + "\n")
    out.flush()


def main() -> int:
    fd = int(os.environ["COSMOS_RAY_RESULT_FD"])
    out = os.fdopen(fd, "w")

    engine = None
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            op = request.get("op")

            if op == "shutdown":
                _reply(out, {"ok": True, "bye": True})
                return 0

            if op == "init":
                # Imported here, not at module scope: the import is expensive
                # and pulls in torch, so it must happen after we are certain we
                # are the child and have been told what to load.
                from cosmos_ray.engine import TransferEngine

                kwargs = dict(request)
                kwargs.pop("op", None)
                engine = TransferEngine(**kwargs)
                _reply(out, {"ok": True, "info": engine.ready()})
                continue

            if op == "run":
                if engine is None:
                    _reply(out, {"ok": False, "error": "run before init"})
                    continue
                # TransferEngine.run never raises; it returns a status row.
                _reply(
                    out,
                    {
                        "ok": True,
                        "row": engine.run(
                            request["task_json"],
                            fingerprint=request.get("fingerprint", False),
                        ),
                    },
                )
                continue

            _reply(out, {"ok": False, "error": f"unknown op {op!r}"})

        except Exception as exc:
            _reply(
                out,
                {
                    "ok": False,
                    "error": f"{type(exc).__name__}: {exc}",
                    "traceback": traceback.format_exc()[-4000:],
                },
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
