import websocket
import uuid
import json
import urllib.request
import urllib.parse
import time
import os
import re

SERVER_ADDRESS = "127.0.0.1:8188"
COMFY_INPUT_DIR = os.environ.get("COMFY_INPUT_DIR", "/comfyui/input")
MAX_INPUT_IMAGE_BYTES = int(os.environ.get("MAX_INPUT_IMAGE_BYTES", str(15 * 1024 * 1024)))
CLIENT_ID = str(uuid.uuid4())

def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": CLIENT_ID}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request("http://{}/prompt".format(SERVER_ADDRESS), data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_image(filename, subfolder, folder_type):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen("http://{}/view?{}".format(SERVER_ADDRESS, url_values)) as response:
        return response.read()

def get_history(prompt_id):
    with urllib.request.urlopen("http://{}/history/{}".format(SERVER_ADDRESS, prompt_id)) as response:
        return json.loads(response.read())

def get_object_info():
    with urllib.request.urlopen("http://{}/object_info".format(SERVER_ADDRESS)) as response:
        return json.loads(response.read())

def check_server_ready():
    try:
        with urllib.request.urlopen("http://{}".format(SERVER_ADDRESS), timeout=1) as response:
            return response.status == 200
    except:
        return False

# Simple wrapper to track execution for a specific prompt_id
def track_progress(prompt, ws):
    prompt_id = queue_prompt(prompt)['prompt_id']
    print(f"Prompt ID: {prompt_id} queued")
    
    # Wait for completion via WebSocket
    # Note: In a real async handler, we'd want non-blocking WS, 
    # but for simplicity in this thread:
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    print(f"Prompt {prompt_id} completed")
                    break
        else:
            continue
            
    return prompt_id

def connect_ws():
    ws = websocket.WebSocket()
    ws.connect("ws://{}/ws?clientId={}".format(SERVER_ADDRESS, CLIENT_ID))
    return ws


def _validate_image_magic(data: bytes) -> None:
    if len(data) < 12:
        raise ValueError("Image too small or empty")
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return
    if data[:3] == b"\xff\xd8\xff":
        return
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return
    raise ValueError("Unsupported image type (use PNG, JPEG, or WebP)")


def write_input_image(filename_hint: str, raw_bytes: bytes) -> str:
    """
    Save bytes to ComfyUI input folder; return basename for LoadImage.
    """
    if not raw_bytes:
        raise ValueError("Empty image data")
    if len(raw_bytes) > MAX_INPUT_IMAGE_BYTES:
        raise ValueError(f"Image exceeds max size ({MAX_INPUT_IMAGE_BYTES // (1024 * 1024)} MB)")
    _validate_image_magic(raw_bytes)
    os.makedirs(COMFY_INPUT_DIR, exist_ok=True)
    base = os.path.basename(filename_hint or "upload.png") or "upload.png"
    base = re.sub(r"[^a-zA-Z0-9._-]", "_", base)
    if not base.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
        base = base + ".png"
    final_name = f"rp_{uuid.uuid4().hex[:12]}_{base}"
    path = os.path.join(COMFY_INPUT_DIR, final_name)
    with open(path, "wb") as f:
        f.write(raw_bytes)
    return final_name
