"""Does a warm actor render the same video as a fresh process?

A long-lived actor carries state across generations. If any of that state feeds
the sampler. A global RNG advanced by the previous render, a cached buffer, a
compiled kernel specialised on the last shape. Then the fifth video from an
actor differs from the first, silently. Nothing errors. The grid just stops
being a controlled experiment, because "which actor rendered this, and how many
renders in" becomes an uncontrolled variable sitting alongside the intended one
to vary.

That risk is created by the optimisation this whole package exists for: loading
the model once and reusing it. So it has to be measured, not assumed.

The experiment
--------------
The same spec is rendered four times across two actors:

    actor A, position 0     "fresh process"
    actor B, position 0     "first in a batch"
    actor B, position 1     (filler task in between)
    actor B, position 2     "last in a batch"

Two comparisons matter and they answer different questions:

    A0 vs B0    two fresh actors, same position. Isolates plain GPU/process
                nondeterminism. The floor below which nothing can be
                attributed to residency.
    B0 vs B2    same actor, different positions. Anything above the A0/B0 floor
                is attributable to reuse.

Reporting, not judging
----------------------
This prints numbers and does not pass or fail. Bit-exactness is the strongest
claim available, but GPU kernels are frequently nondeterministic on their own,
so a sha mismatch between A0 and B0 says nothing about actor reuse. The
comparison that carries information is whether B0-vs-B2 divergence exceeds the
A0-vs-B0 floor. Where to put a threshold is a judgement about the experiment
being run, so it is left to the caller.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def compare(left: dict, right: dict) -> dict[str, Any]:
    """Numeric distance between two fingerprints."""
    import numpy as np

    result: dict[str, Any] = {
        "bit_exact": left["sha256"] == right["sha256"],
        "same_shape": left["shape"] == right["shape"],
    }
    if not result["same_shape"]:
        result["note"] = f"shapes differ: {left['shape']} vs {right['shape']}"
        return result

    left_pooled = np.array(left["pooled"], dtype=np.float64)
    right_pooled = np.array(right["pooled"], dtype=np.float64)
    delta = np.abs(left_pooled - right_pooled)

    left_mean = np.array(left["per_frame_mean"], dtype=np.float64)
    right_mean = np.array(right["per_frame_mean"], dtype=np.float64)

    # Pixel values are 0-255, so these are directly interpretable as levels.
    result.update(
        {
            "pooled_max_abs": float(delta.max()),
            "pooled_mean_abs": float(delta.mean()),
            "frame_mean_max_abs": float(np.abs(left_mean - right_mean).max()),
            "frames_differing": int((delta.max(axis=1) > 1e-6).sum()),
            "frames_total": int(delta.shape[0]),
        }
    )
    return result


def run_experiment(
    task,
    worker_env,
    *,
    filler,
    batch_positions: int = 3,
    num_cpus: int = 8,
) -> dict[str, Any]:
    """Render `task` fresh and at both ends of a batch. Returns fingerprints."""
    import ray

    from .actor import CosmosActor
    from .runner import _actor_options, _engine_kwargs

    route_key = task.route_key
    kwargs = _engine_kwargs(
        task.model.name, task.hint_keys, worker_env, route_key,
        disable_guardrails=True, compile_tokenizer="none",
    )
    remote = ray.remote(**_actor_options(worker_env, num_cpus))(CosmosActor)

    actor_fresh = remote.remote(**kwargs)
    actor_batch = remote.remote(**kwargs)
    ray.get([actor_fresh.ready.remote(), actor_batch.ready.remote()])

    print("  rendering A0 (fresh process) and B0 (first in batch)...", flush=True)
    a0, b0 = ray.get(
        [
            actor_fresh.run.remote(task.to_json(), True),
            actor_batch.run.remote(task.to_json(), True),
        ]
    )

    # Filler renders advance actor B's internal state without touching the spec
    # under test. Distinct names so nothing overwrites the measured output.
    for position in range(1, batch_positions - 1):
        print(f"  advancing actor B with filler render {position}...", flush=True)
        ray.get(actor_batch.run.remote(filler(position).to_json(), False))

    print(f"  rendering B{batch_positions - 1} (last in batch)...", flush=True)
    b_last = ray.get(actor_batch.run.remote(task.to_json(), True))

    for actor in (actor_fresh, actor_batch):
        try:
            ray.get(actor.shutdown.remote(), timeout=60)
        except Exception:
            pass
        ray.kill(actor)

    return {"A0": a0, "B0": b0, f"B{batch_positions - 1}": b_last}


def report(results: dict[str, Any], batch_positions: int) -> dict[str, Any]:
    last_key = f"B{batch_positions - 1}"
    rows = {}
    for key, row in results.items():
        if row.get("status") != "ok":
            print(f"\n{key}: FAILED. {row.get('error')}", file=sys.stderr)
            return {"ok": False, "results": results}
        if "fingerprint" not in row:
            print(f"\n{key}: no fingerprint. {row.get('fingerprint_error')}", file=sys.stderr)
            return {"ok": False, "results": results}
        rows[key] = row

    floor = compare(rows["A0"]["fingerprint"], rows["B0"]["fingerprint"])
    residency = compare(rows["B0"]["fingerprint"], rows[last_key]["fingerprint"])

    print("\n" + "=" * 66)
    print("EQUIVALENCE")
    print("=" * 66)
    print(f"  A0 vs B0        two fresh actors  (nondeterminism floor)")
    print(f"      bit exact          {floor['bit_exact']}")
    print(f"      pooled max abs     {floor.get('pooled_max_abs'):.6f}  (0-255 levels)")
    print(f"      frames differing   {floor.get('frames_differing')}/{floor.get('frames_total')}")
    print(f"\n  B0 vs {last_key}        same actor, position 0 vs {batch_positions - 1}")
    print(f"      bit exact          {residency['bit_exact']}")
    print(f"      pooled max abs     {residency.get('pooled_max_abs'):.6f}")
    print(f"      frames differing   {residency.get('frames_differing')}/{residency.get('frames_total')}")

    floor_max = floor.get("pooled_max_abs", 0.0)
    reuse_max = residency.get("pooled_max_abs", 0.0)
    print("\n  interpretation")
    if residency["bit_exact"]:
        print("      Reuse is bit-exact. Actor position does not affect output.")
    elif floor_max <= 0.0 and reuse_max > 0.0:
        print("      Fresh actors agree bit-exactly but reuse does not:")
        print("      divergence is attributable to residency. Treat actor")
        print("      position as an uncontrolled variable until fixed.")
    elif reuse_max <= floor_max:
        print(f"      Reuse divergence ({reuse_max:.6f}) is at or below the")
        print(f"      nondeterminism floor ({floor_max:.6f}). No evidence that")
        print("      residency changes output beyond ambient nondeterminism.")
    else:
        ratio = reuse_max / floor_max if floor_max else float("inf")
        print(f"      Reuse divergence ({reuse_max:.6f}) exceeds the floor")
        print(f"      ({floor_max:.6f}) by {ratio:.1f}x. Suggests residency")
        print("      contributes beyond ambient nondeterminism.")
    print("=" * 66)

    return {
        "ok": True,
        "nondeterminism_floor": floor,
        "residency_effect": residency,
        "positions": {k: {"seconds": v["seconds"], "sha256": v["fingerprint"]["sha256"]}
                      for k, v in rows.items()},
    }


def main(argv: list[str] | None = None) -> int:
    from .cli import REPO_ROOT, _worker_env
    from .sweeps import expand, load_experiment

    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("experiment", help="experiment file; its first task is the spec under test")
    parser.add_argument("--venv-root", default=None)
    parser.add_argument("--venv-tag", default=None)
    parser.add_argument("--venv-path", default=None)
    parser.add_argument("--hf-home", default=None)
    parser.add_argument("--cosmos-src", default=None)
    parser.add_argument("--scratch-root", default=None)
    parser.add_argument("--unfused-attention", action="store_true")
    parser.add_argument("--positions", type=int, default=3,
                        help="renders in actor B; the spec is measured at 0 and positions-1")
    parser.add_argument("--num-cpus", type=int, default=8)
    parser.add_argument("--out", default=None, help="write the report as JSON here")
    args = parser.parse_args(argv)

    # Fill unset paths from the same defaults the CLI uses.
    from .env import (
        DEFAULT_COSMOS_SRC,
        DEFAULT_HF_HOME,
        DEFAULT_SCRATCH_ROOT,
        DEFAULT_VENV_ROOT,
        DEFAULT_VENV_TAG,
    )

    args.venv_root = args.venv_root or DEFAULT_VENV_ROOT
    args.venv_tag = args.venv_tag or DEFAULT_VENV_TAG
    args.hf_home = args.hf_home or DEFAULT_HF_HOME
    args.cosmos_src = args.cosmos_src or DEFAULT_COSMOS_SRC
    args.scratch_root = args.scratch_root or DEFAULT_SCRATCH_ROOT

    tasks = expand(load_experiment(args.experiment))
    task = tasks[0]
    print(f"spec under test: {task.name}  ({task.route_key})")

    import dataclasses

    def filler(index: int):
        return dataclasses.replace(task, name=f"{task.name}__filler{index}")

    worker_env = _worker_env(args)
    problems = worker_env.preflight()
    if problems:
        for problem in problems:
            print(f"  BLOCKER {problem}", file=sys.stderr)
        return 1

    import tempfile

    import ray

    with tempfile.TemporaryDirectory(prefix="cosmos-ray-eq-") as empty:
        ray.init(address="auto", runtime_env=worker_env.job_runtime_env(empty))
        results = run_experiment(
            task, worker_env, filler=filler,
            batch_positions=args.positions, num_cpus=args.num_cpus,
        )

    summary = report(results, args.positions)
    if args.out:
        Path(args.out).write_text(json.dumps(summary, indent=2))
        print(f"\nwrote {args.out}")
    return 0 if summary.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
