FROM nvidia/cuda:12.1.1-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PATH="/usr/local/cuda/bin:${PATH}"

# 1. System Dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    python3-venv \
    git \
    wget \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && ln -s /usr/bin/python3.10 /usr/bin/python \
    && rm -rf /var/lib/apt/lists/*

# 2. Install PyTorch (matching CUDA 12.1)
# Split installation to avoid OOM on weak build runners
RUN pip install --upgrade pip
RUN pip install --no-cache-dir --default-timeout=100 torch==2.1.2 --index-url https://download.pytorch.org/whl/cu121
RUN pip install --no-cache-dir --default-timeout=100 torchvision==0.16.2 --index-url https://download.pytorch.org/whl/cu121
RUN pip install --no-cache-dir --default-timeout=100 torchaudio==2.1.2 --index-url https://download.pytorch.org/whl/cu121

# 3. Install ComfyUI
WORKDIR /
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /comfyui
WORKDIR /comfyui
RUN pip install -r requirements.txt

# 4. Install RunPod Handler dependencies
COPY requirements.txt /requirements_handler.txt
RUN pip install -r /requirements_handler.txt

# 5. Install ComfyUI Manager (Optional but good for extensions)
WORKDIR /comfyui/custom_nodes
RUN git clone https://github.com/ltdrdata/ComfyUI-Manager.git

# 6. Setup Worker files
COPY rp_handler.py /rp_handler.py
COPY comfy_utils.py /comfy_utils.py
COPY start.sh /start.sh
RUN chmod +x /start.sh

# 7. Create directories for mapping
RUN mkdir -p /runpod-volume/models/checkpoints \
    /runpod-volume/models/loras \
    /runpod-volume/models/vae \
    /runpod-volume/models/controlnet

# 8. Start
CMD ["/start.sh"]
