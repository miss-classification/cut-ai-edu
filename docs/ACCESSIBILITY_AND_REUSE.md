# Accessibility and Reuse Guide

**Authors:** Alicia Chua, Pawarit Laosunthara, and Eric Tang, Anyscale

## Access modes

The lesson supports three use modes:

1. A five-minute live demonstration for a conference room.
2. A fifteen-minute self-guided browser lesson.
3. A thirty-to-forty-minute classroom activity with a worksheet.

The core browser lesson works offline. It does not require a login, GPU, model download, or notebook environment.

## Current accessibility features

- A skip link moves directly to the main lesson.
- Major sections use semantic headings and landmarks.
- Interactive controls use native buttons where possible.
- Videos include descriptive accessible labels.
- The lesson does not depend on spoken audio.
- Essential meaning appears in adjacent text, not in video alone.
- Selection state uses text and shape in addition to color.
- Episode tabs support left and right arrow keys.
- The opening animation stops after user interaction.
- A persistent control pauses or resumes motion across the lesson.
- Reduced-motion preferences disable automatic playback.
- The teaching guide and worksheet provide text-only alternatives.
- The site is responsive for laptop, tablet, and phone layouts.

## Facilitator practices

For a live session:

1. Read the opening question aloud.
2. Describe the source scene before playing variants.
3. State the visible differences that motivate each rubric dimension.
4. Repeat audience vote results verbally.
5. Do not rely on red, green, or animation alone.
6. Pause clips when discussing a single artifact.
7. Share both a QR code and a typed URL.
8. Offer the worksheet in an editable digital format.
9. Allow learners to inspect clips at their own pace after the session.

## Text alternative for the main visual sequence

One clear urban driving clip is transformed into several weather variants. Edge control asks the generator to retain road and object boundaries. Eight fog candidates use the same source, prompt, model, and settings. Only the random seed changes. The candidates vary in weather strength, structure preservation, and temporal stability. A weighted selector ranks the eligible pool. A balanced rubric selects Take 04. A weather-only rubric selects Take 07, whose strong atmosphere also resembles a smoke-like plume. This contrast shows why a larger candidate pool needs a task-aligned selector and hard rejection gates.

## Known limitations

- The site has not received a formal WCAG conformance audit.
- Browser support for embedded H.264 video varies.
- A screen reader cannot fully convey every temporal artifact in a visual clip.
- The current score sliders expose point estimates without uncertainty intervals.
- The current clips contain no spoken narration or meaningful audio, so captions are not required for comprehension.
- Some advanced model and infrastructure details remain in the written guide instead of the main interaction.

Use the text alternative, worksheet, and facilitator description when video inspection is not accessible to a learner.

## Reusing the lesson with new media

The teaching sequence is model and domain independent:

```text
predict -> inspect -> formalize -> perturb -> diagnose -> transfer
```

To replace the driving example:

1. Choose a stochastic generative task with visible candidate variation.
2. State which inputs and settings remain fixed.
3. Change one controlled source of variation, such as a seed.
4. Define two or three observable quality dimensions.
5. Add non-negotiable rejection gates.
6. Collect ratings with concealed candidate order.
7. Replace `data/rubric_scores.csv` with the new values.
8. Update the video file map in the interactive JavaScript.
9. Test at least two weight profiles.
10. Ask learners to design a selector for another domain.

Good transfer domains include robotics, code generation, scientific surrogates, medical image generation, and synthetic training data.

## Collecting stronger classroom annotations

For a larger class, assign at least two independent raters per candidate. Record a score, confidence, visible rationale, and failure timestamp. Report disagreement. Do not average away hard failures. Validate the rubric on held-out examples before making claims about general performance.

## Reuse and rights

The package separates original lesson materials from third-party software, model, and media references. Original educational content is licensed under CC BY 4.0 and original code is licensed under Apache 2.0. Review `LICENSE_SCOPE.md` and `THIRD_PARTY_NOTICES.md` before redistribution.
