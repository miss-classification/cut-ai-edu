"""Declarative experiments and cartesian sweep expansion.

Replaces separate experiment-specific launch scripts. An
experiment is data: a base task plus named axes. Expanding the axes gives the
task list. Everything happens on the driver, so a mistake in a 200-task sweep
surfaces in under a second instead of after a GPU has booted.

    base:  one TransferTask worth of defaults
    axes:  {axis_name: [variant, variant, ...]}

Each variant is a dict of overrides applied on top of the base, plus a ``tag``
used to build the task name and recorded in ``task.tags``. The task list is the
cartesian product of all axes.
"""

from __future__ import annotations

import itertools
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from .spec import ControlSpec, ModelSpec, SpecError, TransferTask, check_unique_names

# Fields a sweep axis is allowed to override. Anything else is a typo, and a
# silently-ignored typo in a sweep axis is expensive: it yields 200 videos
# that all differ from what was intended.
OVERRIDABLE = {
    "video_path",
    "prompt",
    "prompt_path",
    "controls",
    "seed",
    "guidance",
    "num_steps",
    "resolution",
    "max_frames",
    "num_video_frames_per_chunk",
    "num_conditional_frames",
    "sigma_max",
    "negative_prompt",
    "image_context_path",
    "context_frame_index",
    "show_control_condition",
    "show_input",
    "keep_input_resolution",
    "model",
}


def load_experiment(path: str | Path) -> dict[str, Any]:
    """Load a .yaml / .yml / .json experiment file."""
    path = Path(path)
    text = path.read_text()
    if path.suffix in (".yaml", ".yml"):
        try:
            import yaml
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise SpecError(
                "PyYAML is required to read .yaml experiments. Either `pip install pyyaml` "
                "on the driver or write the experiment as .json."
            ) from exc
        data = yaml.safe_load(text)
    elif path.suffix == ".json":
        data = json.loads(text)
    else:
        raise SpecError(f"unsupported experiment file type: {path.suffix}")
    if not isinstance(data, dict):
        raise SpecError(f"{path} must contain a mapping at the top level")
    data.setdefault("name", path.stem)
    data["_source"] = str(path)
    return data


def expand(config: dict[str, Any]) -> list[TransferTask]:
    """Expand an experiment config into concrete tasks."""
    experiment_name = config.get("name") or "experiment"
    base = dict(config.get("base") or {})
    axes: dict[str, list[dict[str, Any]]] = config.get("axes") or {}
    output_dir = config.get("output_dir")
    if not output_dir:
        raise SpecError(f"experiment {experiment_name!r} has no output_dir")

    default_model = _coerce_model(config.get("model") or base.pop("model", None))

    layout = config.get("layout", "by_tag")
    if layout not in ("by_tag", "flat"):
        raise SpecError(f"layout must be 'by_tag' or 'flat', got {layout!r}")

    for axis_name, variants in axes.items():
        if not isinstance(variants, list) or not variants:
            raise SpecError(f"axis {axis_name!r} must be a non-empty list")
        for variant in variants:
            unknown = set(variant) - OVERRIDABLE - {"tag"}
            if unknown:
                raise SpecError(
                    f"axis {axis_name!r} variant {variant.get('tag', '?')!r} sets unknown "
                    f"field(s) {sorted(unknown)}. Allowed: {sorted(OVERRIDABLE)}"
                )

    axis_names = list(axes)
    combos = list(itertools.product(*(axes[name] for name in axis_names))) or [()]

    tasks: list[TransferTask] = []
    for combo in combos:
        merged = dict(base)
        tags: dict[str, str] = {}
        for axis_name, variant in zip(axis_names, combo):
            variant = dict(variant)
            tag = variant.pop("tag", None)
            if tag is None:
                raise SpecError(f"every variant of axis {axis_name!r} needs a 'tag'")
            tags[axis_name] = str(tag)
            merged.update(variant)

        name_parts = [experiment_name] + [tags[a] for a in axis_names]
        merged["name"] = "_".join(str(p) for p in name_parts)
        merged["output_dir"] = _task_output_dir(output_dir, tags, axis_names, layout)
        merged["tags"] = tags
        merged.setdefault("model", default_model)
        tasks.append(_build_task(merged, experiment_name))

    check_unique_names(tasks)
    return tasks


def _task_output_dir(
    root: str, tags: dict[str, str], axis_names: list[str], layout: str
) -> str:
    """Where one task's artifacts land.

    Under 'by_tag' each task gets its own directory named by its axis values:

        runs/car_weather/rain/cw80/car_weather_rain_cw80.mp4
        runs/car_weather/rain/cw80/car_weather_rain_cw80_control_edge.mp4

    which keeps a 12-video sweep browsable instead of 48 files in one folder,
    and mirrors the results_<variant>/ convention already used under
    assets/tests/. With no axes there are no tags, so this is flat anyway.
    """
    if layout == "flat" or not tags:
        return str(root)
    parts = [str(tags[a]) for a in axis_names if a in tags]
    return str(Path(root).joinpath(*parts)) if parts else str(root)


def _build_task(data: dict[str, Any], experiment_name: str) -> TransferTask:
    data = dict(data)

    # prompt_path is resolved here, on the driver, so the worker never has to
    # reach for a file and the manifest records the literal prompt used.
    prompt_path = data.pop("prompt_path", None)
    if prompt_path and not data.get("prompt"):
        resolved = Path(prompt_path).expanduser()
        if not resolved.exists():
            raise SpecError(f"{experiment_name}: prompt_path {resolved} does not exist")
        data["prompt"] = resolved.read_text().strip()
    if not data.get("prompt"):
        raise SpecError(f"{experiment_name}: task {data.get('name')!r} has no prompt or prompt_path")

    data["controls"] = [_coerce_control(c) for c in data.get("controls") or []]
    data["model"] = _coerce_model(data.get("model"))

    for key in ("video_path", "image_context_path"):
        if data.get(key):
            data[key] = str(Path(data[key]).expanduser().resolve())

    try:
        return TransferTask(**data)
    except TypeError as exc:
        raise SpecError(f"{experiment_name}: bad task fields for {data.get('name')!r}: {exc}") from exc


def _coerce_control(raw: Any) -> ControlSpec:
    if isinstance(raw, ControlSpec):
        return raw
    if isinstance(raw, str):
        return ControlSpec(kind=raw)
    raw = dict(raw)
    for key in ("control_path", "mask_path"):
        if raw.get(key):
            raw[key] = str(Path(raw[key]).expanduser().resolve())
    return ControlSpec(**raw)


def _coerce_model(raw: Any) -> ModelSpec:
    if raw is None:
        return ModelSpec()
    if isinstance(raw, ModelSpec):
        return raw
    if isinstance(raw, str):
        # "edge/distilled" or "edge"
        variant, _, suffix = raw.partition("/")
        return ModelSpec(variant=variant, distilled=suffix == "distilled")
    return ModelSpec(**raw)


def summarise(tasks: list[TransferTask]) -> str:
    """A short human-readable plan, printed before anything is scheduled."""
    from .spec import group_by_route

    lines = [f"{len(tasks)} task(s):"]
    for route_key, group in group_by_route(tasks).items():
        lines.append(f"  [{route_key}]  {len(group)} task(s)")
        for task in group[:6]:
            tag_str = " ".join(f"{k}={v}" for k, v in task.tags.items())
            lines.append(f"      {task.name}  {tag_str}")
        if len(group) > 6:
            lines.append(f"      ... and {len(group) - 6} more")
    return "\n".join(lines)
