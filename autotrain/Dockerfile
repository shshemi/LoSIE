FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    ca-certificates \
    curl \
    git \
    build-essential \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y --no-install-recommends \
        python3.11 \
        python3.11-venv \
        python3.11-distutils \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11
RUN python3.11 -m pip install --no-cache-dir --upgrade pip

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/workspace/output/training/hf \
    TRANSFORMERS_CACHE=/workspace/output/training/hf/transformers \
    HF_DATASETS_CACHE=/workspace/output/training/hf/datasets

RUN python3.11 -m pip install --no-cache-dir \
    torch --index-url https://download.pytorch.org/whl/cu121
RUN python3.11 -m pip install --no-cache-dir autotrain-advanced

RUN mkdir -p /workspace/autotrain /workspace/output/training
COPY autotrain/ /workspace/autotrain/

WORKDIR /workspace/output/training
CMD ["autotrain", "--config", "/workspace/autotrain/seq_2_seq_config.yaml"]
