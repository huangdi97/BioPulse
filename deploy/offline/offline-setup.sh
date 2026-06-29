#!/usr/bin/env bash
# ==============================================================
# BioPulse OneCloudFourEnds — Offline Setup Script
# One-time provisioning for air-gapped / offline environments.
# Run once on the target machine before docker compose up.
# ==============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# ---------------------------------------------------------------
# Config
# ---------------------------------------------------------------
MODEL_DIR="${MODEL_DIR:-$SCRIPT_DIR/models}"
DATA_DIR="${DATA_DIR:-$PROJECT_DIR/data}"
CONFIG_DIR="${CONFIG_DIR:-$SCRIPT_DIR/config}"

MODEL_URL="${MODEL_URL:-https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_k_m.gguf}"
MODEL_FILE="qwen2.5-7b-instruct-q4_k_m.gguf"
EXPECTED_CHECKSUM=""

# ---------------------------------------------------------------
# Colors
# ---------------------------------------------------------------
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }

# ---------------------------------------------------------------
# Pre-flight checks
# ---------------------------------------------------------------
preflight_check() {
    info "Running pre-flight checks..."

    command -v docker >/dev/null 2>&1 || { error "Docker is not installed."; exit 1; }
    command -v wget    >/dev/null 2>&1 || { error "wget is required."; exit 1; }
    command -v sha256sum >/dev/null 2>&1 || { error "sha256sum is required."; exit 1; }

    DOCKER_VERSION=$(docker --version | grep -oP '\d+\.\d+\.\d+' | head -1)
    info "Docker version: $DOCKER_VERSION"

    if ! docker compose version >/dev/null 2>&1; then
        error "Docker Compose plugin (v2) is required."
        exit 1
    fi

    # Check disk space (need at least 20 GB free for model + images + data)
    AVAILABLE_KB=$(df "$SCRIPT_DIR" | awk 'NR==2 {print $4}')
    AVAILABLE_GB=$((AVAILABLE_KB / 1024 / 1024))
    if [ "$AVAILABLE_GB" -lt 20 ]; then
        error "Insufficient disk space: ${AVAILABLE_GB}GB available, need >= 20GB."
        exit 1
    fi
    info "Disk space: ${AVAILABLE_GB}GB available — OK"

    info "Pre-flight checks passed."
}

# ---------------------------------------------------------------
# Create directories
# ---------------------------------------------------------------
create_directories() {
    info "Creating required directories..."
    mkdir -p "$MODEL_DIR" "$DATA_DIR" "$CONFIG_DIR"
    info "  MODEL_DIR  = $MODEL_DIR"
    info "  DATA_DIR   = $DATA_DIR"
    info "  CONFIG_DIR = $CONFIG_DIR"
}

# ---------------------------------------------------------------
# Download LLM model
# ---------------------------------------------------------------
download_model() {
    local model_path="$MODEL_DIR/$MODEL_FILE"

    if [ -f "$model_path" ]; then
        local size
        size=$(ls -lh "$model_path" | awk '{print $5}')
        info "Model already exists: $model_path (${size})"
        info "  If you need to re-download, delete it first: rm $model_path"
        return 0
    fi

    info "Downloading LLM model (~4.5 GB) from Hugging Face..."
    info "  URL: $MODEL_URL"
    echo

    wget -O "$model_path" "$MODEL_URL" --progress=bar:force 2>&1

    echo
    info "Download complete."

    # Verify file is valid GGUF
    if ! head -c 4 "$model_path" | grep -q "GGUF"; then
        error "Downloaded file does not appear to be a valid GGUF model."
        error "  Expected magic bytes 'GGUF' at start of file."
        rm -f "$model_path"
        exit 1
    fi

    local final_size
    final_size=$(ls -lh "$model_path" | awk '{print $5}')
    info "Model verified: $model_path (${final_size})"

    # Optional checksum verification
    if [ -n "$EXPECTED_CHECKSUM" ]; then
        info "Verifying SHA-256 checksum..."
        local actual
        actual=$(sha256sum "$model_path" | awk '{print $1}')
        if [ "$actual" != "$EXPECTED_CHECKSUM" ]; then
            error "Checksum mismatch!"
            error "  Expected: $EXPECTED_CHECKSUM"
            error "  Actual:   $actual"
            exit 1
        fi
        info "Checksum verified."
    fi
}

# ---------------------------------------------------------------
# Copy default config
# ---------------------------------------------------------------
setup_config() {
    if [ -f "$PROJECT_DIR/.env" ]; then
        info ".env file already exists — skipping."
    else
        if [ -f "$PROJECT_DIR/.env.example" ]; then
            cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
            info "Created .env from .env.example"
        else
            warn ".env.example not found at $PROJECT_DIR/.env.example"
            warn "Create .env manually with required environment variables."
        fi
    fi
}

# ---------------------------------------------------------------
# Load Docker images from local archive (optional)
# ---------------------------------------------------------------
load_offline_images() {
    local image_archive="$SCRIPT_DIR/images.tar.gz"
    if [ -f "$image_archive" ]; then
        info "Loading Docker images from $image_archive..."
        gunzip -c "$image_archive" | docker load
        info "Images loaded."
    else
        info "No offline image archive found at $image_archive."
        info "  Images will be pulled or built on first docker compose up."
    fi
}

# ---------------------------------------------------------------
# Build application images
# ---------------------------------------------------------------
build_images() {
    info "Building application images..."
    docker compose -f "$SCRIPT_DIR/docker-compose.offline.yml" build --parallel
    info "Build complete."
}

# ---------------------------------------------------------------
# Summary
# ---------------------------------------------------------------
print_summary() {
    local total_gb=0
    if [ -f "$MODEL_DIR/$MODEL_FILE" ]; then
        total_gb=$(du -sh "$MODEL_DIR/$MODEL_FILE" | awk '{print $1}')
    fi

    echo
    echo "========================================================"
    echo "  BioPulse Offline Setup — Complete"
    echo "========================================================"
    echo "  Model:        $MODEL_DIR/$MODEL_FILE (${total_gb})"
    echo "  Data:         $DATA_DIR"
    echo "  Config:       $CONFIG_DIR"
    echo ""
    echo "  To start the system:"
    echo "    docker compose -f $SCRIPT_DIR/docker-compose.offline.yml up -d"
    echo ""
    echo "  To stop:"
    echo "    docker compose -f $SCRIPT_DIR/docker-compose.offline.yml down"
    echo ""
    echo "  Access the API at: http://<host-ip>:8000"
    echo "========================================================"
}

# ---------------------------------------------------------------
# Main
# ---------------------------------------------------------------
main() {
    echo
    echo "========================================================"
    echo "  BioPulse OneCloudFourEnds — Offline Setup"
    echo "========================================================"
    echo

    preflight_check
    create_directories
    download_model
    setup_config
    load_offline_images
    build_images
    print_summary
}

main "$@"
