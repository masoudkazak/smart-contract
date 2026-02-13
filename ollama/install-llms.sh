#!/bin/bash
set -e

BASE_DIR="models"
mkdir -p "$BASE_DIR"

echo "Starting model downloads ..."

echo "Downloading paraphrase-multilingual-MiniLM-L12-v2 ..."
mkdir -p "$BASE_DIR/paraphrase-multilingual-MiniLM-L12-v2"
cd "$BASE_DIR/paraphrase-multilingual-MiniLM-L12-v2"

wget -c "https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2/resolve/main/pytorch_model.bin"
wget -c "https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2/resolve/main/config.json"
wget -c "https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2/resolve/main/tokenizer.json"
wget -c "https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2/resolve/main/tokenizer_config.json"

echo "Finished downloading paraphrase-multilingual-MiniLM-L12-v2"
cd - >/dev/null


echo "Downloading Qwen3-0.6B-GGUF (quantized version)..."
mkdir -p "$BASE_DIR/Qwen3-0.6B-GGUF"
cd "$BASE_DIR/Qwen3-0.6B-GGUF"

wget -c "https://huggingface.co/MaziyarPanahi/Qwen3-0.6B-GGUF/resolve/main/Qwen3-0.6B.Q4_K_M.gguf"

# Optionally, you can use Q3_K_M or Q2_K versions instead:
# wget -c "https://huggingface.co/MaziyarPanahi/Qwen3-0.6B-GGUF/resolve/main/Qwen3-0.6B.Q2_K.gguf"
# wget -c "https://huggingface.co/MaziyarPanahi/Qwen3-0.6B-GGUF/resolve/main/Qwen3-0.6B.Q3_K_M.gguf"

echo "Finished downloading Qwen3-0.6B-GGUF"
cd - >/dev/null

echo "All models have been successfully downloaded 🎉"
