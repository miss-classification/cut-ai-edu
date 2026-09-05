"""Ray orchestration for Cosmos Transfer 2.5 inference.

Layering, which is the whole point of this package:

    spec.py / sweeps.py   driver-safe. No cosmos, no torch, no ray. Runs on the
                          py3.12 head node.
    env.py                builds the runtime_env that puts a worker process
                          inside the cosmos venv.
    engine.py             worker-side. Imports cosmos_transfer2 and holds the
                          model in memory across many tasks.
    runner.py             Ray Data and Ray Core execution over engine actors.
"""

from .spec import ControlSpec, ModelSpec, SpecError, TransferTask

__all__ = ["ControlSpec", "ModelSpec", "SpecError", "TransferTask"]
