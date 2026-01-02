#!/bin/bash

echo "Starting ComfyUI..."
# Start ComfyUI in background
# --listen to 127.0.0.1 is sufficient since we proxy via handler, 
# but binding to 0.0.0.0 is useful for debugging if port is exposed.
python3 /comfyui/main.py --listen 127.0.0.1 --port 8188 &
COMFY_PID=$!

echo "Waiting for ComfyUI to be ready..."
# Simple wait loop to ensure ComfyUI is up before handler starts
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
