# Originality and Scope Statement

**Authors:** Alicia Chua, Pawarit Laosunthara, and Eric Tang, Anyscale

This educational resource was created specifically for the NeurIPS 2026 Education Track.

The following materials were created for this submission:

- the concept framing and learning sequence
- the interactive browser lesson
- the candidate audition and selector lab
- the controlled experiment design
- the prompts and seed matrices
- the fixed illustrative visual annotations
- the weighted scoring example
- the teaching guide, worksheet, and answer key
- the accessibility and reuse guidance
- the reproducibility record
- the diagrams, copy, styling, and presentation code
- the compressed teaching montage and lesson-specific media edits

The central teaching contribution is the connection between verifier-guided Best-of-N inference-time scaling and an observable video-selection task. The lesson asks learners to act as the selector before showing a formal rubric. It then exposes how rubric weights, hard gates, and proxy failures change the decision.

## Third-party foundations

The resource does not claim original authorship of:

- Best-of-N sampling or inference-time scaling
- NVIDIA Cosmos Transfer 2.5 software or model weights
- the published Cosmos car example input
- Ray software
- the research papers cited in the lesson

Cosmos Transfer 2.5 generated the weather variants from the published example input. Ray distributed independent generation jobs. Model weights are not included. The original source clip and derived teaching videos remain subject to the applicable upstream terms.

## Annotation status

The bundled 0-to-100 values are fixed illustrative visual annotations. They were created to teach weighted ranking and selector sensitivity. They are not ground truth, benchmark measurements, a validated autonomous-driving evaluator, a live video-language model output, or a safety certification.

## License scope

Original educational content is licensed under CC BY 4.0 and original code is licensed under Apache 2.0. Third-party material is excluded and listed in `THIRD_PARTY_NOTICES.md` and `LICENSE_SCOPE.md`.
