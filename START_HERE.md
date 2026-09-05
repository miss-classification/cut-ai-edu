# How Do You Test Weather You Cannot Schedule?

**Authors:** Alicia Chua, Pawarit Laosunthara, and Eric Tang, Anyscale

## A visual lesson on verifier-guided test-time scaling for generative video

This package teaches verifier-guided test-time scaling for generative video. Best-of-N selection is the simplest observable mechanism: a stochastic generator spends more compute by producing several candidates, but the final result improves only when a suitable selector can recognize what the application needs.

The lesson uses controllable driving-video generation as a concrete case study. NVIDIA Cosmos Transfer 2.5 creates fog, rain, and snow variants from one recorded drive. A browser-based audition then lets learners inspect candidate variation, change an application rubric, and observe how the selected video changes. Ray is shown only in the optional production notes as the mechanism used to run independent samples concurrently.

## Start the lesson

Open `interactive/index.html` in a modern browser. If the browser restricts local video playback, serve the package directory with any static file server, for example:

```bash
python -m http.server 8000
```

Then open `http://localhost:8000/interactive/`.

No account, internet connection, GPU, model download, or Python environment is required for the core lesson.

## Teaching routes

### Five-minute conference demo

1. Ask the opening question and show the controlled weather transformation.
2. Invite a blind vote between two candidates.
3. Expand the candidate budget from N=1 to N=4.
4. Reveal the selected clip.
5. Move the judge weights once to make the winner change.
6. Close with: "Generation creates options. The judge turns options into a decision."

### Fifteen-minute guided lesson

Use the opening episodes, blind vote, full N=1/2/4/8 audition, selector lab, production-judge explainer, and two-question knowledge check.

### Thirty-to-forty-minute classroom activity

Use `docs/LEARNER_WORKSHEET.md` before revealing the provided scores. Learners define their own operational rubric, add at least one hard rejection gate, compare rankings, and transfer the design to another domain.

## What learners should leave with

Learners should be able to:

1. Explain Best-of-N as generation, scoring, and selection.
2. Identify what is held fixed and what varies in a controlled candidate pool.
3. Apply and critique a multi-criterion selector.
4. Explain why increasing N adds compute but does not guarantee improvement.
5. Distinguish human calibration, deterministic vision metrics, VLM review, and hard safety gates.
6. Design a selector for a different generative task.

## Important scope statement

The interactive scores are fixed illustrative annotations created for teaching. They are not ground truth, benchmark measurements, a validated autonomous-driving evaluator, or a safety certification. No video-language model runs inside the lesson. `docs/RUBRIC_AND_SCORING.md` explains the score provenance and a stronger protocol for future classroom use.

## Package map

- `interactive/`: complete offline lesson, source code, and compressed video examples
- `docs/TEACHING_GUIDE.md`: timing, facilitation prompts, misconceptions, and reuse guidance
- `docs/LEARNER_WORKSHEET.md`: prediction, rubric design, scoring, sensitivity, and transfer activity
- `docs/ANSWER_KEY.md`: suggested answers and discussion guidance
- `docs/RUBRIC_AND_SCORING.md`: video-rating anchors, score provenance, and human-calibration protocol
- `docs/REPRODUCIBILITY.md`: fixed generation settings, hardware record, and limitations
- `docs/ACCESSIBILITY_AND_REUSE.md`: accessibility features and adaptation guidance
- `docs/MEDIA_PROVENANCE.md`: file-by-file media origin, edits, and rights boundary
- `data/rubric_scores.csv`: the values used by the interactive selector
- `notebooks/selector_lab.ipynb`: a hardware-free lab on weight sensitivity and rating uncertainty
- `source/scoring.py`: a small dependency-free implementation of weighted selection
- `source/experiments/`: portable reference configurations, prompts, settings, and random seeds
- `source/manifests/`: sanitized generation records
- `generation/`: Ray and Cosmos execution wrapper, cluster experiment files, tests, and setup guidance
- `references/REFERENCES.bib`: linked research papers and implementation references
- `ORIGINALITY.md`: originality and scope statement
- `THIRD_PARTY_NOTICES.md`: software, model, and media attribution

## The central idea

For source video `v`, condition `c`, generator `p`, and application rubric `r`:

```text
y_1, ..., y_N ~ p(. | v, c)
y* = argmax_i score_r(y_i; v, c)
```

Increasing N expands the search. The selector determines whether that extra search produces a useful decision.
