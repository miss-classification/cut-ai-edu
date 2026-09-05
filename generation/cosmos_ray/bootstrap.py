"""Build the cosmos venv once, on shared storage, for every node to use.

The original scripts rebuilt a venv inside every job, on node-local storage:

    rsync repo -> /mnt/local_storage; uv venv; uv sync --extra=cu130

That is several minutes per job, repeated per node, and thrown away when the
node scales down. Here it happens once into /mnt/cluster_storage, which every
node. Including ones the autoscaler adds tomorrow. Can see.

    python -m cosmos_ray.bootstrap                 # build if missing
    python -m cosmos_ray.bootstrap --force         # rebuild from scratch
    python -m cosmos_ray.bootstrap --check         # just report what is there

Run this once before the first job. It takes roughly ten minutes.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .env import DEFAULT_VENV_ROOT, DEFAULT_VENV_TAG, WORKING_DIR_EXCLUDES

BUILD_SCRIPT = r"""
set -euo pipefail

SRC="$(pwd)"
CANON="{canon}"
VENV="{venv}"
EXTRA="{extra}"

export PATH="$HOME/.local/bin:$PATH"
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

mkdir -p "$CANON"
rsync -a --delete \
  --exclude='.git' --exclude='.venv' --exclude='assets/tests' \
  --exclude='outputs' --exclude='pulled_outputs' \
  --exclude='*.zip' --exclude='*.tar.gz' --exclude='*.tgz' \
  "$SRC/" "$CANON/"

cd "$CANON"

if [ "{force}" = "1" ]; then
  rm -rf "$VENV"
fi

if [ ! -x "$VENV/bin/python" ]; then
  uv python install {python}
  uv venv --python {python} "$VENV"
  VIRTUAL_ENV="$VENV" uv sync --extra="$EXTRA" --python "$VENV/bin/python" --active --inexact
fi

# Ray, so the child process can be driven from a Ray actor.
VIRTUAL_ENV="$VENV" uv pip install --python "$VENV/bin/python" "ray=={ray_version}"

# Pin cuDNN. uv.lock leaves nvidia-cudnn-cu13 floating, and a fresh resolve
# picks up whatever is newest. Which produced libcudnn_cnn.so.9 and
# libcudnn_graph.so.9 from different releases and an undefined-symbol crash at
# model init. Commit cd4f084 pinned cuDNN 9.21 for a conv3d OOM fix; that is
# also the version in the venv known to generate correctly here.
if [ -n "{cudnn}" ]; then
  VIRTUAL_ENV="$VENV" uv pip install --python "$VENV/bin/python" \
    "nvidia-cudnn-cu13=={cudnn}"
fi

# Pin decord to the PyPI build. The cosmos dependency index serves
# decord==0.6.0+cu130.torch29, which links against libavformat.so.60 (ffmpeg 6).
# That library is not present here: only .so.58 in a conda env and .so.62
# bundled by opencv and av. The plain PyPI wheel loads and is what the venv
# known to generate correctly uses.
#
# --reinstall-package and an explicit PyPI index are both required. The index
# build is version 0.6.0+cu130.torch29, and a local version segment satisfies
# the specifier "decord==0.6.0", so a plain install reports "Checked 1 package"
# and changes nothing.
if [ -n "{decord}" ]; then
  VIRTUAL_ENV="$VENV" uv pip install --python "$VENV/bin/python" \
    --reinstall-package decord --index-url https://pypi.org/simple \
    "decord=={decord}"
fi

