# syntax=docker/dockerfile:1.6
FROM docker.arvancloud.ir/python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    CUDA_VISIBLE_DEVICES="" HF_HUB_OFFLINE=1 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
    XDG_CACHE_HOME=/tmp/.cache TORCH_HOME=/tmp/.torch-cache

ARG PIP_PRIMARY_INDEX_URL=https://package-mirror.liara.ir/repository/pypi/simple
ARG PIP_FALLBACK_INDEX_URL=https://mirror2.chabokan.net/pypi/simple/
ARG TORCH_CPU_INDEX_URL=https://download.pytorch.org/whl/cpu
ARG APT_PRIMARY_DEBIAN_URL=https://mirror.metanet.ch/debian
ARG APT_PRIMARY_SECURITY_URL=https://mirror.metanet.ch/debian-security
ARG APT_FALLBACK_DEBIAN_URL=https://mirrors.huaweicloud.com/repository/debian
ARG APT_FALLBACK_SECURITY_URL=https://mirrors.huaweicloud.com/repository/debian-security

WORKDIR /srv
COPY ops/install-debian-packages.sh /usr/local/bin/install-debian-packages
RUN chmod 0555 /usr/local/bin/install-debian-packages && \
    /usr/local/bin/install-debian-packages ffmpeg libgomp1 ca-certificates

COPY backend/requirements.txt /tmp/requirements.txt
COPY backend/requirements-torch-deps.txt /tmp/requirements-torch-deps.txt

# Use an explicit primary/fallback, not --extra-index-url for untrusted dependency resolution.
RUN --mount=type=cache,target=/root/.cache/pip \
    (python -m pip install --timeout 60 --retries 3 --index-url "$PIP_PRIMARY_INDEX_URL" \
       -r /tmp/requirements.txt -r /tmp/requirements-torch-deps.txt \
      || python -m pip install --timeout 60 --retries 3 --index-url "$PIP_FALLBACK_INDEX_URL" \
       -r /tmp/requirements.txt -r /tmp/requirements-torch-deps.txt)

# Explicit CPU-only wheel family, no accidental CUDA wheels or resolver mixing.
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --no-deps --timeout 120 --retries 3 --index-url "$TORCH_CPU_INDEX_URL" \
      'torch==2.10.0+cpu' 'torchvision==0.25.0+cpu' 'torchaudio==2.10.0+cpu' \
    && python -m pip check \
    && python -c "import torch,torchvision,torchaudio; assert torch.version.cuda is None; assert torch.__version__.startswith('2.10.0+cpu'); assert torchvision.__version__.startswith('0.25.0+cpu'); assert torchaudio.__version__.startswith('2.10.0+cpu')"

COPY backend/app /srv/app
COPY backend/scripts /srv/scripts
COPY third_party/efficientat /srv/third_party/efficientat

RUN useradd --system --uid 10001 --home-dir /srv runner && mkdir -p /models
USER runner
EXPOSE 8000
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000","--workers","1","--no-access-log"]
