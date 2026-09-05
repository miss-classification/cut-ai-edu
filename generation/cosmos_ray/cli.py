"""Command line entry point.

    python -m cosmos_ray plan experiments/car_weather.yaml
    python -m cosmos_ray run  experiments/wcht.yaml
    python -m cosmos_ray run  experiments/car_weather.yaml --engine actor-pool -n 4

``plan`` needs no cluster and no cosmos install: it expands the sweep, validates
every task, and checks that the inputs are real files rather than unfetched
git-lfs stubs. Run it before anything else.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from .env import (
    DEFAULT_COSMOS_SRC,
    DEFAULT_HF_HOME,
    DEFAULT_SCRATCH_ROOT,
    DEFAULT_VENV_ROOT,
    DEFAULT_VENV_TAG,
    WorkerEnv,
)
from .spec import SHARED_PREFIXES, SpecError, missing_inputs, unreachable_inputs
from .sweeps import expand, load_experiment, summarise

REPO_ROOT = Path(__file__).resolve().parent.parent


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("experiment", help="path to an experiment .yaml/.json")
    parser.add_argument("--venv-root", default=DEFAULT_VENV_ROOT)
    parser.add_argument("--venv-tag", default=DEFAULT_VENV_TAG)
    parser.add_argument(
        "--venv-path",
        default=None,
        help="use this venv directly instead of --venv-root/--venv-tag, e.g. "
             "e.g. a venv that already exists on the worker node",
    )
    parser.add_argument("--hf-home", default=DEFAULT_HF_HOME)
    parser.add_argument(
        "--cosmos-src",
        default=DEFAULT_COSMOS_SRC,
        help="repo checkout the cosmos child process imports cosmos_ray from",
    )
    parser.add_argument("--scratch-root", default=DEFAULT_SCRATCH_ROOT)
    parser.add_argument(
        "--unfused-attention",
        action="store_true",
        help="force the Transformer-Engine unfused attention path (NVTE_*)",
    )


def _worker_env(args: argparse.Namespace) -> WorkerEnv:
    return WorkerEnv(
        venv_root=args.venv_root,
        venv_tag=args.venv_tag,
        venv_path_override=args.venv_path,
        hf_home=args.hf_home,
        cosmos_src=args.cosmos_src,
        scratch_root=args.scratch_root,
        py_modules=[str(REPO_ROOT / "cosmos_ray")],
        force_unfused_attention=args.unfused_attention,
    )


def _load(args: argparse.Namespace):
    config = load_experiment(args.experiment)
    tasks = expand(config)
    # Remember the run root before the by_tag layout pushes each task into its
    # own subdirectory; the manifest and index belong at the top.
    args.run_root = config["output_dir"]
    print(summarise(tasks))
    return config, tasks


def cmd_plan(args: argparse.Namespace) -> int:
    _, tasks = _load(args)

    print("\ninput check:")
    problems = missing_inputs(tasks)
    if problems:
        for name, detail in problems[:12]:
            print(f"  BAD  {name}: {detail}")
        if len(problems) > 12:
            print(f"  ... and {len(problems) - 12} more")
    else:
        print("  all inputs present")

    unreachable = unreachable_inputs(tasks)
    for name, path in unreachable[:6]:
        print(f"  UNREACHABLE {path}")
        print(f"              not under {', '.join(SHARED_PREFIXES)}; workers "
              f"cannot see it (first seen on {name})")

    print("\nworker environment:")
    worker_env = _worker_env(args)
    print(worker_env.describe())
    env_problems = worker_env.preflight()
    for problem in env_problems:
        print(f"  BLOCKER {problem}")

    if problems or env_problems or unreachable:
        print("\nnot ready to run.")
        return 1
    print("\nready to run.")
    return 0


def cmd_sync(args: argparse.Namespace) -> int:
    """Push the local cosmos_ray package to the shared checkout.

    The cosmos child process imports cosmos_ray from --cosmos-src on shared
    storage, not from the driver, so local edits are invisible to a run until
    they are pushed. Everything else the child needs comes from its venv.
    """
    import shutil
    import subprocess

    source = REPO_ROOT / "cosmos_ray"
    target = Path(args.cosmos_src) / "cosmos_ray"
    print(f"{source}  ->  {target}")

    target.parent.mkdir(parents=True, exist_ok=True)
    if shutil.which("rsync"):
        result = subprocess.run(
            ["rsync", "-a", "--delete", "--exclude=__pycache__", f"{source}/", f"{target}/"],
        )
        if result.returncode != 0:
            print("rsync failed", file=sys.stderr)
            return 1
    else:
        shutil.rmtree(target, ignore_errors=True)
        shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__"))

    print(f"synced {len(list(target.glob('*.py')))} modules")
    return 0


def _connect():
    import ray

    from .pool import NAMESPACE

    if not ray.is_initialized():
        ray.init(address="auto", namespace=NAMESPACE)


def cmd_warm(args: argparse.Namespace) -> int:
    """Report which warm actors exist. They are holding GPUs."""
    from .pool import list_pool

    _connect()
    names = list_pool()
    if not names:
        print("no warm actors")
        return 0
    print(f"{len(names)} warm actor(s), each holding a GPU:")
    for name in names:
        print(f"  {name}")
    print("\nrelease with: python -m cosmos_ray cool")
    return 0


def cmd_cool(args: argparse.Namespace) -> int:
    """Kill warm actors so their GPUs are available again."""
    from .pool import cool as cool_pool
    from .pool import list_pool

    _connect()
    names = list_pool()
    if not names:
        print("no warm actors to release")
        return 0
    killed = cool_pool(names)
    for name in killed:
        print(f"  released {name}")
    print(f"{len(killed)} actor(s) released")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    config, tasks = _load(args)

    problems = missing_inputs(tasks)
    if problems and not args.skip_input_check:
        print("\nrefusing to run; bad inputs:")
        for name, detail in problems[:12]:
            print(f"  {name}: {detail}")
        print("\n(--skip-input-check overrides)")
        return 1

    unreachable = unreachable_inputs(tasks)
    if unreachable and not args.skip_input_check:
        print("\nrefusing to run; inputs the workers cannot read:")
        for name, path in unreachable[:6]:
            print(f"  {path}")
        print(f"\nWorkers only see {', '.join(SHARED_PREFIXES)}. Copy the inputs "
              f"there and point the experiment at the copy.")
        return 1

    worker_env = _worker_env(args)
    env_problems = worker_env.preflight()
    if env_problems:
        print("\nrefusing to run; worker environment not ready:")
        for problem in env_problems:
            print(f"  {problem}")
        return 1

    # Push local cosmos_ray before running. The child imports from shared
    # storage, so without this step the workers may execute stale code.
    if not args.no_sync:
        cmd_sync(args)

    import tempfile

    import ray

    from .runner import run_actor_pool, run_ray_data, summarise_results, write_manifest

    # Code shipping and working_dir are job-level concerns; the actors inherit
    # them and add only py_executable + env_vars on top.
    with tempfile.TemporaryDirectory(prefix="cosmos-ray-job-") as empty:
        from .pool import NAMESPACE
        ray.init(address="auto", namespace=NAMESPACE,
                 runtime_env=worker_env.job_runtime_env(empty))
        return _execute(args, tasks, worker_env, run_actor_pool, run_ray_data,
                        summarise_results, write_manifest)


def _execute(args, tasks, worker_env, run_actor_pool, run_ray_data,
             summarise_results, write_manifest) -> int:

    guardrails = not args.disable_guardrails
    print(f"\nguardrails: {'ENABLED' if guardrails else 'disabled'}")
    if guardrails:
        print(
            "  note: a guardrail rejection yields no video. It is reported as\n"
            "  status=guardrail_blocked rather than passing silently."
        )

    started = time.time()
    common = dict(
        disable_guardrails=not guardrails,
        compile_tokenizer=args.compile_tokenizer,
        num_cpus=args.num_cpus,
        fingerprint=args.fingerprint,
    )
    if args.engine == "actor-pool":
        common["persist"] = args.persist
    if args.engine == "ray-data":
        rows = run_ray_data(tasks, worker_env, concurrency=args.concurrency, **common)
    else:
        rows = run_actor_pool(tasks, worker_env, num_actors=args.concurrency, **common)

    print(summarise_results(rows))
    print(f"wall clock: {time.time() - started:.0f}s")

    # The run root, not tasks[0].output_dir. Under the by_tag layout that is a
    # per-task subdirectory.
    run_root = Path(args.run_root)
    manifest = write_manifest(rows, run_root / "manifest.jsonl")
    index = _write_index(rows, run_root, args.experiment)
    print(f"manifest: {manifest}")
    print(f"index:    {index}")
    print(f"\nbring them into the workspace with:\n"
          f"    python -m cosmos_ray pull {args.experiment}")

    return 0 if all(row.get("status") == "ok" for row in rows) else 2


def _write_index(rows: list[dict], run_root: Path, experiment: str) -> Path:
    """A browsable summary next to the videos, so the folder explains itself."""
    lines = [f"# {Path(experiment).stem}", ""]
    ok = [r for r in rows if r.get("status") == "ok"]
    lines.append(f"{len(ok)}/{len(rows)} produced video.")
    lines.append("")
    lines.append("| status | task | tags | seconds | file |")
    lines.append("|---|---|---|---|---|")
    for row in rows:
        path = row.get("output_path") or ""
        rel = str(Path(path).relative_to(run_root)) if path and str(path).startswith(str(run_root)) else path
        tags = " ".join(f"{k}={v}" for k, v in (row.get("tags") or {}).items())
        link = f"[{Path(rel).name}]({rel})" if rel else ""
        lines.append(
            f"| {row.get('status')} | {row.get('name')} | {tags} | {row.get('seconds')} | {link} |"
        )
    failures = [r for r in rows if r.get("status") != "ok"]
    if failures:
        lines += ["", "## Not produced", ""]
        for row in failures:
            lines.append(f"- **{row.get('name')}**. {row.get('error', '')[:300]}")
    path = run_root / "index.md"
    path.write_text("\n".join(lines) + "\n")
    return path


def cmd_pull(args: argparse.Namespace) -> int:
    """Copy a run's outputs from shared storage into the workspace.

    Ray workers cannot see /home/ray/default. It is the head node's local
    disk. So generated videos live on /mnt/user_storage. This replaces the
    manual archive-transfer workflow. The destination is under the
    repo's /outputs/, which .gitignore already excludes.
    """
    import shutil

    config = load_experiment(args.experiment)
    run_root = Path(config["output_dir"])
    dest = Path(args.dest) / Path(args.experiment).stem

    if not run_root.exists():
        print(f"nothing at {run_root}; has this experiment been run?", file=sys.stderr)
        return 1

    wanted = None if args.all else {".mp4", ".jpg", ".png", ".txt", ".md", ".jsonl"}
    copied = 0
    for source in sorted(run_root.rglob("*")):
        if source.is_dir() or (wanted is not None and source.suffix not in wanted):
            continue
        target = dest / source.relative_to(run_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied += 1

    print(f"{run_root}  ->  {dest}")
    print(f"copied {copied} file(s)")
    videos = sorted(dest.rglob("*.mp4"))
    for video in videos:
        print(f"  {video.relative_to(dest)}  ({video.stat().st_size / 1e6:.1f} MB)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cosmos_ray", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan", help="expand and validate an experiment; no cluster needed")
    _add_common(plan)
    plan.set_defaults(func=cmd_plan)

    sync = sub.add_parser(
        "sync", help="push local cosmos_ray to the shared checkout the child imports from"
    )
    sync.add_argument("--cosmos-src", default=DEFAULT_COSMOS_SRC)
    sync.set_defaults(func=cmd_sync)

    pull = sub.add_parser("pull", help="copy a run's outputs into the workspace for viewing")
    pull.add_argument("experiment", help="path to the experiment .yaml/.json that was run")
    pull.add_argument(
        "--dest",
        default=str(REPO_ROOT / "outputs"),
        help="workspace directory to copy into (gitignored)",
    )
    pull.add_argument("--all", action="store_true", help="include configs and logs, not just media")
    pull.set_defaults(func=cmd_pull)

    cool = sub.add_parser("cool", help="release warm actors and free their GPUs")
    cool.set_defaults(func=cmd_cool)

    warm = sub.add_parser("warm", help="list warm actors currently holding GPUs")
    warm.set_defaults(func=cmd_warm)

    run = sub.add_parser("run", help="execute an experiment on the cluster")
    _add_common(run)
    run.add_argument("--engine", choices=("ray-data", "actor-pool"), default="ray-data")
    run.add_argument("-n", "--concurrency", type=int, default=4, help="actors (i.e. GPUs) to use")
    run.add_argument("--num-cpus", type=int, default=8, help="CPUs reserved per actor")
    run.add_argument(
        "--disable-guardrails",
        action="store_true",
        help="disable upstream text/video guardrails for controlled research "
             "reproduction; guardrails are enabled by default",
    )
    run.add_argument("--compile-tokenizer", choices=("none", "moderate", "aggressive"), default="none")
    run.add_argument("--skip-input-check", action="store_true")
    run.add_argument(
        "--fingerprint",
        action="store_true",
        help="record a numeric summary of each output (sha256 + per-frame mean "
             "luma) in the manifest, for variance and luma-delta analysis",
    )
    run.add_argument(
        "--persist",
        action="store_true",
        help="leave actors alive after the run so the next one skips the model "
             "load. They hold GPUs until `cosmos_ray cool`. actor-pool engine only",
    )
    run.add_argument(
        "--no-sync",
        action="store_true",
        help="skip the automatic push of cosmos_ray to the shared checkout",
    )
    run.set_defaults(func=cmd_run)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except SpecError as exc:
        print(f"\nexperiment error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
