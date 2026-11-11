# syntax=docker/dockerfile:1.6
FROM python:3.11-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    CUDA_VISIBLE_DEVICES="" HF_HUB_OFFLINE=1 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
ARG PIP_PRIMARY_INDEX_URL=https://package-mirror.liara.ir/repository/pypi/simple
ARG PIP_FALLBACK_INDEX_URL=https://mirror2.chabokan.net/pypi/simple/
ARG TORCH_CPU_INDEX_URL=https://download.pytorch.org/whl/cpu
WORKDIR /srv
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg libgomp1 ca-certificates && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt /srv/requirements.txt
RUN pip install --index-url "$PIP_PRIMARY_INDEX_URL" --extra-index-url "$PIP_FALLBACK_INDEX_URL" -r requirements.txt
RUN pip install --index-url "$TORCH_CPU_INDEX_URL" torch==2.10.0+cpu torchvision==0.25.0+cpu torchaudio==2.10.0+cpu
RUN python -c "import torch,torchvision,torchaudio; assert torch.version.cuda is None"
COPY backend/app /srv/app
COPY backend/scripts /srv/scripts
COPY third_party/efficientat /srv/third_party/efficientat
RUN useradd --system --uid 10001 --home-dir /srv runner && mkdir /models
USER runner
EXPOSE 8000
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000","--workers","1","--no-access-log"]
