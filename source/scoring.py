#!/usr/bin/env python3
"""Rank the lesson candidates with a transparent weighted selector.

Authors: Alicia Chua, Pawarit Laosunthara, and Eric Tang, Anyscale.

The bundled values are fixed illustrative visual annotations. They
are teaching inputs, not ground truth, benchmark results, or safety metrics.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_DATA = Path(__file__).resolve().parents[1] / "data" / "rubric_scores.csv"


@dataclass(frozen=True)
class Candidate:
    name: str
    seed: int
    weather: float
    structure: float
    stability: float
    note: str


def load_candidates(path: Path) -> list[Candidate]:
    """Load the illustrative annotations from a CSV file."""
    with path.open(newline="", encoding="utf-8") as handle:
        rows = csv.DictReader(handle)
        required = {
            "candidate",
            "seed",
            "weather_fidelity",
            "structure_preservation",
            "temporal_stability",
            "annotation_note",
        }
        missing = required.difference(rows.fieldnames or [])
        if missing:
            names = ", ".join(sorted(missing))
            raise ValueError(f"CSV is missing columns: {names}")

        candidates = [
            Candidate(
                name=row["candidate"],
                seed=int(row["seed"]),
                weather=float(row["weather_fidelity"]),
                structure=float(row["structure_preservation"]),
                stability=float(row["temporal_stability"]),
                note=row["annotation_note"],
            )
            for row in rows
        ]

    if not candidates:
        raise ValueError("CSV contains no candidates")
    return candidates


def weighted_score(
    candidate: Candidate,
    weather_weight: float,
    structure_weight: float,
    stability_weight: float,
) -> float:
    """Return a normalized score on the original 0 to 100 scale."""
    weights = (weather_weight, structure_weight, stability_weight)
    if any(weight < 0 for weight in weights):
        raise ValueError("weights must be nonnegative")
    total = sum(weights)
    if total <= 0:
        raise ValueError("at least one weight must be positive")
    return (
        weather_weight * candidate.weather
        + structure_weight * candidate.structure
        + stability_weight * candidate.stability
    ) / total


def rank_candidates(
    candidates: Iterable[Candidate],
    weather_weight: float,
    structure_weight: float,
    stability_weight: float,
) -> list[tuple[Candidate, float]]:
    """Rank candidates from largest score to smallest score."""
    scored = [
        (
            candidate,
            weighted_score(
                candidate,
                weather_weight,
                structure_weight,
                stability_weight,
            ),
        )
        for candidate in candidates
    ]
    return sorted(scored, key=lambda item: (-item[1], item[0].name))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Explore Best-of-N selection with the lesson annotations."
    )
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--n", type=int, default=8, help="Use the first N candidates.")
    parser.add_argument("--weather", type=float, default=40.0)
    parser.add_argument("--structure", type=float, default=35.0)
    parser.add_argument("--stability", type=float, default=25.0)
    parser.add_argument(
        "--reject",
        action="append",
        default=[],
        metavar="TAKE",
        help="Apply a human-defined hard gate, for example --reject take07.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    candidates = load_candidates(args.data)
    if not 1 <= args.n <= len(candidates):
        raise SystemExit(f"--n must be between 1 and {len(candidates)}")

    rejected = {name.lower() for name in args.reject}
    pool = [candidate for candidate in candidates[: args.n] if candidate.name.lower() not in rejected]
    if not pool:
        raise SystemExit("No eligible candidate remains. Abstain or revise the pool.")

    ranking = rank_candidates(
        pool,
        weather_weight=args.weather,
        structure_weight=args.structure,
        stability_weight=args.stability,
    )

    print("Scores are fixed illustrative annotations, not ground truth.")
    print(
        f"N={args.n} weights: weather={args.weather:g}, "
        f"structure={args.structure:g}, stability={args.stability:g}"
    )
    if rejected:
        print("Hard-gated: " + ", ".join(sorted(rejected)))
    print()
    print(f"{'rank':>4}  {'candidate':<9}  {'score':>6}  {'seed':>6}  note")
    for rank, (candidate, score) in enumerate(ranking, start=1):
        print(
            f"{rank:>4}  {candidate.name:<9}  {score:>6.2f}  "
            f"{candidate.seed:>6}  {candidate.note}"
        )
    print()
    print(f"Selected: {ranking[0][0].name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
