# Evidence inventory

This extension accompanies CUT! Best-of-N Studio. It is based on the supplied November 2026 source, evidence, and showcase snapshots. It does not replace the original fog experiment with the later evaluation.

## Claim-to-record mapping

| Finding | Supplied record | Treatment in the lab |
| --- | --- | --- |
| 735 of 735 paired structure scores equal 5 | CUT-evidence.zip: runs/eval_v4/show4/vlm.jsonl | Recomputed from all 735 raw paired responses, rather than inferred from a rounded mean. |
| Invented hood is listed but structure scored 5 | Same JSONL, request 88959458ef3e47d4c208 | Full blind and paired responses included in reviewed-data.json. |
| Night rain stays daytime, condition score 2 | Same JSONL, request 315464a22d1ebec3ee86 | Full blind and paired responses included. |
| 58 requested cases per initial configuration | runs/eval_v4/main/summary.json | Counts and per-variant means retained. Cosmos 3 generated 57 and blocked 1 per configuration. |
| 16-case Nano tuning study | runs/eval_v4/c3tune/summary.json; repo/docs/cosmos3_tuning.md | Deliberately selected tuning set. Exploratory, with no general ranking claim. |
| 24-request Ray actor scaling | repo/results/benchmark/scaling.json | Exact timings retained; private workspace locations omitted. |
| B200 depth probe | runs/depth_probe/main/probe_result.json | Measured load 64.7 s, generation 172.1 s. Private host and output paths omitted. |
| A100 depth probe | Supplied handoff text, depth-probe and Phase 5 notes | Reported load 212 s, generation 868 s. Original A100 raw JSON was absent from this handoff. |
| Showcase selection | repo/docs/depth_showcase_picks.md | Curated examples with seeds, not a measured acceptance rate. |
| Judge prompts and sampling | CUT-source.zip: cosmos-offroad-ray/jobs/eval_v4.py | Exact prompts included in reviewed-data.json. |

## Calculations

- End-to-end actor speedup = 2067.75 / 398.39 = 5.1903.
- Generation-window speedup = 1958.07 / 280.67 = 6.9764.
- Reported A100/B200 single-probe generation ratio = 868 / 172.1 = 5.0436. The A100 value is supported by notes, not its original raw record.
- The 16-case tuning means are 3.688 before tuning and 4.250 with depth remap plus guidance 1.0. Display rounding gives 3.69 and 4.25.
- No H100 timing, price comparison, downstream model-training gain, or independently measured acceptance rate is available.

## Protocol and limits

The judge is Qwen3-VL-32B-Instruct, with greedy decoding and at most 700 output tokens. Blind review samples 4 frames per second and sees the generated clip. Paired review samples 3 frames per second and sees the real source, generated output, and target condition. Model-generated scores and explanations are not human labels.

The interactive exclusion controls use the supplied documented failures. They are an explicit rule exercise, not live inference or automatic object detection. An absence of an exclusion does not imply approval.

The supplied Cosmos 3 trial used text filtering and face blurring. Its generated-video content filter was disabled. The Transfer 2.5 path had a different guardrail configuration. A guardrails request flag alone does not establish identical coverage across these runs.

The recorded source snapshot identifies commit 1a9ac3f371b0465cdb78b4caaba4a887ad7532ab, with uncommitted curation additions. The archive is the reviewed source of record; the remote repository may change. No claim is made that this static site runs the generation service.

## Reuse

Media credits and applicable licenses are in media-manifest.json and in the video footers. The 21 extension videos are unchanged copies of the supplied compressed comparisons. Selected examples are not the complete 339-video archive. More selected renders are in the online Paint the Trail Gallery, linked from the lesson.

## v28 educational additions

- The rail-yard condition wall is show_grandtour_web/grandtour_wall_6.mp4. It contains one real source and 7 selected generated conditions.
- Boreas same420_snow compares a sunny source, depth-guided snow, edge-guided snow, and a real snowy drive at a matched camera location on another day. The same-place matching method is documented in jobs/fetch_boreas_sameplace.py. Traffic and viewpoints differ.
- The GOOSE drought comparison holds the model and seed fixed and changes the prompt. The explanatory prompt descriptions on the page are paraphrases. The saved scene-aware prompt is supplied in prompt-example.json.
- fog-annotations.json supplies explanatory prose for the pre-existing illustrative scores. The prose is a new teaching interpretation, not a recovered annotation log. It must not be described as an empirical metric or an independently validated rating.
- The score inspector exposes the weighted calculation. Gates precede scoring; zero eligible candidates lead to abstention. Zero weights produce no ranking.
- The first architecture diagram retains the original network animation and temporal edge strip. Its output area is enlarged. The quality-gate diagram is now a worked example with thresholds 80 and 97, rather than an unfulfilled vote-reveal placeholder.

## v29 selected transformations

The 10 additional comparisons match the supplied selection screenshot, including the exact seeds. selected-comparisons.json identifies their source, preservation focus, and inspection question. Media bytes and embedded credits are unchanged. Visual inspection sampled each clip at 15%, 50%, and 85% of its duration; this is not a full quality annotation or acceptance assessment.

The Wikimedia examples come from commons_show4_depth, separate from the 735-clip show4 audit. No numeric judge badge was inferred from the screenshot. Source credits were checked against the two original Wikimedia file pages on 2026-11-26.

## Poster edition

- walkthrough.json: exact blind and paired records for GOOSE flooded mud, seed 101, request 87dabe390a3e2f4d6b17. The illustrated review question is a paraphrase; the complete evaluation prompt is in this file.
- field-reel.json: chapter times, source hashes, credits and modifications for the closing film, animation source and neutral-caption case copies. The live divider draws both panels from one decoded comparison video, preserving their encoded temporal alignment.
- The umbrella-to-snow sequence comes from the original GrandTour comparison dated 2024-10-01-11-29-55. No seed is claimed for that comparison.
- The VLM field animation uses the saved words “muddy brown water pools in ruts” and a condition rating of 5/5. This is the model's recorded judgment, not independent verification of water depth, scene geometry or safety.


## Native-picture edition

- picture-quality.json distinguishes original file preservation from the fidelity of the new edited exports. Crop coordinates are in decoded comparison pixels.
- hood-case.json contains the matched record, exact model responses and a separately labelled visual observation at 2.875 seconds.
- lesson-findings.json separates the observations from proposed validation. No error rate or downstream benefit is inferred from a uniformly high structure score.
