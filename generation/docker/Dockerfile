# Container image for regenerating the lesson's candidates on NVIDIA H100 (Hopper) or B200 (Blackwell) GPUs.
#
# Build from the repository root:
#   docker build -f generation/docker/Dockerfile -t cut-cosmos:cu130 .
#
# Contents:
#   - Ray 2.60 on Python 3.13 with CUDA 13 (base image), so one image covers Hopper and Blackwell.
#   - NVIDIA Cosmos Transfer 2.5 source at the revision the lesson recorded (2ff49d0), in /opt/cosmos-transfer2.5.
#   - The Cosmos Python environment, built with the same steps as generation/cosmos_ray/bootstrap.py,
#     in /opt/cosmos-venvs/cu130-py313. It lives in the image, so no node rebuilds it at run time.
#   - The cosmos_ray wrapper from this repository in /home/ray/cut-ai-edu/generation.
#
# Excluded:
#   - Model weights and Hugging Face credentials. Mount a model cache at run time and pass the token as an
#     environment variable after accepting the model terms on Hugging Face.
#
# Host requirement: NVIDIA driver 580 or newer (CUDA 13) and the NVIDIA Container Toolkit.

ARG BASE_IMAGE=anyscale/ray:2.60.0-py313-cu130
FROM ${BASE_IMAGE}

USER root
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg git git-lfs rsync curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.8.12 /uv /uvx /usr/local/bin/
ENV UV_LINK_MODE=copy \
    UV_PYTHON_INSTALL_DIR=/opt/uv-python

# Cosmos Transfer 2.5 source. The revision is the one recorded for the lesson run; it already includes the
# upstream Blackwell video-encoder fix. Large test assets are git-lfs files and are not needed, so they are skipped.
ARG COSMOS_REPO=https://github.com/nvidia-cosmos/cosmos-transfer2.5
ARG COSMOS_REF=2ff49d0717af02057ae79bc75c00fbff9da1b4e7
ENV COSMOS_SRC=/opt/cosmos-transfer2.5 \
    COSMOS_VENV=/opt/cosmos-venvs/cu130-py313 \
    GIT_LFS_SKIP_SMUDGE=1
RUN git clone --filter=blob:none --no-checkout "${COSMOS_REPO}" "${COSMOS_SRC}" \
 && git -C "${COSMOS_SRC}" checkout --quiet "${COSMOS_REF}" \
 && rm -rf "${COSMOS_SRC}/.git" "${COSMOS_SRC}/assets/tests"

# Cosmos environment, same steps and pins as generation/cosmos_ray/bootstrap.py:
#   uv sync with the cu130 extra, Ray at the driver's version, cuDNN 9.21.1.3 (a mixed cuDNN pair crashes at
#   model init), and decord 0.6.0 from PyPI (the Cosmos index build links an ffmpeg library that is often absent).
ARG CUDA_EXTRA=cu130
ARG CUDNN_VERSION=9.21.1.3
ARG DECORD_VERSION=0.6.0
RUN cd "${COSMOS_SRC}" \
 && uv python install 3.13 \
 && uv venv --python 3.13 "${COSMOS_VENV}" \
 && VIRTUAL_ENV="${COSMOS_VENV}" uv sync --extra="${CUDA_EXTRA}" --python "${COSMOS_VENV}/bin/python" --active --inexact \
 && RAY_VERSION="$(python -c 'import ray; print(ray.__version__)')" \
 && VIRTUAL_ENV="${COSMOS_VENV}" uv pip install --python "${COSMOS_VENV}/bin/python" "ray==${RAY_VERSION}" \
 && VIRTUAL_ENV="${COSMOS_VENV}" uv pip install --python "${COSMOS_VENV}/bin/python" "nvidia-cudnn-cu13==${CUDNN_VERSION}" \
 && VIRTUAL_ENV="${COSMOS_VENV}" uv pip install --python "${COSMOS_VENV}/bin/python" \
      --reinstall-package decord --index-url https://pypi.org/simple "decord==${DECORD_VERSION}" \
 && rm -rf /root/.cache/uv

# Build-time checks that do not need a GPU. CUDA availability is checked at run time (see generation/docker/README.md).
RUN "${COSMOS_VENV}/bin/python" -c "import cosmos_transfer2, decord, ray, torch, importlib.metadata as m; print('cosmos ok | torch', torch.__version__, '| ray', ray.__version__, '| cudnn', m.version('nvidia-cudnn-cu13'))"

# This repository's wrapper. The run command copies cosmos_ray into the Cosmos source tree, so that tree must be
# writable by the container user.
COPY --chown=1000:100 generation /home/ray/cut-ai-edu/generation
RUN chown -R 1000:100 "${COSMOS_SRC}" "${COSMOS_VENV}" \
 && mkdir -p /mnt/cluster_storage /mnt/user_storage /mnt/local_storage \
 && chown 1000:100 /mnt/cluster_storage /mnt/user_storage /mnt/local_storage

USER ray
WORKDIR /home/ray/cut-ai-edu
ENV PYTHONPATH=/home/ray/cut-ai-edu/generation \
    HF_HOME=/mnt/cluster_storage/hf
