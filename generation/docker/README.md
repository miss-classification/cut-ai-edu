# Regenerate the candidates on H100 or B200

This folder holds one container image for regenerating the lesson's fog, rain, and snow candidates on NVIDIA H100 (Hopper) or B200 (Blackwell) GPUs. The browser lesson does not need any of this.

## What you need

- A Linux machine with NVIDIA H100 or B200 GPUs, NVIDIA driver 580 or newer (CUDA 13), Docker, and the NVIDIA Container Toolkit.
- A Hugging Face account that has accepted the terms for [`nvidia/Cosmos-Transfer2.5-2B`](https://huggingface.co/nvidia/Cosmos-Transfer2.5-2B) and its guardrail models, and a read token.
- About 60 GB of disk for the image and the model cache.

## 1. Build the image

From the repository root:

```bash
docker build -f generation/docker/Dockerfile -t cut-cosmos:cu130 .
```

The image contains Ray 2.60 on Python 3.13 with CUDA 13, the Cosmos Transfer 2.5 source at the lesson's recorded revision (`2ff49d0`), its Python environment, and this repository's `cosmos_ray` wrapper. It contains no model weights and no credentials.

## 2. Prepare the data and cache folders

```bash
export DATA=$HOME/cut-data        # inputs and generated videos
export CACHE=$HOME/cut-cache      # Hugging Face model cache
mkdir -p "$DATA/cosmos-tests/car" "$CACHE/hf"
curl -L -o "$DATA/cosmos-tests/car/car_input.mp4" \
  https://media.githubusercontent.com/media/nvidia-cosmos/cosmos-transfer2.5/2ff49d0717af02057ae79bc75c00fbff9da1b4e7/assets/car_example/car_input.mp4
```

This is the upstream Cosmos car example that the lesson restages. `$DATA` is mounted at `/mnt/user_storage`, so the paths in `generation/experiments/*.yaml` work without edits.

## 3. Start the container

```bash
export HF_TOKEN=...   # your Hugging Face read token; never commit it
docker run --rm -it --gpus all --ipc=host --shm-size=64g \
  -e HF_TOKEN \
  -v "$DATA":/mnt/user_storage \
  -v "$CACHE":/mnt/cluster_storage \
  cut-cosmos:cu130 bash
```

Inside the container, confirm the GPUs are visible:

```bash
"$COSMOS_VENV/bin/python" -c "import torch; print(torch.cuda.device_count(), torch.cuda.get_device_name(0))"
```

## 4. Plan, then run

```bash
ray start --head
FLAGS="--venv-path $COSMOS_VENV --cosmos-src $COSMOS_SRC --hf-home /mnt/cluster_storage/hf"

python -m cosmos_ray plan generation/experiments/directors_cut.yaml $FLAGS
python -m cosmos_ray run  generation/experiments/directors_cut.yaml $FLAGS --engine actor-pool -n 8
python -m cosmos_ray run  generation/experiments/weather_replication.yaml $FLAGS --engine actor-pool -n 8
```

`plan` checks inputs, paths, and the environment without generating anything. `-n` is the number of model replicas, one per GPU: use the number of GPUs in the machine. With 8 GPUs, the eight fog takes run at the same time. The first run downloads the checkpoints into `$CACHE/hf`.

Outputs are written to `$DATA/cosmos-runs/<experiment>/`. Guardrails are on by default; a blocked sample is recorded as `guardrail_blocked`.

## On a Ray cluster

Push the image to a registry your cluster can pull from and use it as the cluster image (on Anyscale, as the container image in the compute configuration). Every node must see the same shared storage at `/mnt/user_storage` and `/mnt/cluster_storage`. Run the same `plan` and `run` commands on the head node with the same flags.

## What to expect

- The settings are those recorded for the lesson: `edge/distilled`, 4 denoising steps, guidance 4, 93 frames, edge weight 0.65, guardrails on. The seeds are listed in the experiment files.
- The lesson's candidates were generated on NVIDIA L40S GPUs. On other GPUs, and with a different model-weight revision, the outputs will differ. Byte-identical regeneration is not claimed. See `docs/REPRODUCIBILITY.md`.
- Status: the build steps follow `generation/cosmos_ray/bootstrap.py`, which built the environment used for the lesson. This image itself has not yet been built or run on H100 or B200. Please report problems in the repository issues.
