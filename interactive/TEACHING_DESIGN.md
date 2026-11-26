# Teaching design and verification

The lesson keeps verifier-guided test-time scaling as its central concept. Broader weather transformations supply additional evidence and failure cases rather than replacing that concept with a general video gallery.

| Learning need | Experience in the website | Evidence of understanding |
| --- | --- | --- |
| Understand test-time scaling before operating controls | Opening explanation, video-generation overview, and expandable background | Distinguishes inference computation from model training |
| Compare candidate-retention policies | Nested N pools and retain-all versus Best-of-N explanation | Explains that retaining all preserves failures as well as useful candidates |
| See why an illustrative candidate received a score | Candidate inspector, observations, full score table, and weighted calculation | Connects a score to an observation and critiques its precision |
| Apply gates before ranking | Worked threshold diagram and interactive fog thresholds | Excludes failed candidates and explains an empty eligible set |
| Understand a concrete verifier | Blind and paired VLM inputs, exact responses, frame rates, prompts, and output fields | Explains why realism and requested-condition match differ |
| Recognize verifier failure | Invented hood with full marks and the 735/735 structure-score ceiling | Identifies a conflict between textual evidence and a numeric score |
| Evaluate the comparison design | Boreas different-day snow reference and one-case GOOSE prompt test | States what each comparison can and cannot establish |
| Transfer the method to another task | Integrated worksheet and instructor assessment guide | Specifies criteria, evidence, rejection, abstention, and independent validation |
| Distinguish model quality from execution speed | Optional Ray actor benchmark and hardware notes | Distinguishes per-request time, batch time, and output usefulness |
| Reuse the material in a class | Embedded 5-minute, 15–20-minute, and 35–40-minute routes | Instructor can teach from the website without searching offline files |

## Visual and functional design

The animated network and temporal edge strip remain the visual introduction. The output receives more screen area. Videos have descriptive labels and playback controls; motion can be paused. The original quality-gate placeholder is replaced by a fully specified example. Candidate selection is separated from native video playback controls.

The larger showcase is deliberately selective: flooded mud, a rail-yard condition wall, golden hour, night rain, and snow. The main path includes only the evidence needed for its questions. Methods, model tuning, and hardware detail are expandable or linked as optional depth.

## Verification limit

Static and behavior checks passed. Browser rendering, playback, keyboard order, and print layout remain to be checked manually. This distinction is material for a previously reported playback issue; valid assets and decoding do not by themselves prove browser behavior.

## Additional comparison choices

The expandable viewer offers 10 examples across 4 themes. Flooded terrain raises geometry and traversability questions. Frost and fog expose appearance-versus-preservation tradeoffs. Moving wildlife introduces subject identity and gait. Winter roads expose lighting changes and details that snow previously concealed. The learner follows a specific feature over time before consulting a judge. These cases broaden the original fog lesson without adding an always-visible video wall.

## Poster route and final assessment

The 6-stop projector route begins with the original controlled fog comparison. It then separates 3 decisions: how much to sample, which criterion to rank, and whether anything is eligible. An optional worked calculation connects the winning score to its component values. The VLM walkthrough and the 2 recorded counterexamples distinguish what the model was asked from what it observed. Case titles and player labels do not disclose the outcome before the reveal.

The final activity is an unfamiliar case rather than a recap. Learners compare the same time point in recorded and generated footage, supply a retention decision, and name a visible reason. The local screening log pins the frame time (or identifies a poster frame) so another viewer can return to the evidence. Look for a reason tied to the requested condition and a specific feature that should be preserved. Credit a well-supported rejection or request for further evidence. A short film and the original four-condition montage remain optional.

The full lesson retains the in-page course roadmap, source material, and a design exercise for a new task. The opening, retention-policy comparison, reveal, methods drawers, and teaching guide use shorter labels and complete sentences. The initial counterfactual output can also be opened in a larger player.


## Findings and open questions

The first projector audit uses the GOOSE frost case. Its neutral title permits a blind assessment. The named case file gives instructors a direct route to a time-matched source/output frame and the recorded disagreement between the added-object list and structure rating. The lesson debrief pairs each observed result with a specific validation experiment that has not been performed. No downstream improvement to a driving model is inferred from the clips.

For close inspection, use the native-width divider or the still pair. The source comparisons were supplied as web proxies; full-screen projection can enlarge their pixels but cannot restore full-resolution masters.
