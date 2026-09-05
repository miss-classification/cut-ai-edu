"""The Ray actor. Runs on the cluster's python and drives a cosmos child process.

This is the parent half of the split described in child.py. It presents exactly
the interface the runners want. ``ready()`` and ``run(task_json)`` returning a
status row. So the execution code does not care that a process boundary
exists. It holds one child for its whole life, so the model still loads once.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import time
from pathlib import Path
from typing import Any


class ChildDied(RuntimeError):
    """The cosmos process exited. Its tail of stdout is attached, since that is
    where the real cause (OOM, CUDA error, import failure) will be."""


class CosmosActor:
    """Owns one long-lived cosmos process."""

    def __init__(
        self,
        model_name: str,
        hint_keys: list[str],
        scratch_dir: str,
        *,
        child_python: str,
        cosmos_src: str,
        child_env: dict[str, str] | None = None,
        disable_guardrails: bool = True,
        compile_tokenizer: str = "none",
        fingerprint: bool = False,
        startup_timeout: float = 3600.0,
    ) -> None:
        # Ray Data constructs actors itself and calls __call__, so it cannot pass
        # per call arguments. Carrying the flag on the instance is what lets
        # --fingerprint work on that engine instead of being silently dropped.
        self.fingerprint_default = fingerprint
        self.host = socket.gethostname()
        self.model_name = model_name
        self.tasks_run = 0
        self._log_path = Path(scratch_dir) / "child.log"
        self._log_path.parent.mkdir(parents=True, exist_ok=True)

        env = dict(os.environ)
        env.update(child_env or {})
        # The child must find cosmos_ray itself; cosmos comes from its venv.
        env["PYTHONPATH"] = cosmos_src + (":" + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        env["PYTHONUNBUFFERED"] = "1"

        read_fd, write_fd = os.pipe()
        env["COSMOS_RAY_RESULT_FD"] = str(write_fd)

        self._log = open(self._log_path, "wb")
        self._proc = subprocess.Popen(
            [child_python, "-m", "cosmos_ray.child"],
            stdin=subprocess.PIPE,
            stdout=self._log,
            stderr=subprocess.STDOUT,
            env=env,
            cwd=cosmos_src,
            pass_fds=(write_fd,),
        )
        # The parent must drop its copy of the write end, or reading the pipe
        # would never see EOF when the child dies.
        os.close(write_fd)
        self._replies = os.fdopen(read_fd, "r")

        started = time.time()
        reply = self._exchange(
            {
                "op": "init",
                "model_name": model_name,
                "hint_keys": hint_keys,
                "scratch_dir": scratch_dir,
                "disable_guardrails": disable_guardrails,
                "compile_tokenizer": compile_tokenizer,
            },
            timeout=startup_timeout,
        )
        if not reply.get("ok"):
            raise ChildDied(
                f"cosmos child failed to initialise: {reply.get('error')}\n"
                f"{reply.get('traceback', '')}\n--- child log ---\n{self._tail()}"
            )
        self.info = reply["info"]
        self.load_seconds = round(time.time() - started, 1)

    # interface used by the runners

    def ready(self) -> dict[str, Any]:
        info = dict(self.info)
        info["load_seconds"] = self.load_seconds
        info["host"] = self.host
        info["child_log"] = str(self._log_path)
        return info

    def run(self, task_json: str, fingerprint: bool = False) -> dict[str, Any]:
        self.tasks_run += 1
        try:
            reply = self._exchange(
                {"op": "run", "task_json": task_json, "fingerprint": fingerprint}
            )
        except ChildDied as exc:
            return {
                "name": json.loads(task_json).get("name"),
                "status": "error",
                "error": str(exc)[:2000],
                "host": self.host,
                "model": self.model_name,
            }
        if not reply.get("ok"):
            return {
                "name": json.loads(task_json).get("name"),
                "status": "error",
                "error": reply.get("error"),
                "traceback": reply.get("traceback"),
                "host": self.host,
                "model": self.model_name,
            }
        return reply["row"]

    def __call__(self, batch: dict[str, Any]) -> dict[str, Any]:
        """Ray Data map_batches entry point. One JSON column in, one out."""
        import numpy as np

        results = [
            json.dumps(self.run(str(blob), self.fingerprint_default))
            for blob in batch["task_json"]
        ]
        return {"result_json": np.array(results, dtype=object)}

    def shutdown(self) -> None:
        try:
            if self._proc.poll() is None:
                self._proc.stdin.write(b'{"op": "shutdown"}\n')
                self._proc.stdin.flush()
                self._proc.wait(timeout=30)
        except Exception:
            self._proc.kill()
        finally:
            self._log.close()

    # plumbing

    def _exchange(self, request: dict, timeout: float | None = None) -> dict:
        if self._proc.poll() is not None:
            raise ChildDied(
                f"cosmos child already exited with code {self._proc.returncode}\n"
                f"--- child log ---\n{self._tail()}"
            )
        try:
            self._proc.stdin.write((json.dumps(request) + "\n").encode())
            self._proc.stdin.flush()
        except BrokenPipeError:
            raise ChildDied(
                f"cosmos child closed its input (exit code {self._proc.poll()})\n"
                f"--- child log ---\n{self._tail()}"
            ) from None

        line = self._replies.readline()
        if not line:
            # EOF on the reply pipe means the child is gone.
            self._proc.wait(timeout=30)
            raise ChildDied(
                f"cosmos child died (exit code {self._proc.returncode}); this is "
                f"usually CUDA OOM or a checkpoint failure\n"
                f"--- child log ---\n{self._tail()}"
            )
        return json.loads(line)

    def _tail(self, limit: int = 3000) -> str:
        try:
            self._log.flush()
            return self._log_path.read_text(errors="replace")[-limit:]
        except Exception:
            return "(no child log)"
