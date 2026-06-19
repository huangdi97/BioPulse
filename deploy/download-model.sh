#!/bin/bash
# 下载 Qwen2.5-7B-Instruct GGUF 模型
# 约 4.5GB，根据网络情况可能需要数分钟

set -e
MODEL_DIR="$(dirname "$0")/models"
mkdir -p "$MODEL_DIR"

MODEL_URL="https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_k_m.gguf"
MODEL_PATH="$MODEL_DIR/qwen2.5-7b-instruct-q4_k_m.gguf"

if [ -f "$MODEL_PATH" ]; then
    echo "模型已存在: $MODEL_PATH"
    ls -lh "$MODEL_PATH"
    exit 0
fi

echo "下载模型 (约 4.5GB)..."
echo "URL: $MODEL_URL"
wget -O "$MODEL_PATH" "$MODEL_URL"
echo "下载完成: $MODEL_PATH"
ls -lh "$MODEL_PATH"
