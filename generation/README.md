# Video generation source

This directory contains the Ray wrapper and experiment definitions used to execute independent NVIDIA Cosmos Transfer 2.5 samples in parallel for the lesson.

## Contents

- `cosmos_ray/`: task validation, sweep expansion, worker environment setup, model actors, execution, manifests, and output utilities
- `experiments/`: the eight-seed fog experiment and four-seed rain and snow extension
- `tests/`: driver-side tests that do not require Cosmos, Ray, PyTorch, or a GPU

## Requirements

Full generation requires the upstream [Cosmos Transfer 2.5](https://github.com/nvidia-cosmos/cosmos-transfer2.5) source and model access, compatible NVIDIA hardware, Ray, shared storage visible to every worker, and acceptance of the applicable upstream terms.

The wrapper was developed for an Anyscale-style Ray cluster whose workers share `/mnt/user_storage`. Change the input, output, source, environment, and cache paths for your own cluster. Do not commit tokens. The wrapper reads Hugging Face credentials from the worker environment or the standard Hugging Face token cache.

## Validate first

From the repository root:

```bash
export PYTHONPATH="$PWD/generation"
python -m cosmos_ray plan generation/experiments/directors_cut.yaml
python generation/tests/test_cosmos_ray.py
```

`plan` expands the sweep, validates task fields, checks inputs, confirms that worker-visible paths use supported shared-storage prefixes, and checks the configured worker environment. It does not start a generation run.

## Run

```bash
python -m cosmos_ray run generation/experiments/directors_cut.yaml --engine actor-pool -n 4
python -m cosmos_ray run generation/experiments/weather_replication.yaml --engine actor-pool -n 4
```

Each actor holds one model replica and processes multiple tasks. The fog experiment produces eight candidates in two waves on four GPUs. The rain and snow experiment produces four candidates for each condition.

Guardrails are enabled by default. A blocked sample is recorded as `guardrail_blocked`. For controlled research reproduction only, `--disable-guardrails` explicitly disables them. Review generated media before use.

## Recorded lesson configuration

| Setting | Value |
| --- | --- |
| Cosmos source revision | `2ff49d0` |
| Model configuration | `edge/distilled` |
| Denoising steps | 4 |
| Guidance | 4 |
| Frames | 93 |
| Edge weight | 0.65 |
| Parallel workers | 4 |
| Recorded GPU type | NVIDIA L40S |

The exact model-weight revision was not recorded. Results may change with the model revision, environment, source clip, prompt, seed, or upstream implementation. See `../docs/REPRODUCIBILITY.md` for the complete record and limitations.
