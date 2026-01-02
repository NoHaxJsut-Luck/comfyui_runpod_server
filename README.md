# ComfyUI RunPod Serverless Worker (Android Backend)

This is a custom RunPod Serverless Worker designed to serve as a backend for an Android ComfyUI frontend. It supports on-demand model downloading, workflow execution, and catalog retrieval.

![Runpod Badge](https://api.runpod.io/badge/NoHaxJsut-Luck/comfyui_runpod_server)
*(Note: Replace `NoHaxJsut-Luck/comfyui_runpod_server` in the badge URL with your actual GitHub username/repo)*

## Features
- **Serverless API**: Custom routing for `/catalog`, `/models`, `/run`.
- **Model Management**: API to download checkpoints/LoRAs to persistent volume.
- **ComfyUI Integration**: Bridges serverless requests to a local ComfyUI instance.

## Deployment
This project is set up with GitHub Actions to automatically build and push the Docker image to Docker Hub.

1.  **Push to GitHub**: The action `Build and Push Docker Image` will run.
2.  **Deploy on RunPod**: Use the built image (e.g., `docker.io/youruser/comfyui-runpod-android:latest`) in a RunPod Serverless Template.

## Usage
Refer to `deployment.md` for detailed instructions.
