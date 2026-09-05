"""Score an existing run with the detector, in parallel.

    python -m cosmos_ray.score /mnt/user_storage/cosmos-runs/fog_noise_floor

Reads manifest.jsonl, runs the detector over every produced video, writes the
detections back into the manifest, and prints counts grouped by tag.

Separate from `run` on purpose. Detection is cheap and generation is not, so
rescoring a finished grid with a different detector or threshold should not
cost another 100 seconds per clip.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run_root", help="directory containing manifest.jsonl")
    parser.add_argument("--model", default="fasterrcnn_resnet50_fpn_v2")
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--frame-stride", type=int, default=5,
                        help="score every Nth frame; 1 scores all of them")
    parser.add_argument("-n", "--concurrency", type=int, default=4)
    parser.add_argument("--num-gpus", type=float, default=0.25,
                        help="GPU fraction per detector actor. A detector is small, "
                             "so several share a card")
    parser.add_argument("--axis", default=None, help="tag to group the summary by")
    args = parser.parse_args(argv)

    run_root = Path(args.run_root)
    manifest = run_root / "manifest.jsonl"
    if not manifest.exists():
        print(f"no manifest at {manifest}", file=sys.stderr)
        return 1

    rows = [json.loads(line) for line in manifest.read_text().splitlines() if line.strip()]
    todo = [r for r in rows if r.get("status") == "ok" and r.get("output_path")]
    if not todo:
        print("no produced videos to score", file=sys.stderr)
        return 1
    print(f"scoring {len(todo)} video(s) from {run_root}")

    import tempfile

    import ray

    from .detect import DetectorActor

    with tempfile.TemporaryDirectory(prefix="cosmos-score-") as empty:
        ray.init(address="auto", runtime_env={"working_dir": empty,
                                              "py_modules": [str(Path(__file__).resolve().parent)]})
        pool_size = min(args.concurrency, len(todo))
        remote = ray.remote(num_gpus=args.num_gpus, num_cpus=2)(DetectorActor)
        actors = [
            remote.remote(model_name=args.model, score_threshold=args.threshold,
                          frame_stride=args.frame_stride)
            for _ in range(pool_size)
        ]
        for info in ray.get([a.ready.remote() for a in actors]):
            print(f"  detector on {info['host']} device={info['device']}")

        pending: dict[Any, Any] = {}
        queue = list(todo)
        idle = list(actors)
        done_rows: list[dict] = []

        while queue or pending:
            while queue and idle:
                actor = idle.pop()
                row = queue.pop(0)
                pending[actor.score.remote(row["output_path"])] = (actor, row)
            if not pending:
                break
            ready, _ = ray.wait(list(pending), num_returns=1)
            for ref in ready:
                actor, row = pending.pop(ref)
                try:
                    row["detections"] = ray.get(ref)
                except Exception as exc:
                    row["detections"] = {"detector_ok": False,
                                         "detector_error": f"{type(exc).__name__}: {exc}"}
                else:
                    idle.append(actor)
                done_rows.append(row)
                detections = row["detections"]
                mark = "ok " if detections.get("detector_ok") else "ERR"
                counts = detections.get("counts", {})
                print(f"  [{len(done_rows)}/{len(todo)}] {mark} {row['name']}  "
                      f"{detections.get('detections_per_frame', '?')}/frame  "
                      f"{ {k: v for k, v in list(counts.items())[:4]} }", flush=True)

        for actor in actors:
            ray.kill(actor)

    by_name = {r["name"]: r for r in done_rows}
    merged = [by_name.get(r.get("name"), r) for r in rows]
    manifest.write_text("\n".join(json.dumps(r) for r in merged) + "\n")
    print(f"\nwrote detections into {manifest}")

    _summary(done_rows, args.axis)
    return 0


def _summary(rows: list[dict], axis: str | None) -> None:
    """Mean detections per frame, grouped by a tag. The degradation curve."""
    groups: dict[str, list[dict]] = {}
    for row in rows:
        key = (row.get("tags") or {}).get(axis, "all") if axis else "all"
        groups.setdefault(key, []).append(row)

    print(f"\n{'level':<16} {'n':>2} {'det/frame':>10} {'sd':>7}   per class mean count")
    print(f"{'-' * 16} {'-' * 2} {'-' * 10} {'-' * 7}   {'-' * 40}")
    for key in sorted(groups):
        group = [r for r in groups[key] if r.get("detections", {}).get("detector_ok")]
        if not group:
            continue
        per_frame = [r["detections"]["detections_per_frame"] for r in group]
        classes: dict[str, list[float]] = {}
        for row in group:
            for cls, value in row["detections"].get("counts", {}).items():
                classes.setdefault(cls, []).append(value)
        summary = ", ".join(
            f"{c}={statistics.fmean(v):.2f}" for c, v in sorted(classes.items())
        )
        sd = statistics.stdev(per_frame) if len(per_frame) > 1 else float("nan")
        print(f"{key:<16} {len(group):>2} {statistics.fmean(per_frame):>10.3f} "
              f"{sd:>7.3f}   {summary}")


if __name__ == "__main__":
    sys.exit(main())
