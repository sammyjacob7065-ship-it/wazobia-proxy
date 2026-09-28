# Render: set this service's Environment/Runtime to "Docker" (not "Python 3")
# so it picks this file up instead of trying to use requirements.txt directly.

FROM python:3.10-slim

# deepfilternet needs a Rust toolchain to build its extension at install time.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential git \
    && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /build

# Clone the model repo and run ITS OWN install script, staged the way the
# maintainers designed it (numpy/torch first, then the rest) - this avoids
# guessing at the exact pip order ourselves, which the model card explicitly
# warns will break if done as a flat "pip install -r requirements.txt".
RUN git clone https://github.com/Ememzyvisuals/wazobiavoice-TTS.git
WORKDIR /build/wazobiavoice-TTS

# The script itself also apt-get installs cargo/rustc directly, so the
# package index needs to be present again right before it runs.
RUN apt-get update && bash scripts/install.sh

# Now add the API server itself on top of that environment.
RUN pip install --no-cache-dir fastapi uvicorn python-multipart

WORKDIR /app
COPY main.py .

# If you're adding voice reference clips for the 13 personas, also:
# COPY voices/ voices/

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
