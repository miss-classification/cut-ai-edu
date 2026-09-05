"""Execution: Ray Data streaming, or a plain Ray Core actor pool.

Both paths run the same ``CosmosActor``. Which drives a long-lived cosmos
child process. And produce the same manifest rows. They differ only in how
work is fed to the actors.

    ray-data    ds.map_batches over an autoscaling actor pool. Streams, applies
                backpressure, restarts failed actors, and scales the pool with
                the cluster. Use for sweeps.

    actor-pool  A fixed set of actors and an explicit ray.wait dispatch loop.
                Fewer moving parts and results arrive as they finish rather than
                at the end. Use for a handful of tasks, or when debugging.

Tasks are grouped by route_key first, because Control2WorldInference binds its
checkpoint at construction: one pool per (model, hint-key set).
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .actor import CosmosActor
from .env import WorkerEnv
from .pool import code_fingerprint, get_or_create
from .spec import TransferTask, iter_route


def _actor_options(worker_env: WorkerEnv, num_cpus: int) -> dict[str, Any]:
    return {
        "num_gpus": 1,
        "num_cpus": num_cpus,
        "runtime_env": worker_env.runtime_env(),
    }


def _engine_kwargs(
    model_name: str,
    hint_keys: list[str],
    worker_env: WorkerEnv,
    route_key: str,
    disable_guardrails: bool,
    compile_tokenizer: str,
) -> dict[str, Any]:
    safe = route_key.replace("/", "-").replace("|", "_").replace("+", "-")
    return {
        "model_name": model_name,
        "hint_keys": hint_keys,
        "scratch_dir": f"{worker_env.scratch_root}/{safe}",
        "disable_guardrails": disable_guardrails,
        "compile_tokenizer": compile_tokenizer,
        **worker_env.child_kwargs(),
    }


# ---------------------------------------------------------------- Ray Core


def run_actor_pool(
    tasks: list[TransferTask],
    worker_env: WorkerEnv,
    *,
    num_actors: int = 4,
    num_cpus: int = 8,
    disable_guardrails: bool = True,
    compile_tokenizer: str = "none",
    fingerprint: bool = False,
    persist: bool = False,
    on_result=None,
) -> list[dict[str, Any]]:
    import ray

    rows: list[dict[str, Any]] = []

    for route_key, model, hint_keys, group in iter_route(tasks):
        pool_size = min(num_actors, len(group))
        print(f"\n[{route_key}] {len(group)} task(s) across {pool_size} actor(s)", flush=True)

        _check_gpu_capacity(pool_size, persist)

        options = _actor_options(worker_env, num_cpus)
        kwargs = _engine_kwargs(
            model.name, hint_keys, worker_env, route_key, disable_guardrails, compile_tokenizer
        )

        if persist:
            # Detached actors keyed on config plus a hash of this package, so a
            # code or config change never reuses a stale one.
            code_hash = code_fingerprint()
            print("  attaching to warm actors where possible...", flush=True)
            actors, warm_count = [], 0
            for i in range(pool_size):
                handle, was_warm = get_or_create(CosmosActor, options, kwargs, i, code_hash)
                actors.append(handle)
                warm_count += int(was_warm)
            print(f"    {warm_count} of {pool_size} were already warm "
                  f"({'no model load paid' if warm_count == pool_size else 'rest loaded now'})",
                  flush=True)
        else:
            remote_engine = ray.remote(**options)(CosmosActor)
            actors = [remote_engine.remote(**kwargs) for _ in range(pool_size)]
            # Warm up explicitly so model-load time is visible and separate from
            # generation time, and so a broken environment fails before we have
            # queued a hundred tasks behind it.
            print("  loading model on each actor (first load also pulls the checkpoint)...", flush=True)
            for info in ray.get([a.ready.remote() for a in actors]):
                print(
                    f"    {info['host']} gpu={info['cuda_visible_devices']} "
                    f"load={info['load_seconds']}s",
                    flush=True,
                )

        pending: dict[Any, Any] = {}
        queue = list(group)
        idle = list(actors)

        while queue or pending:
            while queue and idle:
                actor = idle.pop()
                task = queue.pop(0)
                pending[actor.run.remote(task.to_json(), fingerprint)] = actor

            if not pending:
                # Every actor in this pool has died and there is nothing in
                # flight to wait on. Without this the loop spins forever on
                # ray.wait([]).
                for task in queue:
                    row = {
                        "name": task.name,
                        "status": "error",
                        "error": "not attempted: every actor in the pool died",
                        "tags": task.tags,
                    }
                    rows.append(row)
                    _print_row(row, len(rows), len(tasks))
                break

            done, _ = ray.wait(list(pending), num_returns=1)
            for ref in done:
                actor = pending.pop(ref)
                try:
                    row = ray.get(ref)
                except Exception as exc:
                    # The actor died mid-task (OOM is the usual cause). Record
                    # it against the run rather than losing the task silently.
                    row = {
                        "name": "<unknown>",
                        "status": "error",
                        "error": f"actor failure: {type(exc).__name__}: {exc}",
                        "host": None,
                    }
                else:
                    idle.append(actor)
                rows.append(_slim(row))
                _print_row(row, len(rows), len(tasks))
                if on_result:
                    on_result(row)

        if persist:
            # Left alive on purpose. They hold GPUs until `cosmos_ray cool`.
            print("  actors left warm. release them with: python -m cosmos_ray cool",
                  flush=True)
        else:
            for actor in actors:
                try:
                    ray.get(actor.shutdown.remote(), timeout=60)
                except Exception:
                    pass
                ray.kill(actor)

    return rows


def _check_gpu_capacity(needed: int, persist: bool) -> None:
    """Fail fast when the GPUs are already taken.

    Ray queues an actor it cannot place, forever and silently, so a run whose
    GPUs are held by warm actors from an earlier session simply hangs. That is
    indistinguishable from slow generation. Say so instead.
    """
    import ray

    from .pool import list_pool

    free = int(ray.available_resources().get("GPU", 0))
    if free >= needed:
        return

    warm = list_pool()
    print(f"\n  only {free} of {needed} GPUs are free.", flush=True)
    if warm:
        print(f"  {len(warm)} warm actor(s) are holding GPUs from an earlier run:", flush=True)
        for name in warm[:6]:
            print(f"    {name}", flush=True)
        print("\n  release them with:  python -m cosmos_ray cool", flush=True)
        raise SystemExit(
            "refusing to queue actors that cannot be placed. Run `cosmos_ray cool` "
            "or lower -n."
        )
    print("  something else on the cluster is using them. Check `ray status`.", flush=True)
    raise SystemExit("refusing to queue actors that cannot be placed. Lower -n or wait.")


# ---------------------------------------------------------------- Ray Data


def run_ray_data(
    tasks: list[TransferTask],
    worker_env: WorkerEnv,
    *,
    concurrency: int = 4,
    num_cpus: int = 8,
    disable_guardrails: bool = True,
    compile_tokenizer: str = "none",
    fingerprint: bool = False,
) -> list[dict[str, Any]]:
    import ray
    import ray.data

    rows: list[dict[str, Any]] = []

    for route_key, model, hint_keys, group in iter_route(tasks):
        pool = min(concurrency, len(group))
        print(f"\n[{route_key}] {len(group)} task(s), actor pool concurrency={pool}", flush=True)

        dataset = ray.data.from_items([{"task_json": task.to_json()} for task in group])
        result = dataset.map_batches(
            CosmosActor,
            fn_constructor_kwargs={
                **_engine_kwargs(
                    model.name, hint_keys, worker_env, route_key,
                    disable_guardrails, compile_tokenizer,
                ),
                "fingerprint": fingerprint,
            },
            # One video per call. Batching buys nothing here: the pipeline
            # generates sequentially inside generate() anyway, and a batch of 1
            # means a failure costs one video rather than the whole batch.
            batch_size=1,
            # ActorPoolStrategy, not concurrency=: the latter is deprecated
            # from Ray 2.51. A fixed size keeps every actor's model load paid
            # exactly once; an autoscaling pool would re-pay ~180s per new actor.
            compute=ray.data.ActorPoolStrategy(size=pool),
            num_gpus=1,
            num_cpus=num_cpus,
            # map_batches collects unknown kwargs into ray_remote_args itself,
            # so runtime_env is passed directly. Wrapping it in a
            # ray_remote_args dict is rejected as an invalid actor option.
            runtime_env=worker_env.runtime_env(),
        )

        for record in result.take_all():
            row = _slim(json.loads(record["result_json"]))
            rows.append(row)
            _print_row(row, len(rows), len(tasks))

    return rows


# ---------------------------------------------------------------- reporting

_STATUS_MARK = {"ok": "OK ", "guardrail_blocked": "BLOCKED", "error": "ERROR"}


def _slim(row: dict[str, Any]) -> dict[str, Any]:
    """Drop the bulky part of a fingerprint before it reaches the manifest.

    per_frame_mean is ~93 floats and is exactly what luma-delta analysis needs,
    so it stays. The 8x8 pooled grid is ~6k floats per video and is only needed
    by the equivalence test, which reads it straight off the wire.
    """
    fp = row.get("fingerprint")
    if isinstance(fp, dict) and "pooled" in fp:
        row = dict(row)
        row["fingerprint"] = {k: v for k, v in fp.items() if k != "pooled"}
    return row


def _print_row(row: dict[str, Any], index: int, total: int) -> None:
    mark = _STATUS_MARK.get(row.get("status", "error"), "?")
    name = row.get("name")
    seconds = row.get("seconds")
    suffix = f"  {seconds}s" if seconds is not None else ""
    print(f"  [{index}/{total}] {mark:8} {name}{suffix}", flush=True)
    if row.get("status") != "ok" and row.get("error"):
        print(f"           {row['error']}", flush=True)


def write_manifest(rows: list[dict[str, Any]], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")
    return path


def summarise_results(rows: list[dict[str, Any]]) -> str:
    counts: dict[str, int] = {}
    for row in rows:
        status = row.get("status", "error")
        counts[status] = counts.get(status, 0) + 1

    durations = [r["seconds"] for r in rows if r.get("status") == "ok" and r.get("seconds")]
    lines = ["", "=" * 62, "RESULTS"]
    for status in ("ok", "guardrail_blocked", "error"):
        if counts.get(status):
            lines.append(f"  {status:20} {counts[status]}")
    if durations:
        lines.append(f"  mean generate time   {sum(durations) / len(durations):.1f}s")

    failures = [r for r in rows if r.get("status") != "ok"]
    if failures:
        lines.append("")
        lines.append("  not produced:")
        for row in failures:
            lines.append(f"    {row.get('name')}: {row.get('error', '')[:110]}")
    lines.append("=" * 62)
    return "\n".join(lines)
