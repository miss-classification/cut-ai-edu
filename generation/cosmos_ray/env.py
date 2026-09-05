"""Where the cosmos venv lives and what environment it needs.

Both defaults point at shared storage, not node local disk, so a node the
autoscaler adds later can start work immediately:

    VENV_ROOT   /mnt/cluster_storage/cosmos-venvs/<tag>   built by bootstrap.py
    HF_HOME     /mnt/cluster_storage/hf                   checkpoint cache

The original scripts used /mnt/local_storage for both, which is ephemeral, so
every new node rebuilt the venv and redownloaded the checkpoint first.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_VENV_ROOT = "/mnt/cluster_storage/cosmos-venvs"
# Python 3.13, deliberately NOT the cluster's 3.12: cosmos runs in a child
# process, and natten has no cp312 wheel for cu130_torch29.
DEFAULT_VENV_TAG = "cu130-py313"
DEFAULT_HF_HOME = "/mnt/cluster_storage/hf"
# Canonical repo checkout on shared storage. The child process imports
# cosmos_ray from here (cosmos itself comes from its venv), so it must be
# readable from every node. bootstrap.py keeps it in sync.
DEFAULT_COSMOS_SRC = "/mnt/cluster_storage/cosmos-src/cosmos-transfer2.5"
DEFAULT_SCRATCH_ROOT = "/mnt/local_storage/cosmos-scratch"

# Excluded from the working_dir upload. The repo carries multi-hundred-MB
# archives and checkpoints that must never ride along on every job submission.
WORKING_DIR_EXCLUDES = [
    ".git",
    ".venv",
    "**/.venv",
    "outputs",
    "pulled_outputs",
    "assets/tests",
    "*.tgz",
    "*.tar.gz",
    "*.zip",
    "*.mp4",
    "*.mov",
    "uv.lock",
    "ATTRIBUTIONS.md",
]


@dataclass
class WorkerEnv:
    """Everything needed to start a cosmos-capable Ray worker."""

    venv_root: str = DEFAULT_VENV_ROOT
    venv_tag: str = DEFAULT_VENV_TAG
    # Explicit override, e.g. a venv that already exists on the worker's local
    # disk. Wins over venv_root/venv_tag when set.
    venv_path_override: str | None = None
    hf_home: str = DEFAULT_HF_HOME
    cosmos_src: str = DEFAULT_COSMOS_SRC
    scratch_root: str = DEFAULT_SCRATCH_ROOT
    # The cosmos_ray package directory. Shipped via py_modules rather than
    # working_dir: we need our own code on the worker, but cosmos itself should
    # come from the venv's proven install rather than from a source tree upload
    # that would shadow it.
    py_modules: list[str] = field(default_factory=list)
    hf_token: str | None = None

    # Distilled checkpoints are gated behind this flag, and it is read at import
    # time by cosmos_transfer2._src.imaginaire.flags. So it has to be in the
    # process environment before cosmos is imported, which is exactly what
    # runtime_env env_vars gives us and what a post-import os.environ set would
    # not.
    experimental_checkpoints: bool = True

    # Transformer-Engine attention backend. The working experiment runs left
    # these unset; the smoke script forced the unfused path. Off by default so
    # we reproduce what worked, available when a node needs it.
    force_unfused_attention: bool = False

    extra_env: dict[str, str] = field(default_factory=dict)

    @property
    def venv_path(self) -> Path:
        if self.venv_path_override:
            return Path(self.venv_path_override)
        return Path(self.venv_root) / self.venv_tag

    @property
    def venv_is_on_shared_storage(self) -> bool:
        """Whether the driver can meaningfully check that the venv exists.

        A venv on a worker's local disk is invisible from the head node, so a
        driver-side existence check would be a false negative. It is also
        ephemeral: it disappears when that node is replaced.
        """
        shared = ("/mnt/cluster_storage", "/mnt/shared_storage", "/mnt/user_storage")
        return str(self.venv_path).startswith(shared)

    @property
    def child_python(self) -> str:
        """Interpreter for the cosmos child process.

        Not used as Ray's py_executable: Ray demands the worker's python minor
        version match the cluster's (3.12), while cosmos needs 3.10 or 3.13
        (natten ships cp310 wheels only for cu130_torch29). No version satisfies
        both, so cosmos runs in a child process instead of in the actor.
        """
        return str(self.venv_path / "bin" / "python")

    # Retained under the old name for callers that still ask for it.
    py_executable = child_python

    def resolve_hf_token(self) -> str | None:
        """Read the HF token the same way the original scripts did."""
        if self.hf_token:
            return self.hf_token
        for key in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN"):
            if os.environ.get(key):
                return os.environ[key]
        token_file = Path("~/.cache/huggingface/token").expanduser()
        if token_file.exists():
            return token_file.read_text().strip()
        return None

    def env_vars(self) -> dict[str, str]:
        env: dict[str, str] = {
            "HF_HOME": self.hf_home,
            "TOKENIZERS_PARALLELISM": "false",
        }
        token = self.resolve_hf_token()
        if token:
            env["HF_TOKEN"] = token
            env["HUGGING_FACE_HUB_TOKEN"] = token
        if self.experimental_checkpoints:
            env["COSMOS_EXPERIMENTAL_CHECKPOINTS"] = "1"
        if self.force_unfused_attention:
            env["NVTE_FUSED_ATTN"] = "0"
            env["NVTE_FLASH_ATTN"] = "0"
            env["NVTE_UNFUSED_ATTN"] = "1"
        env.update(self.extra_env)
        return env

    def runtime_env(self) -> dict:
        """Per-actor runtime_env, for @ray.remote / ray_remote_args.

        Only env_vars. The actor runs on the cluster's own python. Cosmos
        lives in the child process. And a local directory in py_modules is
        rejected at this level anyway, so code shipping happens in
        job_runtime_env() and is inherited by every actor.
        """
        return {"env_vars": self.env_vars()}

    def job_runtime_env(self, empty_dir: str) -> dict:
        """Job-level runtime_env, for ray.init.

        working_dir is pinned to an empty directory on purpose: left implicit,
        Ray and Anyscale's wrapper snapshot the current working directory, which
        for this repo means uploading a few hundred MB of assets/tests.
        """
        runtime: dict = {"working_dir": empty_dir}
        if self.py_modules:
            runtime["py_modules"] = list(self.py_modules)
        return runtime

    def describe(self) -> str:
        token = self.resolve_hf_token()
        location = "shared storage" if self.venv_is_on_shared_storage else "worker-local (ephemeral)"
        return "\n".join(
            [
                f"  cosmos py   {self.child_python}",
                f"              ({location}, runs as a child process)",
                f"  cosmos src  {self.cosmos_src}",
                f"  HF_HOME     {self.hf_home}",
                f"  scratch     {self.scratch_root}",
                f"  hf token    {'found' if token else 'NOT FOUND'}",
                f"  py_modules  {', '.join(self.py_modules) or '(none)'}",
            ]
        )

    def _check_venv_contents(self) -> list[str]:
        """A venv directory existing does not mean the venv works.

        `uv venv` creates bin/python before `uv sync` installs anything, so a
        build that fails partway leaves a skeleton that passes a naive
        existence check and then dies in the actor. Look for the packages that
        actually have to be there.
        """
        site_packages = sorted(self.venv_path.glob("lib/python*/site-packages"))
        if not site_packages:
            return [f"{self.venv_path} has no site-packages; the build did not complete"]
        def installed(name: str) -> bool:
            for sp in site_packages:
                # A plain package directory, or. For `uv sync`, which installs
                # the project editable. A dist-info with no directory beside it.
                if (sp / name).exists():
                    return True
                prefix = name.replace("_", "?").lower()
                if any(sp.glob(f"{prefix}-*.dist-info")) or any(sp.glob(f"{name}-*.dist-info")):
                    return True
            return False

        missing = [
            name for name in ("cosmos_transfer2", "torch", "ray") if not installed(name)
        ]
        if missing:
            return [
                f"{self.venv_path} is incomplete. Missing {', '.join(missing)}. "
                f"A partly-built venv looks valid but fails inside the actor. Rebuild:\n"
                f"    python -m cosmos_ray.bootstrap --python 3.13 "
                f"--venv-tag {self.venv_tag} --force"
            ]
        return []

    def child_kwargs(self) -> dict[str, Any]:
        """Constructor arguments the actor needs to spawn its cosmos child."""
        return {
            "child_python": self.child_python,
            "cosmos_src": self.cosmos_src,
            "child_env": self.env_vars(),
        }

    def preflight(self) -> list[str]:
        """Driver-side checks. Cheap, and each one maps to a real past failure."""
        problems: list[str] = []
        if self.venv_is_on_shared_storage:
            if not self.venv_path.exists():
                problems.append(
                    f"cosmos venv not found at {self.venv_path}. Build it once with:\n"
                    f"    python -m cosmos_ray.bootstrap --venv-tag {self.venv_tag}"
                )
            elif not Path(self.child_python).exists():
                problems.append(f"{self.venv_path} exists but has no bin/python")
            else:
                problems.extend(self._check_venv_contents())
        # A worker-local venv cannot be checked from here; the actor will fail
        # fast with an ImportError if it is absent on the node it lands on.
        if not Path(self.hf_home).parent.exists():
            problems.append(f"HF_HOME parent {Path(self.hf_home).parent} does not exist")
        if not self.resolve_hf_token():
            problems.append(
                "no Hugging Face token found (checked $HF_TOKEN, "
                "$HUGGING_FACE_HUB_TOKEN, ~/.cache/huggingface/token). "
                "Checkpoint download will fail."
            )
        return problems
