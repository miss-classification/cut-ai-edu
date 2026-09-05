"""Actors that survive between runs, so the model loads once per session.

A normal run builds actors, loads the model, generates, and throws the actors
away. The load is 54s from a local venv and 174s from the shared one, paid every
time. Detached named actors let the next run attach to what is already there, so
the second run starts generating immediately.

That is a real speedup and a real hazard, so three things are deliberate here.

THE NAME ENCODES EVERYTHING THAT AFFECTS OUTPUT
    Model, hint keys, guardrail setting, compile mode, which interpreter the
    child runs, and a hash of the cosmos_ray source that was shipped. Change any
    of them and the name changes, so a stale actor is never silently reused. In
    particular a warm actor holds the code it started with, so editing engine.py
    must not quietly keep running the old version.

THEY HOLD GPUS UNTIL TOLD OTHERWISE
    A detached actor outlives the notebook that made it. Four of them occupy
    four GPUs indefinitely and everything else queues behind them. Release with
    `python -m cosmos_ray cool`.

EXISTING IS NOT THE SAME AS HEALTHY
    An actor whose child process has wedged still resolves by name. Every reuse
    calls ready() first and rebuilds on failure.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

NAMESPACE = "cosmos_ray"
PREFIX = "cosmos:"


def code_fingerprint(package_dir: str | Path | None = None) -> str:
    """Short hash of the cosmos_ray sources that a child process would import.

    Included in actor names so that editing this package invalidates warm
    actors instead of leaving them running last week's engine.
    """
    root = Path(package_dir) if package_dir else Path(__file__).resolve().parent
    digest = hashlib.sha256()
    for path in sorted(root.glob("*.py")):
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()[:8]


def actor_name(engine_kwargs: dict[str, Any], code_hash: str) -> str:
    """A name that changes whenever anything affecting the output changes."""
    model = str(engine_kwargs.get("model_name", "?")).replace("/", "-")
    keys = "-".join(engine_kwargs.get("hint_keys") or [])
    # Everything else that changes behaviour goes into the hash, including the
    # child interpreter and the guardrail setting.
    material = json.dumps(
        {k: str(v) for k, v in sorted(engine_kwargs.items()) if k != "scratch_dir"},
        sort_keys=True,
    )
    short = hashlib.sha256(material.encode()).hexdigest()[:6]
    return f"{PREFIX}{model}:{keys}:{code_hash}:{short}"


def get_or_create(actor_cls, options: dict[str, Any], engine_kwargs: dict[str, Any],
                  index: int, code_hash: str, ready_timeout: float = 3600.0):
    """Attach to a warm actor if one is healthy, otherwise build a fresh one.

    Returns (handle, was_warm).
    """
    import ray

    name = f"{actor_name(engine_kwargs, code_hash)}:{index}"
    remote_cls = ray.remote(**options)(actor_cls)

    try:
        handle = ray.get_actor(name, namespace=NAMESPACE)
    except Exception:
        handle = None

    if handle is not None:
        try:
            ray.get(handle.ready.remote(), timeout=120)
            return handle, True
        except Exception:
            # Resolvable but not usable. Most likely a wedged or dead child.
            print(f"  {name} exists but is not responding, rebuilding", flush=True)
            try:
                ray.kill(handle)
            except Exception:
                pass

    handle = remote_cls.options(
        name=name, lifetime="detached", namespace=NAMESPACE, get_if_exists=False
    ).remote(**engine_kwargs)
    ray.get(handle.ready.remote(), timeout=ready_timeout)
    return handle, False


def list_pool() -> list[str]:
    """Names of our detached actors currently alive."""
    import ray
    from ray.util import list_named_actors

    try:
        names = list_named_actors(all_namespaces=True)
    except Exception:
        return []
    out = []
    for entry in names:
        name = entry.get("name") if isinstance(entry, dict) else entry
        ns = entry.get("namespace") if isinstance(entry, dict) else None
        if name and str(name).startswith(PREFIX) and (ns in (None, NAMESPACE)):
            out.append(str(name))
    return sorted(out)


def cool(names: list[str] | None = None) -> list[str]:
    """Kill warm actors and release their GPUs. Returns what was killed."""
    import ray

    targets = names if names is not None else list_pool()
    killed = []
    for name in targets:
        try:
            handle = ray.get_actor(name, namespace=NAMESPACE)
        except Exception:
            continue
        try:
            ray.get(handle.shutdown.remote(), timeout=60)
        except Exception:
            pass
        try:
            ray.kill(handle)
            killed.append(name)
        except Exception:
            pass
    return killed