echo "===== verifying ====="
"$VENV/bin/python" --version
"$VENV/bin/python" -c "import torch; print('torch', torch.__version__, 'cuda', torch.cuda.is_available())"
"$VENV/bin/python" -c "import flash_attn; print('flash-attn ok')" || echo "WARNING: flash_attn import failed"
"$VENV/bin/python" -c "import cosmos_transfer2; print('cosmos_transfer2 ok')"
"$VENV/bin/python" -c "import ray; print('ray', ray.__version__)"
"$VENV/bin/python" -c "import importlib.metadata as m; print('cudnn', m.version('nvidia-cudnn-cu13'))"
# decord is used to read input video, so a broken one fails at generation time.
"$VENV/bin/python" -c "import decord; print('decord ok', decord.__version__)"
# Proves the cuDNN pair actually links, which an import of torch alone does not.
"$VENV/bin/python" -c "import torch; torch.backends.cudnn.is_available(); print('cudnn links ok')"
du -sh "$VENV"
"""


def _build_remotely(
    repo: Path, venv_root: str, venv_tag: str, extra: str, python: str,
    cudnn: str, decord: str, force: bool
) -> str:
    import ray

    venv = f"{venv_root}/{venv_tag}"
    canon = f"{venv_root}/../cosmos-src/cosmos-transfer2.5"
    script = BUILD_SCRIPT.format(
        canon=canon,
        venv=venv,
        extra=extra,
        python=python,
        ray_version=ray.__version__,
        cudnn=cudnn,
        decord=decord,
        force="1" if force else "0",
    )

    # working_dir is set at the job level (see main): Ray only uploads local
    # directories there, not in a task's runtime_env. The task inherits it, so
    # $(pwd) inside the build script is the uploaded repo.
    @ray.remote(num_gpus=1, num_cpus=8)
    def build() -> str:
        import subprocess

        process = subprocess.run(
            script, shell=True, text=True, capture_output=True, executable="/bin/bash"
        )
        output = process.stdout + process.stderr
        if process.returncode != 0:
            raise RuntimeError(f"venv build failed ({process.returncode}):\n{output[-6000:]}")
        return output

    return ray.get(build.remote(), timeout=5400)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parent.parent))
    parser.add_argument("--venv-root", default=DEFAULT_VENV_ROOT)
    parser.add_argument("--venv-tag", default=DEFAULT_VENV_TAG)
    parser.add_argument("--extra", default="cu130", help="uv extra: cu130 or cu128")
    parser.add_argument(
        "--python",
        default=f"{sys.version_info.major}.{sys.version_info.minor}",
        help="python for the venv. Use 3.13 (or 3.10), NOT the cluster's 3.12: "
             "natten has no cp312 wheel for cu130_torch29. cosmos runs in a "
             "child process, so it does not need to match the cluster. The "
             "default here only matches because bootstrap runs on the driver.",
    )
    parser.add_argument(
        "--cudnn",
        default="9.21.1.3",
        help="pin nvidia-cudnn-cu13. uv.lock leaves it floating and a fresh "
             "resolve picked 9.24.0.43, whose libcudnn_cnn/libcudnn_graph pair "
             "crashes with an undefined symbol at model init. Empty string to "
             "leave whatever uv resolves.",
    )
    parser.add_argument(
        "--decord",
        default="0.6.0",
        help="pin decord. The cosmos index build needs ffmpeg 6, which is not "
             "installed; the PyPI wheel works. Empty string to leave as resolved.",
    )
    parser.add_argument("--force", action="store_true", help="delete and rebuild the venv")
    parser.add_argument("--check", action="store_true", help="report state without building")
    args = parser.parse_args(argv)

    venv_path = Path(args.venv_root) / args.venv_tag
    print(f"venv target: {venv_path}")

    if args.check:
        if (venv_path / "bin" / "python").exists():
            print("  present")
            return 0
        print("  absent. Run without --check to build")
        return 1

    if (venv_path / "bin" / "python").exists() and not args.force:
        print("  already present; pass --force to rebuild")
        return 0

    import ray

    ray.init(
        address="auto",
        runtime_env={"working_dir": args.repo, "excludes": WORKING_DIR_EXCLUDES},
    )
    print(f"building on a GPU node with python {args.python} (about 10 minutes)...", flush=True)
    print(
        _build_remotely(
            Path(args.repo), args.venv_root, args.venv_tag, args.extra,
            args.python, args.cudnn, args.decord, args.force
        )
    )
    print(f"\ndone: {venv_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
