"""Worker-side inference engine. Runs inside the cosmos venv.

This module imports cosmos_transfer2 at construction time, so it must only ever
be instantiated in a process started with the cosmos ``py_executable``. The
driver imports nothing from here except the class object itself, which Ray ships
by reference.

The single most important property: ``Control2WorldInference`` is built once, in
``__init__``, and reused for every task the actor receives. Model load is
minutes; generation is ~60s. The original scripts paid the former for each of
the latter.

The second most important property: ``run()`` always returns a status row and
never raises. A sample that the video guardrail rejects comes back from
``generate()`` as an empty list with no exception and no log line. That is how
seven of nine historical runs reported success while producing no video. Here it
becomes ``status="guardrail_blocked"`` in the manifest.
"""

from __future__ import annotations

import json
import os
import socket
import time
import traceback
from pathlib import Path
from typing import Any

from .spec import TransferTask


class TransferEngine:
    """Holds one loaded cosmos model and runs tasks against it."""

    def __init__(
        self,
        model_name: str,
        hint_keys: list[str],
        scratch_dir: str,
        *,
        disable_guardrails: bool = True,
        offload_guardrail_models: bool = False,
        compile_tokenizer: str = "none",
        benchmark: bool = False,
    ) -> None:
        from cosmos_oss.init import init_environment, init_output_dir

        init_environment()

        from cosmos_transfer2.config import SetupArguments
        from cosmos_transfer2.inference import Control2WorldInference

        self.scratch_dir = Path(scratch_dir)
        self.scratch_dir.mkdir(parents=True, exist_ok=True)

        # Called exactly once per actor. Calling it per task would add a fresh
        # pair of loguru file sinks on every call and leak handles for the life
        # of the actor.
        init_output_dir(self.scratch_dir)

        self.model_name = model_name
        self.hint_keys = list(hint_keys)
        self.host = socket.gethostname()

        # `model` must be passed explicitly: SetupArguments has a mode="before"
        # validator that raises "model is required" when the key is absent,
        # which fires before pydantic would apply the field default.
        self.setup_args = SetupArguments(
            model=model_name,
            output_dir=self.scratch_dir,
            disable_guardrails=disable_guardrails,
            offload_guardrail_models=offload_guardrail_models,
            compile_tokenizer=compile_tokenizer,
            benchmark=benchmark,
            # We detect and report a dropped sample ourselves, per task, rather
            # than letting a batch abort. Never silently.
            keep_going=True,
        )

        started = time.time()
        self.inference = Control2WorldInference(self.setup_args, batch_hint_keys=self.hint_keys)
        self.load_seconds = round(time.time() - started, 1)
        self.tasks_run = 0

    # introspection

    def ready(self) -> dict[str, Any]:
        """Force a round trip so the caller knows the model is resident."""
        return {
            "host": self.host,
            "model": self.model_name,
            "hint_keys": self.hint_keys,
            "load_seconds": self.load_seconds,
            "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
            "gpu_memory_gb": self._gpu_memory_gb(),
        }

    def _gpu_memory_gb(self) -> float | None:
        try:
            import torch

            if not torch.cuda.is_available():
                return None
            return round(torch.cuda.max_memory_allocated() / 1024**3, 2)
        except Exception:
            return None

    # the unit of work

    def _decode(self, path: str):
        """Decode a video to a (T, H, W, 3) uint8 array, inside the cosmos venv."""
        import numpy as np

        try:
            import decord

            reader = decord.VideoReader(path)
            return reader.get_batch(range(len(reader))).asnumpy()
        except Exception:
            import imageio.v3 as iio

            return np.asarray(iio.imread(path, plugin="pyav"))

    def fingerprint(self, path: str) -> dict[str, Any]:
        """A compact numeric summary of a rendered video.

        Exists so equivalence testing never has to move video files: the head
        node has no ffmpeg, and shipping clips back to compare them would be
        both slow and beside the point.

        Reports rather than judges. sha256 answers 'bit-exact?', which GPU
        nondeterminism alone can break; the pooled statistics say *how far
        apart* two renders are, which is the question that actually matters
        when deciding whether actor reuse changed the output.
        """
        import hashlib

        import numpy as np

        frames = self._decode(path)
        sha = hashlib.sha256(np.ascontiguousarray(frames).tobytes()).hexdigest()
        gray = frames.astype(np.float32).mean(axis=3)
        count, height, width = gray.shape
        block_h, block_w = height // 8, width // 8
        pooled = (
            gray[:, : block_h * 8, : block_w * 8]
            .reshape(count, 8, block_h, 8, block_w)
            .mean(axis=(2, 4))
        )
        return {
            "sha256": sha,
            "shape": list(frames.shape),
            "per_frame_mean": gray.mean(axis=(1, 2)).tolist(),
            # Spatial standard deviation per frame, averaged. Falls when an image
            # flattens, which is what fog does. Brightness cannot see that, and
            # for fog it moves the opposite way to night.
            "contrast": float(gray.std(axis=(1, 2)).mean()),
            "pooled": pooled.reshape(count, -1).tolist(),
        }

    def run(self, task_json: str, fingerprint: bool = False) -> dict[str, Any]:
        """Generate one video. Always returns a row; never raises."""
        started = time.time()
        row: dict[str, Any] = {
            "name": None,
            "status": "error",
            "output_path": None,
            "error": None,
            "traceback": None,
            "seconds": None,
            "host": self.host,
            "model": self.model_name,
            "load_seconds": self.load_seconds,
            "actor_task_index": self.tasks_run,
            "tags": {},
        }
        self.tasks_run += 1

        try:
            task = TransferTask.from_json(task_json)
            row["name"] = task.name
            row["tags"] = task.tags

            from cosmos_transfer2.config import InferenceArguments

            sample = InferenceArguments(**task.to_inference_kwargs())
            output_dir = Path(task.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            produced = self.inference.generate([sample], output_dir)

            if produced:
                row["status"] = "ok"
                row["output_path"] = produced[0]
            else:
                # generate() drops a sample and returns no path only when
                # _generate_sample returned None, which happens on a guardrail
                # rejection under keep_going. There is no log line for it.
                row["status"] = "guardrail_blocked"
                row["error"] = (
                    "no output produced: the text or video guardrail rejected this sample. "
                    "Re-run with guardrails disabled, or inspect the prompt/output."
                )
        except Exception as exc:
            row["error"] = f"{type(exc).__name__}: {exc}"
            row["traceback"] = traceback.format_exc()[-4000:]

        if fingerprint and row["status"] == "ok" and row["output_path"]:
            try:
                row["fingerprint"] = self.fingerprint(row["output_path"])
            except Exception as exc:
                row["fingerprint_error"] = f"{type(exc).__name__}: {exc}"

        row["seconds"] = round(time.time() - started, 1)
        row["gpu_memory_gb"] = self._gpu_memory_gb()
        return row

    # Ray Data adapter

    def __call__(self, batch: dict[str, Any]) -> dict[str, Any]:
        """map_batches entry point. One JSON column in, one JSON column out."""
        import numpy as np

        results = [json.dumps(self.run(str(blob))) for blob in batch["task_json"]]
        return {"result_json": np.array(results, dtype=object)}
