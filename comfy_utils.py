import websocket
import uuid
import json
import urllib.request
import urllib.parse
import time
import os

SERVER_ADDRESS = "127.0.0.1:8188"
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
