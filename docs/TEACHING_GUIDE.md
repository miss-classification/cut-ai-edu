# Teaching Guide

**Authors:** Alicia Chua, Pawarit Laosunthara, and Eric Tang, Anyscale

## Lesson title

**How Do You Test Weather You Cannot Schedule?**

Technical subtitle: **A visual lesson on verifier-guided Best-of-N scaling for controllable video**

## What this lesson teaches

The lesson teaches a generator-selector pattern that now appears across reasoning, alignment, image generation, and video generation:

1. Generate several candidates with a fixed model and condition.
2. Evaluate each candidate against an application-specific rubric.
3. Keep the highest-ranked eligible candidate, or abstain if none is acceptable.

The video case study makes the selector bottleneck visible. Learners can see that the most dramatic weather effect may not be the most useful AV test case. They also see that adding candidates cannot repair an incomplete or misaligned definition of quality.

## Audience and prerequisites

- Recommended level: first-year university through graduate study
- Also appropriate for first-time NeurIPS attendees and technical practitioners outside computer vision
- Required background: basic random sampling, random seeds, weighted averages, and the idea of conditioning a generative model
- Not required: diffusion mathematics, AV expertise, Python, Ray, CUDA, or GPU access

## Learning objectives

By the end, learners should be able to:

1. Explain the three components of Best-of-N: generator, candidate pool, and selector.
2. State what remains fixed and what varies across the fog audition.
3. Use observable evidence to define weather fidelity, structural fidelity, and temporal stability.
4. Apply a weighted score after hard rejection gates.
5. Predict how changing rubric weights can change the winner.
6. Explain why a larger candidate pool may increase cost without improving the selected result.
7. Distinguish human calibration, deterministic vision metrics, VLM review, and safety gates.
8. Transfer the selector design to a different generative task.

## Preparation

1. Open `interactive/index.html` or serve the package locally.
2. Confirm all clips load before the session.
3. Press `Reset` so no earlier choice remains.
4. Verify that Take 04 is not identified as the lesson rubric selection before the learner submits a ranking.
5. Prepare `LEARNER_WORKSHEET.md` for the longer activity.
6. Provide both a QR code and a typed URL if the lesson is hosted.
7. Keep a local copy available in case conference Wi-Fi is unreliable.

The video generation has already been completed. Learners need no GPU.

## Five-minute live demonstration

### 0:00 to 0:45 | The hook

Show the headline: "How do you test weather you cannot schedule?"

Suggested narration:

> A fleet can collect millions of ordinary miles and still miss the exact combinations it needs. Suppose we have one clear drive and need a plausible fog case. A controllable video model can restage the scene, but it does not produce the same result every time.

### 0:45 to 1:30 | Controlled restaging

Use the opening weather switch. Show source plus edge control, then fog, rain, and snow.

Ask:

> What must change, and what must remain recognizable?

State that this experiment used edge conditioning. Depth is another supported control, but was not used for these clips.

### 1:30 to 2:15 | Blind vote

Show the two candidate clips and ask the room to vote.

Prompt:

> Do not choose the prettiest clip. Choose the one you would be more willing to place in a test dataset. What failure are you accepting?

### 2:15 to 3:15 | Scale N

Open the audition. Move from N=1 to N=2 and N=4. Explain that the model, prompt, source, and settings are fixed; only the seed changes.

### 3:15 to 4:20 | Reveal and perturb the rubric

Submit a ranking and reveal the example rubric's selection. Move the selector to `Fog only` and show how a narrow proxy can reward an undesirable artifact.

Ask:

> Did the generator fail, or did the judge ask the wrong question?

### 4:20 to 5:00 | Close

Show the production-judge explainer.

Close with:

> More inference compute buys options. It does not buy judgment. A larger pool helps only when useful candidates exist and the selector can rank them reliably.

## Fifteen-minute guided lesson

