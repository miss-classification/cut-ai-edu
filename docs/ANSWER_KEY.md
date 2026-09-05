# Suggested Answer Key and Discussion Guide

**Authors:** Alicia Chua, Pawarit Laosunthara, and Eric Tang, Anyscale

This guide provides defensible answers, not a single ground truth ranking. The purpose is to evaluate reasoning about selection.

## Embedded lesson questions

### Question 1

**What changed across the eight fog takes?**

Correct answer: **The random seed.**

The source video, prompt, Cosmos Transfer 2.5 model, guidance, inference steps, edge-control weight, and frame count remain fixed. The seed changes the sampled noise and therefore the generated candidate.

### Question 2

**Why might a larger N fail to improve the final output?**

Correct answer: **The selector may rank candidates poorly.**

A second valid reason is that the generator may not produce a useful candidate even in a larger pool. Best-of-N needs both candidate coverage and reliable selection.

## Worksheet guidance

### Part 1

Accept any candidate choice supported by specific visual evidence. Strong answers distinguish fitness for purpose from visual appeal. Examples of useful observations include condition strength, lane continuity, vehicle shape, object persistence, localized artifacts, color shifts, or flicker.

### Part 2

Strong operational definitions might include:

- **Weather fidelity:** fog is visible across the scene at the requested moderate severity; nearby road markings remain visible; distant structures lose contrast.
- **Structure preservation:** lane topology, road boundaries, buildings, vehicles, pedestrians, and traffic cones remain recognizable and spatially consistent with the source.
- **Temporal stability:** important objects preserve identity and shape; the weather field changes smoothly; no abrupt flicker, teleportation, or camera discontinuity appears.

Acceptable hard gates include:

- a vehicle or pedestrian disappears or changes identity
- lane topology changes
- an object teleports or moves impossibly
- the camera pose jumps
- a large region flickers across frames
- the requested condition is absent

### Part 3

Using the lesson's default weights of 40 percent weather, 35 percent structure, and 25 percent stability, Take 04 is the example rubric's highest-ranked candidate.

The important reasoning is the sequence:

1. Apply hard gates.
2. Score eligible candidates.
3. Rank them.
4. Inspect the score margin.
5. Abstain if none is acceptable.

### Part 4

The winner may change when the mission changes. A structure-first profile tends to favor candidates such as Take 03 or Take 06. A weather-only profile favors Take 07 in the illustrative data, even though its localized plume resembles smoke. This is the intended proxy-failure demonstration.

### Part 5

Strong answers identify missing dimensions such as object detection consistency, lane-boundary accuracy, physical plausibility, collision relevance, visibility range, or uncertainty. They should not treat a VLM explanation as ground truth.

Appropriate automation candidates include edge similarity, depth consistency, object detection and tracking, optical-flow consistency, temporal flicker, and visibility or contrast changes. Humans are still needed to define acceptable behavior, calibrate thresholds, inspect ambiguous cases, and validate the full system.

The selector should abstain when all candidates fail a hard gate, when the top score is below an acceptance threshold, or when uncertainty and disagreement are too high.

## Transfer challenge rubric

| Category | 0 | 1 | 2 | 3 |
| --- | --- | --- | --- | --- |
| Mechanism | Cannot describe Best-of-N | Mentions multiple outputs | Separates generation and selection | Explains diversity, selection, and compute cost |
| Rubric design | No usable criteria | Criteria remain subjective | Criteria cite observable evidence | Criteria are operational and include hard gates |
| Analysis | No defensible choice | Chooses without a rule | Correctly applies a rule | Tests sensitivity and explains a ranking change |
| Critical evaluation | Treats score as truth | Gives a vague limitation | Identifies a concrete failure | Proposes calibration, auditing, and abstention |

Suggested mastery threshold: 9 of 12 points, with no zero in any category.

## Exit ticket

1. `N` is the number of candidate outputs generated and considered for one input or condition.
2. Hard gates prevent a severe failure from being hidden by high scores on other criteria.
3. A misaligned selector can optimize an incomplete proxy, such as choosing the densest fog while ignoring vehicle deformation or unstable motion.
