"""Luma delta and replicate variance over a finished run.

    python -m cosmos_ray.analyze /mnt/user_storage/cosmos-runs/fog_severity
    python -m cosmos_ray.analyze <run> --axis severity --baseline s0_clear --group weight

Answers one question: did the treatment actually change the image, by more than
generation noise?

Mean luma per clip comes from the manifest's ``per_frame_mean`` (recorded by
``run --fingerprint``), so this needs no video decoding and no GPU.

The honest part is the noise floor. A luma delta only means something relative
to how much two renders of the SAME condition differ, which requires replicate
seeds. Without them this reports the effect and says plainly that it cannot be
judged. Rather than printing a number that looks like a finding.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any


def load_rows(run_root: Path) -> list[dict[str, Any]]:
    manifest = run_root / "manifest.jsonl"
    if not manifest.exists():
        raise SystemExit(f"no manifest at {manifest}")
    rows = [json.loads(line) for line in manifest.read_text().splitlines() if line.strip()]
    usable = [r for r in rows if r.get("status") == "ok" and r.get("fingerprint")]
    if not usable:
        raise SystemExit(
            f"{manifest} has no fingerprinted successes. Re-run with --fingerprint."
        )
    return usable


def mean_luma(row: dict) -> float:
    return statistics.fmean(row["fingerprint"]["per_frame_mean"])


def contrast(row: dict) -> float | None:
    """Mean spatial standard deviation. Recorded from newer runs only."""
    return row["fingerprint"].get("contrast")


def analyse(rows, axis: str, baseline: str | None, group: str | None) -> int:
    groups: dict[str, list[dict]] = {}
    for row in rows:
        key = (row.get("tags") or {}).get(group, "") if group else ""
        groups.setdefault(key, []).append(row)

    for group_value, group_rows in sorted(groups.items()):
        header = f"{group}={group_value}" if group else "all"
        print(f"\n{'=' * 62}\n{header}\n{'=' * 62}")

        # Bucket by the treatment axis; multiple rows in a bucket are replicates.
        buckets: dict[str, list[float]] = {}
        for row in group_rows:
            level = (row.get("tags") or {}).get(axis)
            if level is None:
                continue
            buckets.setdefault(level, []).append(mean_luma(row))
        if not buckets:
            print(f"  no rows carry tag {axis!r}")
            continue

        levels = sorted(buckets)
        base = baseline if baseline in buckets else levels[0]
        base_luma = statistics.fmean(buckets[base])

        # Within condition spread. Standard deviation, not range: range grows
        # with n and would overstate the noise at small replicate counts.
        replicated = {k: v for k, v in buckets.items() if len(v) > 1}
        pooled_sd = None
        if replicated:
            variances = [statistics.variance(v) for v in replicated.values()]
            pooled_sd = (statistics.fmean(variances)) ** 0.5

        print(f"  baseline: {base}  (mean luma {base_luma:.3f})")
        print(f"\n  {'level':<14} {'n':>2} {'mean':>9} {'sd':>7} {'range':>7} "
              f"{'delta':>9} {'contrast':>8}")
        print(f"  {'-' * 14} {'-' * 2} {'-' * 9} {'-' * 7} {'-' * 7} {'-' * 9} {'-' * 8}")
        for level in levels:
            values = buckets[level]
            luma = statistics.fmean(values)
            sd = statistics.stdev(values) if len(values) > 1 else float("nan")
            spread = max(values) - min(values)
            con = [
                c for c in (
                    contrast(r) for r in group_rows
                    if (r.get("tags") or {}).get(axis) == level
                ) if c
            ]
            con_txt = f"{statistics.fmean(con):>8.2f}" if con else f"{'-':>8}"
            print(f"  {level:<14} {len(values):>2} {luma:>9.3f} {sd:>7.3f} "
                  f"{spread:>7.3f} {luma - base_luma:>+9.3f} {con_txt}")

        if pooled_sd is None:
            print(
                "\n  NO REPLICATES. Every condition has one seed, so none of these\n"
                "  deltas can be called a finding. Two seeds of one condition can\n"
                "  differ more than two adjacent conditions do. Add a seed axis."
            )
            return 0

        print(f"\n  pooled within condition sd: {pooled_sd:.3f} luma levels")
        print("  contrast is the instrument for fog, which brightens rather than darkens")
        print(f"\n  {'comparison':<26} {'effect':>9} {'effect/sd':>10} {'reading':>18}")
        print(f"  {'-' * 26} {'-' * 9} {'-' * 10} {'-' * 18}")
        for level in levels:
            if level == base or len(buckets[level]) < 2:
                continue
            effect = statistics.fmean(buckets[level]) - base_luma
            ratio = abs(effect) / pooled_sd if pooled_sd else float("inf")
            # Cohen's d of 0.8 is a conventional "large" effect; below about 1
            # sd, five replicates per arm cannot separate signal from noise.
            if ratio >= 2.0:
                reading = "clear"
            elif ratio >= 1.0:
                reading = "suggestive"
            else:
                reading = "indistinguishable"
            print(f"  {base} vs {level:<12} {effect:>+9.3f} {ratio:>10.2f} {reading:>18}")

        print(
            "\n  effect/sd below 1 means the treatment moves mean luma less than\n"
            "  reseeding does. That is a statement about this metric, not about\n"
            "  whether the videos differ: mean luma is a coarse whole frame\n"
            "  summary and can miss a change that is obvious to look at."
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run_root", help="directory containing manifest.jsonl")
    parser.add_argument("--axis", default="severity", help="tag treated as the treatment")
    parser.add_argument("--baseline", default=None, help="tag value used as the reference level")
    parser.add_argument("--group", default=None,
                        help="tag to report separately, e.g. weight")
    args = parser.parse_args(argv)

    rows = load_rows(Path(args.run_root))
    print(f"{len(rows)} fingerprinted clip(s) from {args.run_root}")
    return analyse(rows, args.axis, args.baseline, args.group)


if __name__ == "__main__":
    sys.exit(main())
