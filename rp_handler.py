import runpod
import os
import json
import shutil
import urllib.request
import threading
import time
import comfy_utils
from urllib.parse import urlparse

# --- Global State for Job Handling (Single Worker Assumption) ---
JOBS = {}
# Structure: { job_id: { "status": "IN_QUEUE" | "IN_PROGRESS" | "COMPLETED" | "FAILED", "output": ... } }

# Paths based on Dockerfile
ROOT_DIR = "/runpod-volume"
MODELS_DIR_MAP = {
    "checkpoint": f"{ROOT_DIR}/models/checkpoints",
    "vae": f"{ROOT_DIR}/models/vae",
    "lora": f"{ROOT_DIR}/models/loras",
    "controlnet": f"{ROOT_DIR}/models/controlnet",
}

import requests

def download_file(url, target_dir, filename=None, api_key=None):
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)
    
    if not filename:
        filename = os.path.basename(urlparse(url).path)
        
    file_path = os.path.join(target_dir, filename)
    
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    try:
        print(f"Downloading {url} to {file_path}")
        with requests.get(url, headers=headers, stream=True) as r:
            r.raise_for_status()
            with open(file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"Download failed: {e}")
        return False

def process_workflow_thread(job_id, workflow_json):
    global JOBS
    try:
        JOBS[job_id]["status"] = "IN_PROGRESS"
        
        # 1. Connect WS
        ws = comfy_utils.connect_ws()
        
        # 2. Submit and Wait matches simple tracking
        prompt_id = comfy_utils.track_progress(workflow_json, ws)
        ws.close()
        
        # 3. Get History for Outputs
        history = comfy_utils.get_history(prompt_id)[prompt_id]
        outputs = history['outputs']
        
        final_images = []
        for node_id, node_output in outputs.items():
            if 'images' in node_output:
                for img in node_output['images']:
                    final_images.append(img)
        
        JOBS[job_id]["status"] = "COMPLETED"
        JOBS[job_id]["output"] = {"images": final_images}
        
    except Exception as e:
        print(f"Job {job_id} failed: {e}")
        JOBS[job_id]["status"] = "FAILED"
        JOBS[job_id]["error"] = str(e)


def handler(event):
    req = event.get('input', {})
    
    # If input is empty, maybe the event IS the input
    if not req and event:
        req = event
        
    route = req.get('route')
    method = req.get('method', 'GET')
    body = req.get('body', {})
    
    # Auto-route to /run if it looks like a ComfyUI workflow (has nodes)
    # or if route is missing but it's a POST
    if not route:
        if any(key.isdigit() for key in req.keys()): # ComfyUI JSON usually has numeric keys
            route = '/run'
            body = req
        elif method == 'POST':
            route = '/run'
            body = req
        else:
            route = '/catalog' # default to catalog for sanity check

    print(f"Received Request: {method} {route}")
    
    # --- 1. GET /catalog ---
    if route == '/catalog':
        info = comfy_utils.get_object_info()
        return info

    # --- 2. GET /models ---
    if route.startswith('/models') and method == 'GET':
        categories = ["checkpoints", "loras", "vae", "controlnet"]
        result = {}
        for cat in categories:
            path = f"{ROOT_DIR}/models/{cat}"
            if os.path.exists(path):
                result[cat] = os.listdir(path)
            else:
                result[cat] = []
        return result

    # --- 3. POST /models/download ---
    if route == '/models/download' and method == 'POST':
        url = body.get('url')
        m_type = body.get('type')
        filename = body.get('filename')
        api_key = body.get('api_key') or body.get('civitai_api_key')
        
        target_dir = MODELS_DIR_MAP.get(m_type)
        if not target_dir:
            return {"error": f"Invalid type: {m_type}"}
            
        success = download_file(url, target_dir, filename, api_key)
        if success:
            return {"status": "success", "file": filename}
        else:
            return {"status": "error", "message": "Download failed"}

    # --- 4. POST /run (Async start) ---
    if route == '/run' and method == 'POST':
        # body is the workflow json (the "prompt" object for /prompt endpoint)
        # Note: ComfyUI JSON often wraps in "prompt": {...} or is just the dict?
        # Requirement says "checkpoints": [..], "loras": [..]
        # BUT implies we construct the workflow?
        # OR implementation assumes body IS the ComfyUI workflow.
        # Let's assume body IS the workflow for maximum flexibility as per "Tech Scheme" 
        # which mentions "submit workflow JSON" in 8.3 /run example.
        
        # Wait, 8.3 Example for /run payload is:
        # { "checkpoints": [...], "loras": [...] } -> This implies CONSTRUCTING workflow.
        # BUT later it says "Output: ComfyUI API format workflow JSON".
        # I will support passing RAW workflow in body for now, as constructing dynamic workflows 
        # is complex and depends on specific custom nodes.
        # User likely sends a full workflow.
        
        workflow = body
        import uuid
        job_id = f"run-{uuid.uuid4()}"
        
        JOBS[job_id] = {"status": "IN_QUEUE"}
        
        # Run in thread so we can return ID immediately
        t = threading.Thread(target=process_workflow_thread, args=(job_id, workflow))
        t.start()
        
        return {"id": job_id, "status": "IN_QUEUE"}

    # --- 5. GET /result/{id} ---
    if route.startswith('/result/'):
        # extract ID
        # route usually is /result/run-xxx
        parts = route.split('/')
        job_id = parts[-1]
        
        job_data = JOBS.get(job_id)
        if job_data:
            return {"id": job_id, "status": job_data["status"], "output": job_data.get("output")}
        else:
            return {"error": "Job not found"}

    return {"error": "Route not found"}

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
