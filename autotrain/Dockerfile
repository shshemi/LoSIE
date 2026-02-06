FROM nvidia/cuda:12.8.1-cudnn-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/output/hf

ENV TORCH_VERSION=2.9.1 \
    TORCHVISION_VERSION=0.24.1 \
    TORCHAUDIO_VERSION=2.9.1 \
    TORCH_INDEX_URL=https://download.pytorch.org/whl/cu128

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        software-properties-common \
        ca-certificates \
        curl \
        git \
        build-essential; \
    add-apt-repository -y ppa:deadsnakes/ppa; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        python3.11 \
        python3.11-venv \
        python3.11-distutils; \
    curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11; \
    python3.11 -m pip install --no-cache-dir --upgrade pip; \
    python3.11 -m pip install --no-cache-dir \
        torch==${TORCH_VERSION} \
        torchvision==${TORCHVISION_VERSION} \
        torchaudio==${TORCHAUDIO_VERSION} \
        --index-url ${TORCH_INDEX_URL}; \
    printf "torch==%s\ntorchvision==%s\ntorchaudio==%s\n" \
        "${TORCH_VERSION}" "${TORCHVISION_VERSION}" "${TORCHAUDIO_VERSION}" \
        > /tmp/pip-constraints.txt; \
    python3.11 -m pip install --no-cache-dir -c /tmp/pip-constraints.txt autotrain-advanced; \
    apt-get purge -y --auto-remove build-essential software-properties-common; \
    rm -rf /var/lib/apt/lists/* /root/.cache/pip /tmp/pip-constraints.txt

RUN mkdir -p /workspace /output/hf /data
COPY output/splits/ /data/
COPY autotrain/ /workspace/

WORKDIR /output
CMD ["autotrain", "--config", "/workspace/seq_2_seq_config.yaml"]
