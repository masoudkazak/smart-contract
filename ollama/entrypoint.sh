#!/usr/bin/env bash
set -e

MODEL_NAME="qwen3-0.6b"
MODEL_PATH="/models/Qwen3-0.6B-GGUF/Qwen3-0.6B.Q4_K_M.gguf"
MODELFILE="/tmp/Modelfile"

echo "Starting Ollama..."

ollama serve &
OLLAMA_PID=$!

echo "Waiting for Ollama to be ready..."
for i in $(seq 1 30); do
    if ollama list > /dev/null 2>&1; then
        echo "Ollama is ready!"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "ERROR: Ollama failed to start after 30 attempts"
        exit 1
    fi
    sleep 2
done

if ! ollama list | awk '{print $1}' | grep -qx "$MODEL_NAME"; then
    echo "Model $MODEL_NAME not found. Creating..."
    
    if [ ! -f "$MODEL_PATH" ]; then
        echo "ERROR: Model file not found: $MODEL_PATH"
        exit 1
    fi
    
    cat > "$MODELFILE" << 'EOF'
FROM /models/Qwen3-0.6B-GGUF/Qwen3-0.6B.Q4_K_M.gguf

TEMPLATE """{{ if .System }}### System:
{{ .System }}

{{ end }}### User:
{{ .Prompt }}

### Assistant:
"""

PARAMETER repeat_penalty 1.2
PARAMETER num_ctx 2048

PARAMETER stop "### User:"
PARAMETER stop "\n### User:"
PARAMETER stop "###"

SYSTEM """You are a helpful AI assistant. Answer questions clearly and concisely in a natural conversational style."""
EOF

    echo "Creating model with Modelfile..."
    ollama create "$MODEL_NAME" -f "$MODELFILE"
    
    if [ $? -eq 0 ]; then
        echo "Model created successfully!"
    else
        echo "ERROR: Failed to create model"
        exit 1
    fi
else
    echo "Model $MODEL_NAME already exists."
fi

echo "Available models:"
ollama list

echo "Ollama setup complete. Keeping service running..."
wait $OLLAMA_PID