| Time | Activity | Teaching purpose |
| --- | --- | --- |
| 0:00-2:00 | Missing cases and controlled transformation | Establish the AV problem before terminology |
| 2:00-4:00 | Blind vote | Make every learner act as a selector |
| 4:00-7:00 | N=1/2/4/8 audition | Connect sample budget to search and cost |
| 7:00-10:00 | Reveal and weighted rubric | Formalize `argmax` selection |
| 10:00-12:30 | Change weights | Demonstrate sensitivity and proxy failure |
| 12:30-14:00 | Production judge | Separate human, metric, VLM, and safety evidence |
| 14:00-15:00 | Knowledge check | Retrieve the mechanism and limitation |

## Thirty-to-forty-minute classroom activity

### Phase 1 | Predict before scoring

Learners inspect the candidates without scores and record:

- one selected clip
- confidence from 1 to 5
- two visible reasons
- one unacceptable failure

### Phase 2 | Operationalize quality

In pairs, learners define three observable criteria and one hard rejection gate. Require operational language. "Looks good" is not an acceptable criterion; "lane topology remains unchanged" is.

### Phase 3 | Apply the selector

Learners assign weights summing to 100, calculate scores for eligible candidates, and compare the winner with their blind vote.

### Phase 4 | Stress-test the decision

Learners create a second mission profile, change the weights, and record whether the winner changes. Ask them to report the score margin and whether the ranking appears stable.

### Phase 5 | Transfer

Each group designs a three-criterion selector and one hard gate for another domain, such as robotic manipulation, medical image generation, scientific surrogates, warehouse simulation, or code generation.

## Facilitation prompts

- Which visible property made you trust one candidate more?
- Were you choosing visual appeal or fitness for purpose?
- Whose priorities are encoded in these weights?
- What failure must never be averaged away?
- If moving one weight by five points changes the winner, what does that tell us?
- Does generating eight candidates make the final decision eight times more trustworthy?
- When should the system select none?
- What evidence can a VLM provide, and what can it miss?

## Common misconceptions

**"More samples guarantee improvement."**

No. More samples enlarge the pool. Improvement also requires generator coverage and reliable selection.

**"The highest weighted average is safe."**

No. A severe failure can be hidden by high scores elsewhere. Apply hard gates first.

**"A VLM is the judge."**

A VLM can provide semantic evidence. The full judge also includes the rubric, thresholds, other measurements, and a decision rule.

**"The scores are measurements."**

The current values are fixed illustrative annotations. They support a lesson, not an autonomous-vehicle benchmark.

**"Ray improves generation quality."**

Ray runs independent samples concurrently. It changes throughput, not the quality criterion.

**"The weather prompt changes between fog takes."**

It does not. Only the random seed changes in the eight-take fog audition.

**"Synthetic weather certifies AV safety."**

It does not. This resource teaches candidate triage and evaluation design.

## Assessment

Use the two embedded questions for rapid retrieval. Use the worksheet's transfer challenge for higher-order assessment.

Suggested mastery threshold for the transfer challenge: 9 of 12 points, with no zero in any category.

| Category | 0 | 1 | 2 | 3 |
| --- | --- | --- | --- | --- |
| Mechanism | Cannot describe Best-of-N | Mentions multiple samples | Separates generation and selection | Explains diversity, selection, and cost |
| Rubric design | No criteria | Subjective criteria only | Observable criteria | Operational criteria plus hard gates |
| Analysis | No defensible selection | Choice without calculation | Correctly applies score | Tests sensitivity and explains a change |
| Critical evaluation | Treats score as truth | Names a vague limitation | Identifies a concrete failure | Proposes calibration, auditing, and abstention |

## Reuse and adaptation

Educators may replace the clips, conditions, and scoring dimensions while keeping the learning sequence:

```text
predict -> inspect -> formalize -> perturb -> diagnose -> transfer
```

For an introductory audience, hide the equation and production notes. For an advanced audience, use `source/scoring.py` and ask learners to analyze weight sensitivity or rating uncertainty.
