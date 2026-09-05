# Reproducibility Record

**Authors:** Alicia Chua, Pawarit Laosunthara, and Eric Tang, Anyscale

## What can be reproduced without a GPU

The core lesson is self-contained. Open `interactive/index.html` in a modern browser. All lesson videos are bundled. No account, network connection, model download, or Python environment is required.

The selector calculation is also reproducible with the Python standard library:

```bash
python source/scoring.py --n 8
python source/scoring.py --n 8 --weather 100 --structure 0 --stability 0
python source/scoring.py --n 8 --reject take07
```

The first command uses the balanced weights shown in the website. It selects `take04`. The second command demonstrates proxy failure. A weather-only rubric selects `take07`, even though its atmosphere resembles a smoke-like plume and its structural and temporal annotations are weaker.

## Controlled generation design

The fog audition isolates random sampling. The following settings remain fixed across all eight candidates:

| Item | Fixed value |
| --- | --- |
| Generator | NVIDIA Cosmos Transfer 2.5 |
| Model configuration | `edge/distilled` |
| Source video | Bundled car example clip |
| Prompt | One moderate-fog prompt |
| Denoising steps | 4 |
| Guidance | 4 |
| Control | Edge |
| Edge control weight | 0.65 |
| Frames | 93 |

Only the random seed changes:

```text
2025, 7319, 18427, 29063, 41851, 57203, 70439, 91873
```

The rain and snow extension changes the requested weather condition. It uses four fixed seeds for each condition. The source, model, steps, guidance, frame count, and edge weight remain fixed.

## Why edge control was used

Cosmos Transfer supports several spatial control modalities, including edge and depth. These examples use edge control. They do not use depth control.

Edge conditioning was selected because a distilled edge checkpoint fit the available single-GPU setup. The non-distilled depth configuration did not fit the available L40S memory budget. The website includes an illustrative depth diagram only to distinguish the modalities. It labels depth as supported but not used.

Edge maps preserve visible boundaries well. They can also carry appearance cues from the source. This makes the control weight a meaningful tradeoff. A high weight can preserve geometry while resisting the requested weather. A low weight can permit stronger restaging while increasing structural drift. A short pilot selected 0.65 for this lesson.

## Recorded software and hardware

The generation environment recorded during the run used:

- Python 3.13.14
- PyTorch 2.9.1 with CUDA 13.0 support
- cuDNN 9.21.1.3
- Ray 2.56.0
- NVIDIA Cosmos Transfer 2.5, source revision `2ff49d0`
- NVIDIA Cosmos Transfer 2.5 distilled edge checkpoint at `distilled/general/edge`
- Four NVIDIA L40S GPUs for the parallel eight-candidate runs

The exact Hugging Face model revision was not recorded. The source revision above is abbreviated because that is the identifier preserved in the run notes.

Four independent Ray actors each loaded one model replica. The eight samples then ran in two waves. Ray changed throughput, not the model output distribution or the selection rule.

| Run | Tasks | GPUs | Mean generation time per task | Recorded wall clock |
| --- | ---: | ---: | ---: | ---: |
| Fog audition | 8 | 4 | 106.0 s | 474 s |
| Rain and snow extension | 8 | 4 | 105.0 s | 381 s |

These timings describe one run. They are not a performance benchmark.

## Guardrail status

The experiment console summary available during preparation reported `guardrails: disabled`. The surviving records do not establish whether separate safety checks were applied elsewhere in the workflow. Treat the bundled clips as unverified generated media, review them independently, and follow NVIDIA's current model terms.

## Generation records

Portable reference experiment configurations are in:

- `source/experiments/directors_cut.yaml`
- `source/experiments/weather_replication.yaml`

The paths in those files assume execution from the teaching package root. The files record the schema used by the companion `cosmos_ray` experiment runner. They are reference configurations, not commands for the upstream Cosmos CLI.

Sanitized run records are in:

- `source/manifests/directors_cut_public.jsonl`
- `source/manifests/weather_replication_public.jsonl`

The public manifests retain task names, conditions, seeds through the experiment files, generation times, model labels, output shapes, checksums, contrast summaries, and peak GPU memory. Machine names, private paths, tokens, and internal service details were removed.

## Fingerprint scope

Each manifest checksum describes the original full-resolution generated output. The teaching package contains compressed web proxies. Transcoding changes file bytes, so a proxy will not match the full-resolution checksum.

To verify the teaching package itself, use the `SHA256SUMS` file created with the final ZIP. Those checksums apply to the files that are actually distributed.

## Optional regeneration

Full regeneration requires the upstream Cosmos Transfer software, compatible hardware, approved access to the applicable model weights, and acceptance of the relevant upstream terms. The adapter that maps the provided YAML schema to the Cosmos inference interface is included in `generation/cosmos_ray/`.

From the repository root, edit the shared paths in `generation/experiments/*.yaml`, then run:

```bash
export PYTHONPATH="$PWD/generation"
python -m cosmos_ray plan generation/experiments/directors_cut.yaml
python -m cosmos_ray run generation/experiments/directors_cut.yaml --engine actor-pool -n 4
python -m cosmos_ray run generation/experiments/weather_replication.yaml --engine actor-pool -n 4
```

The public runner enables upstream guardrails by default. The lesson's surviving run record reports that guardrails were disabled during the original generation. Use `--disable-guardrails` only when intentionally reproducing that controlled research setting, and review all generated media independently.

A careful regeneration should:

1. Use the source clip in `interactive/media/source.mp4`.
2. Use edge control, not the illustrative depth diagram.
3. Preserve the fixed prompt and parameters in the YAML.
4. Vary only the listed seeds for the fog audition.
5. Record software versions and model revisions.
6. Retain every candidate before human review.
7. Compare structural and temporal failures, not only visual appeal.
8. Record any guardrail, retry, or post-processing decision.

## Limits of the evidence

- The demonstration uses one source drive and a small candidate pool.
- The scores are fixed illustrative visual annotations.
- The scores were not collected through a blinded multi-rater study.
- The score dimensions are not validated AV safety metrics.
- No downstream perception or planning stack was evaluated.
- The weather outputs do not establish physical realism or safety.
- The lesson demonstrates selection mechanics, not deployment readiness.
- A different prompt, source, model revision, or transcode may change the results.

These limits are part of the lesson. Best-of-N is useful only when the candidate distribution contains useful outputs and the selector is aligned with the task.
