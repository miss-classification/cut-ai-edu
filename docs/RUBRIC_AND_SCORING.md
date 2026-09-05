# Rubric and Score Provenance

**Authors:** Alicia Chua, Pawarit Laosunthara, and Eric Tang, Anyscale

## Read this before interpreting the numbers

The website uses **fixed illustrative annotations**. The values were created through visual inspection to make weighted selection and selector sensitivity interactive. They are not:

- ground-truth labels
- benchmark measurements
- outputs from a live VLM
- validated autonomous-driving metrics
- safety certification
- evidence that any generated clip is suitable for deployment or training

The exact values appear in `data/rubric_scores.csv`. Their role is pedagogical: a learner can change what the selector values, see the ranking respond, and identify how a narrow proxy can reward an undesirable artifact.

## Current annotation procedure

The current 0-to-100 values were entered as fixed lesson values during resource construction after visual inspection of each candidate. A formal rater count, blinded order, independent rating set, and collection date were not recorded. The values therefore function as a transparent worked example, not as empirical human-evaluation data. The stronger protocol below describes how to collect new ratings for a research or classroom extension.

## Dimensions used in the lesson

### Weather fidelity

Question: Does the candidate visibly express the requested moderate fog while preserving the near-field visibility described by the prompt?

Observable evidence includes fog distribution, distant contrast loss, near-field visibility, and whether the condition resembles fog rather than a localized smoke plume.

### Structure preservation

Question: Are the road, lane markings, vehicles, pedestrians, buildings, cones, and camera geometry consistent with the source?

Observable evidence includes topology, object identity, object shape, relative position, and continuity of important boundaries.

### Temporal stability

Question: Do objects, atmosphere, and camera motion remain coherent over time?

Observable evidence includes flicker, object deformation, identity changes, abrupt lighting changes, teleportation, and discontinuous motion.

## Recommended human-rating anchors

Use these 1-to-5 anchors when collecting fresh classroom ratings.

| Score | Weather fidelity | Structure preservation | Temporal stability |
| ---: | --- | --- | --- |
| 1 | Condition absent or incorrect | Major road, lane, vehicle, or object changes | Frequent flicker, teleportation, or identity breaks |
| 2 | Condition weak or spatially inconsistent | Clear deformation or object drift | Repeated jitter or instability |
| 3 | Condition recognizable but imperfect | Minor defects that do not dominate the clip | Occasional transient artifacts |
| 4 | Condition clear and plausible | Important scene structure largely preserved | Motion and appearance largely stable |
| 5 | Target severity coherent across the scene | Road layout and important actors closely match the source | Stable throughout the clip |

## Hard gates come first

A weighted average should not compensate for critical failures. Before scoring, reject a candidate when any agreed gate fails. Example gates include:

- lane topology changes
- a vehicle or pedestrian disappears
- an important actor changes identity
- physically impossible motion occurs
- a major camera discontinuity occurs
- the requested condition is absent

If every candidate fails, `select none` is a valid result.

## Lesson score

For eligible candidate `i`, the lesson computes:

```text
S_i = (w_weather * weather_i
     + w_structure * structure_i
     + w_stability * stability_i)
     / (w_weather + w_structure + w_stability)
```

The candidate with the largest `S_i` is displayed. The browser performs no uncertainty estimation and no independent validity check.

## Stronger annotation protocol

For a research or classroom extension:

1. Randomize candidate order and conceal seed identifiers.
2. Define each criterion using observable evidence.
3. Review one calibration example together.
4. Have at least two reviewers rate the remaining clips independently.
5. Record ratings, confidence, short explanations, and failure timestamps.
6. Apply hard gates before averaging scores.
7. Report reviewer disagreement rather than hiding it.
8. Examine ranking sensitivity to weights and rating uncertainty.
9. Validate the selector on held-out clips and conditions.
10. Avoid the term expert ground truth unless expertise and validation justify it.

## What could power a production quality gate?

A practical AV quality gate could combine:

- **Human calibration:** defines what the application values and supplies reference judgments.
- **Deterministic vision checks:** evaluates edge or depth consistency, object retention, tracking, optical flow, flicker, and visibility.
- **VLM review:** evaluates semantic condition match and describes visible failures.
- **Hard safety rules:** reject critical failures before ranking.
- **Abstention:** retain no candidate when evidence is weak or all candidates fail.

A VLM is one source of evidence. The complete judge is the rubric, evidence, thresholds, and decision rule together.
