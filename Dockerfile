FROM python:3.8.18-slim-bookworm

LABEL org.opencontainers.image.title="Wav2lip-Frozen"
LABEL org.opencontainers.image.description="Accurately Lip-syncing Videos In The Wild, now in Docker form!"
LABEL org.opencontainers.image.source="https://github.com/PhysCorp/Wav2Lip-Frozen"
LABEL org.opencontainers.image.licenses="Check repo"
LABEL org.opencontainers.image.version="2024.2.1.0"

# Copy project to /app
WORKDIR /app
COPY . /app

# # Setup output folders
# RUN mkdir -p /content
# RUN mkdir -p /content/input
# RUN mkdir -p /content/output

# Install dependencies
RUN apt-get update && \
    apt-get -y --no-install-recommends install \
    wget \
    nano \
    curl \
    ffmpeg \
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install dependencies
RUN pip install '/app/lib/ghc-1.0-py3-none-any.whl'
RUN pip install --no-cache-dir -r requirementsDOCKER.txt
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir --force-reinstall charset-normalizer

# Expose port for Flask
EXPOSE 5000

CMD ["python3", "web/flask_endpoint.py"]
