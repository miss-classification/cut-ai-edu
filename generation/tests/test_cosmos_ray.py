"""Driver-side tests for the cosmos_ray package.

These cover only the parts that must work without cosmos, torch, ray or a GPU,
which is deliberate: that is the layer where a sweep of 200 tasks is defined,
and a mistake there is the expensive kind.

Runnable two ways, because the head node has no pytest:

    python tests/test_cosmos_ray.py          # standalone, no deps
    pytest tests/test_cosmos_ray.py          # inside the cosmos venv
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from cosmos_ray.spec import (  # noqa: E402
    ControlSpec,
    ModelSpec,
    SpecError,
    TransferTask,
    check_unique_names,
    group_by_route,
    missing_inputs,
)
from cosmos_ray.sweeps import expand  # noqa: E402


def _task(name: str = "t", **overrides) -> TransferTask:
    kwargs: dict = {
        "name": name,
        "video_path": "/tmp/in.mp4",
        "prompt": "a prompt",
        "output_dir": "/tmp/out",
        "controls": [ControlSpec(kind="edge", weight=0.8)],
    }
    kwargs.update(overrides)
    return TransferTask(**kwargs)


def _raises(exc_type, fn, *args, **kwargs) -> Exception:
    try:
        fn(*args, **kwargs)
    except exc_type as exc:
        return exc
    raise AssertionError(f"expected {exc_type.__name__}, nothing was raised")


#. Model / control validation ------------------------------------------


def test_model_name_matches_cosmos_format():
    assert ModelSpec(variant="edge", distilled=True).name == "edge/distilled"
    assert ModelSpec(variant="depth", distilled=False).name == "depth"


def test_unknown_model_variant_rejected():
    # Multiview and robot variants exist upstream but need a different pipeline.
    _raises(SpecError, ModelSpec, variant="auto/multiview")


def test_control_weight_bounds_enforced():
    _raises(SpecError, ControlSpec, kind="edge", weight=1.5)


def test_mask_path_and_prompt_are_exclusive():
    _raises(SpecError, ControlSpec, kind="edge", mask_path="/a.mp4", mask_prompt="car")


def test_task_requires_a_control():
    exc = _raises(SpecError, _task, controls=[])
    assert "at least one" in str(exc)


def test_vis_control_conflicts_with_image_context():
    _raises(
        SpecError,
        _task,
        controls=[ControlSpec(kind="vis")],
        image_context_path="/style.png",
    )


# routing


def test_hint_keys_use_canonical_order():
    # cosmos builds a comma-separated control_weight string in CONTROL_KEYS
    # order, so hint_keys must not follow the order the user wrote them in.
    task = _task(controls=[ControlSpec(kind="seg"), ControlSpec(kind="edge")])
    assert task.hint_keys == ["edge", "seg"]


def test_route_key_separates_models_and_hint_sets():
    edge = _task("a")
    depth = _task("b", model=ModelSpec(variant="depth"), controls=[ControlSpec(kind="depth")])
    multi = _task("c", controls=[ControlSpec(kind="edge"), ControlSpec(kind="depth")])
    groups = group_by_route([edge, depth, multi])
    assert len(groups) == 3, "each needs its own actor pool"


def test_same_route_tasks_share_a_pool():
    groups = group_by_route([_task("a"), _task("b")])
    assert len(groups) == 1 and len(next(iter(groups.values()))) == 2


# name collisions


def test_duplicate_output_names_rejected():
    # Cosmos writes output_dir/name; a collision silently overwrites the earlier
    # video, so this must fail on the driver rather than at generation time.
    exc = _raises(SpecError, check_unique_names, [_task("same"), _task("same")])
    assert "unique" in str(exc)


def test_same_name_different_output_dir_is_fine():
    check_unique_names([_task("same"), _task("same", output_dir="/tmp/other")])


# inference kwargs


def test_controls_become_nested_kwargs():
    task = _task(controls=[ControlSpec(kind="edge", weight=0.5, preset_edge_threshold="high")])
    kwargs = task.to_inference_kwargs()
    assert kwargs["edge"] == {"control_weight": 0.5, "preset_edge_threshold": "high"}


def test_unset_optionals_are_omitted_not_none():
    # InferenceArguments has its own defaults; passing None would override them.
    kwargs = _task().to_inference_kwargs()
    for key in ("num_steps", "max_frames", "sigma_max", "image_context_path"):
        assert key not in kwargs, f"{key} should be omitted when unset"


def test_task_survives_a_json_round_trip():
    original = _task("rt", tags={"weather": "rain"}, num_steps=4)
    restored = TransferTask.from_json(original.to_json())
    assert restored.to_inference_kwargs() == original.to_inference_kwargs()
    assert restored.tags == {"weather": "rain"}
    assert restored.route_key == original.route_key


# sweep expansion


def test_cartesian_expansion_and_naming():
    tasks = expand(
        {
            "name": "sweep",
            "output_dir": "/tmp/out",
            "base": {"video_path": "/tmp/in.mp4", "prompt": "p", "controls": [{"kind": "edge"}]},
            "axes": {
                "weather": [{"tag": "rain", "prompt": "rainy"}, {"tag": "snow", "prompt": "snowy"}],
                "cw": [{"tag": "hi", "controls": [{"kind": "edge", "weight": 0.9}]}],
            },
        }
    )
    assert len(tasks) == 2
    assert {t.name for t in tasks} == {"sweep_rain_hi", "sweep_snow_hi"}
    assert tasks[0].tags == {"weather": "rain", "cw": "hi"}
    assert tasks[0].prompt == "rainy"
    assert tasks[0].controls[0].weight == 0.9


def test_typo_in_axis_field_is_rejected():
    # A silently ignored typo means N videos that all differ from the intent.
    exc = _raises(
        SpecError,
        expand,
        {
            "name": "s",
            "output_dir": "/tmp/out",
            "base": {"video_path": "/tmp/in.mp4", "prompt": "p", "controls": [{"kind": "edge"}]},
            "axes": {"a": [{"tag": "x", "guidence": 4}]},
        },
    )
    assert "guidence" in str(exc)


def test_experiment_without_output_dir_is_rejected():
    _raises(SpecError, expand, {"name": "s", "base": {}})


def test_model_string_shorthand():
    tasks = expand(
        {
            "name": "s",
            "output_dir": "/tmp/out",
            "model": "edge/distilled",
            "base": {"video_path": "/tmp/in.mp4", "prompt": "p", "controls": [{"kind": "edge"}]},
        }
    )
    assert tasks[0].model == ModelSpec(variant="edge", distilled=True)


# input preflight


def test_lfs_pointer_detected_as_bad_input(tmp_path: Path | None = None):
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        stub = Path(tmp) / "car.mp4"
        stub.write_text(
            "version https://git-lfs.github.com/spec/v1\n"
            "oid sha256:61a03443cd2dc535db7fa6dcec5044d0990c2c3a9f4dc0da5b736bdac44763ca\n"
            "size 3434042\n"
        )
        problems = missing_inputs([_task(video_path=str(stub))])
        assert len(problems) == 1 and "git-lfs" in problems[0][1]


def test_missing_input_detected():
    problems = missing_inputs([_task(video_path="/nonexistent/nope.mp4")])
    assert len(problems) == 1 and "missing" in problems[0][1]


def test_real_file_passes():
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as handle:
        handle.write(b"\x00" * 5000)
        name = handle.name
    assert missing_inputs([_task(video_path=name)]) == []


def main() -> int:
    tests = [(k, v) for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
        except Exception as exc:
            failed += 1
            print(f"FAIL {name}: {type(exc).__name__}: {exc}")
        else:
            print(f"ok   {name}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
