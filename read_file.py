import sys

file_path = r"e:\comfyui_runpod_android_server\Android 前端 + Runpod Serverless（ComfyUI 驱动）技术方案（个人闲用）.txt"

try:
    with open(file_path, 'r', encoding='gb18030') as f:
        print(f.read())
except Exception as e:
    print(f"Error reading with gb18030: {e}")
    try:
        with open(file_path, 'r', encoding='gb2312') as f:
            print(f.read())
    except Exception as e2:
        print(f"Error reading with gb2312: {e2}")
