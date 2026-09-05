"""Driver-safe data model for Cosmos Transfer inference jobs.

Nothing in this module imports cosmos_transfer2, torch, or ray. That is
deliberate: the driver runs on the head node (python 3.12, no cosmos install)
and must be able to build, validate and shard a several-thousand-task sweep
without the model environment existing anywhere near it.

The worker side (engine.py) converts these into real
``cosmos_transfer2.config.InferenceArguments`` objects.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterator

# Order matters: cosmos_transfer2.config.CONTROL_KEYS uses this exact order to
# build the comma-separated control_weight string handed to the pipeline.
CONTROL_KEYS: tuple[str, ...] = ("edge", "vis", "depth", "seg")

THRESHOLDS: tuple[str, ...] = ("very_low", "low", "medium", "high", "very_high")


class SpecError(ValueError):
    """Raised for a malformed task or sweep. Always names the offending task."""


@dataclass(frozen=True)
class ModelSpec:
    """Which checkpoint an actor will load.

    An actor is *pinned* to one of these for its whole life: Control2WorldInference
    resolves its checkpoint list from (variant, distilled) at construction time,
    so tasks must be grouped by model before any actor is started.
    """

    variant: str = "edge"
    distilled: bool = True

    def __post_init__(self) -> None:
        if self.variant not in CONTROL_KEYS:
            raise SpecError(
                f"model variant {self.variant!r} is not one of {CONTROL_KEYS}. "
                "Multiview/robot variants are not handled by this pipeline."
            )

    @property
    def name(self) -> str:
        """The string cosmos expects for SetupArguments.model, e.g. 'edge/distilled'."""
        return f"{self.variant}/distilled" if self.distilled else self.variant

    @property
    def needs_experimental_checkpoints(self) -> bool:
        """Distilled checkpoints are only registered when COSMOS_EXPERIMENTAL_CHECKPOINTS is set."""
        return self.distilled


@dataclass
class ControlSpec:
    """One control modality applied to a task."""

    kind: str
    weight: float = 1.0
    control_path: str | None = None
    mask_path: str | None = None
    mask_prompt: str | None = None
    # edge only
    preset_edge_threshold: str | None = None
    # vis only
    preset_blur_strength: str | None = None
    # seg only
    control_prompt: str | None = None

    def __post_init__(self) -> None:
        if self.kind not in CONTROL_KEYS:
            raise SpecError(f"control kind {self.kind!r} is not one of {CONTROL_KEYS}")
        if not 0.0 <= self.weight <= 1.0:
            raise SpecError(f"control weight {self.weight} for {self.kind!r} is outside [0.0, 1.0]")
        for name, value in (
            ("preset_edge_threshold", self.preset_edge_threshold),
            ("preset_blur_strength", self.preset_blur_strength),
        ):
            if value is not None and value not in THRESHOLDS:
                raise SpecError(f"{name}={value!r} is not one of {THRESHOLDS}")
        if self.mask_path and self.mask_prompt:
            raise SpecError(f"control {self.kind!r}: give only one of mask_path or mask_prompt")

    def to_cosmos_kwargs(self) -> dict[str, Any]:
        """kwargs for EdgeConfig / BlurConfig / DepthConfig / SegConfig."""
        out: dict[str, Any] = {"control_weight": self.weight}
        if self.control_path:
            out["control_path"] = self.control_path
        if self.mask_path:
            out["mask_path"] = self.mask_path
        if self.mask_prompt:
            out["mask_prompt"] = self.mask_prompt
        if self.kind == "edge" and self.preset_edge_threshold:
            out["preset_edge_threshold"] = self.preset_edge_threshold
        if self.kind == "vis" and self.preset_blur_strength:
            out["preset_blur_strength"] = self.preset_blur_strength
        if self.kind == "seg" and self.control_prompt:
            out["control_prompt"] = self.control_prompt
        return out


@dataclass
class TransferTask:
    """One video generation. The unit of work that flows through Ray."""

    name: str
    video_path: str
    prompt: str
    output_dir: str
    controls: list[ControlSpec] = field(default_factory=list)
    model: ModelSpec = field(default_factory=ModelSpec)

    # Sampling
    seed: int = 2025
    guidance: int = 3
    num_steps: int | None = None
    resolution: str = "720"
    max_frames: int | None = None
    num_video_frames_per_chunk: int = 93
    num_conditional_frames: int = 1
    sigma_max: str | None = None
    negative_prompt: str | None = None

    # Style reference
    image_context_path: str | None = None
    context_frame_index: int | None = None

    # Output composition
    show_control_condition: bool = False
    show_input: bool = False
    keep_input_resolution: bool = True

    # Free-form provenance, carried into the manifest. Sweeps use it to record
    # which axis values produced this task (e.g. {"weather": "rainy"}).
    tags: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.controls:
            raise SpecError(
                f"task {self.name!r} has no controls; cosmos requires at least one "
                f"of {CONTROL_KEYS}"
            )
        kinds = [c.kind for c in self.controls]
        if len(set(kinds)) != len(kinds):
            raise SpecError(f"task {self.name!r} repeats a control kind: {kinds}")
        if "vis" in kinds and self.image_context_path:
            raise SpecError(
                f"task {self.name!r}: vis control and image_context_path both transfer "
                "style and conflict; use one"
            )
        if not 0 <= self.guidance <= 7:
            raise SpecError(f"task {self.name!r}: guidance {self.guidance} is outside [0, 7]")

    @property
    def hint_keys(self) -> list[str]:
        """Control kinds in the canonical order cosmos expects."""
        kinds = {c.kind for c in self.controls}
        return [k for k in CONTROL_KEYS if k in kinds]

    @property
    def route_key(self) -> str:
        """Tasks sharing a route_key can share an actor; others cannot.

        Encodes both the checkpoint identity and the hint-key set, because
        Control2WorldInference switches to the multicontrol checkpoint whenever
        more than one hint key is present in the batch.
        """
        return f"{self.model.name}|{'+'.join(self.hint_keys)}"

    def to_inference_kwargs(self) -> dict[str, Any]:
        """kwargs for cosmos_transfer2.config.InferenceArguments.

        Every path is passed through as given; the caller is responsible for
        them being absolute. We never rely on InferenceArguments.from_files,
        which resolves relative paths by chdir-ing the whole process.
        """
        kwargs: dict[str, Any] = {
            "name": self.name,
            "video_path": self.video_path,
            "prompt": self.prompt,
            "seed": self.seed,
            "guidance": self.guidance,
            "resolution": self.resolution,
            "num_video_frames_per_chunk": self.num_video_frames_per_chunk,
            "num_conditional_frames": self.num_conditional_frames,
            "show_control_condition": self.show_control_condition,
            "show_input": self.show_input,
            "keep_input_resolution": self.keep_input_resolution,
        }
        if self.num_steps is not None:
            kwargs["num_steps"] = self.num_steps
        if self.max_frames is not None:
            kwargs["max_frames"] = self.max_frames
        if self.sigma_max is not None:
            kwargs["sigma_max"] = self.sigma_max
        if self.negative_prompt is not None:
            kwargs["negative_prompt"] = self.negative_prompt
        if self.image_context_path is not None:
            kwargs["image_context_path"] = self.image_context_path
        if self.context_frame_index is not None:
            kwargs["context_frame_index"] = self.context_frame_index
        for control in self.controls:
            kwargs[control.kind] = control.to_cosmos_kwargs()
        return kwargs

    # serialisation
    # Tasks cross a process boundary as a single JSON string column. Encoding
    # the whole task rather than spreading it over typed columns keeps Arrow
    # out of the business of inferring a schema for nested control structs.

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True)

    @classmethod
    def from_json(cls, blob: str) -> TransferTask:
        return cls.from_dict(json.loads(blob))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TransferTask:
        data = dict(data)
        data["controls"] = [ControlSpec(**c) for c in data.get("controls", [])]
        if "model" in data and isinstance(data["model"], dict):
            data["model"] = ModelSpec(**data["model"])
        return cls(**data)


def check_unique_names(tasks: list[TransferTask]) -> None:
    """Cosmos writes every artifact as ``output_dir / name``; collisions overwrite.

    from_files enforces this upstream by calling sys.exit(1), which would kill an
    actor. We enforce it on the driver, before anything is scheduled.
    """
    seen: dict[str, str] = {}
    for task in tasks:
        key = f"{task.output_dir}/{task.name}"
        if key in seen:
            raise SpecError(
                f"two tasks would both write {key!r}. Names must be unique within "
                f"an output directory. Conflicting tags: {seen[key]} vs {task.tags}"
            )
        seen[key] = str(task.tags)


def missing_inputs(tasks: list[TransferTask]) -> list[tuple[str, str]]:
    """Return (task name, path) for every input file that is absent or an LFS stub.

    Unfetched git-lfs pointers are ~130-byte text files. Feeding one to the
    pipeline fails deep inside a video decoder, so we catch it on the driver.
    """
    problems: list[tuple[str, str]] = []
    for task in tasks:
        candidates = [task.video_path, task.image_context_path]
        candidates += [c.control_path for c in task.controls]
        candidates += [c.mask_path for c in task.controls]
        for raw in candidates:
            if not raw:
                continue
            path = Path(raw)
            if not path.exists():
                problems.append((task.name, f"{raw} (missing)"))
            elif _is_lfs_pointer(path):
                problems.append((task.name, f"{raw} (unfetched git-lfs pointer)"))
    return problems


# Filesystems that every node can see. Anything else is the driver's private
# view: /home/ray/default is the head node's local disk, so a path under it
# validates fine here and then fails inside the actor with "Path does not point
# to a file", which reads like a missing file rather than a mount problem.
SHARED_PREFIXES = ("/mnt/cluster_storage", "/mnt/shared_storage", "/mnt/user_storage")


def unreachable_inputs(tasks: list[TransferTask]) -> list[tuple[str, str]]:
    """Return (task name, path) for inputs the workers will not be able to read.

    Checked separately from missing_inputs because the failure is the opposite
    shape: the file is definitely there, just not where the work happens.
    """
    problems: list[tuple[str, str]] = []
    seen: set[str] = set()
    for task in tasks:
        candidates = [task.video_path, task.image_context_path]
        candidates += [c.control_path for c in task.controls]
        candidates += [c.mask_path for c in task.controls]
        for raw in candidates:
            if not raw or raw in seen:
                continue
            if not str(raw).startswith(SHARED_PREFIXES):
                seen.add(raw)
                problems.append((task.name, str(raw)))
    return problems


def _is_lfs_pointer(path: Path) -> bool:
    try:
        if path.stat().st_size > 200:
            return False
        with open(path, "rb") as handle:
            return handle.read(40).startswith(b"version https://git-lfs")
    except OSError:
        return False


def group_by_route(tasks: list[TransferTask]) -> dict[str, list[TransferTask]]:
    """Partition tasks into groups that can each be served by one actor pool."""
    groups: dict[str, list[TransferTask]] = {}
    for task in tasks:
        groups.setdefault(task.route_key, []).append(task)
    return groups


def iter_route(tasks: list[TransferTask]) -> Iterator[tuple[str, ModelSpec, list[str], list[TransferTask]]]:
    """Yield (route_key, model, hint_keys, tasks) for each actor pool to create."""
    for route_key, group in group_by_route(tasks).items():
        yield route_key, group[0].model, group[0].hint_keys, group
