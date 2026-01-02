#!/bin/bash

echo "Setting up model paths..."
# Ensure the target directories exist on the persistent volume
mkdir -p /runpod-volume/models/checkpoints
mkdir -p /runpod-volume/models/loras
mkdir -p /runpod-volume/models/vae
mkdir -p /runpod-volume/models/controlnet
mkdir -p /runpod-volume/output

# Sync ComfyUI internal models folder to point to the persistent volume
# This ensures that even if the container is killed, models remain on the volume
for dir in checkpoints loras vae controlnet; do
    rm -rf /comfyui/models/$dir
    ln -s /runpod-volume/models/$dir /comfyui/models/$dir
done

# Link output directory as well
rm -rf /comfyui/output
ln -s /runpod-volume/output /comfyui/output

echo "Starting ComfyUI..."
# Start ComfyUI in background
python3 /comfyui/main.py --listen 127.0.0.1 --port 8188 &
COMFY_PID=$!

echo "Waiting for ComfyUI to be ready..."
# Simple wait loop
for i in {1..30}; do
    if curl -s http://127.0.0.1:8188/ > /dev/null; then
        echo "ComfyUI is ready!"
        break
    fi
    echo "Waiting for ComfyUI... ($i/30)"
    sleep 2
done

echo "Starting RunPod Handler..."
python3 -u /rp_handler.py
