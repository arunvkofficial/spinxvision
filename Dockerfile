FROM rocm/dev-ubuntu-24.04:6.4.3

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.12 \
    python3.12-venv \
    python3-pip \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 9999 appuser

RUN mkdir -p /input /output /temp && \
    chown -R appuser:appuser /input /output /temp

WORKDIR /app

USER appuser

RUN python3.12 -m venv /home/appuser/venv && \
    /home/appuser/venv/bin/pip install --no-cache-dir --upgrade pip

RUN /home/appuser/venv/bin/pip install --no-cache-dir \
    torch==2.9.1+rocm6.4 \
    torchvision==0.24.1+rocm6.4 \
    --index-url https://download.pytorch.org/whl/rocm6.4

COPY requirements.txt .
RUN /home/appuser/venv/bin/pip install --no-cache-dir -r requirements.txt && \
    /home/appuser/venv/bin/pip cache purge

COPY . .

ENV PATH="/home/appuser/venv/bin:$PATH"

# Run as root to allow writing to mounted volumes
USER root

ENTRYPOINT ["/home/appuser/venv/bin/python", "/app/app.py"]
