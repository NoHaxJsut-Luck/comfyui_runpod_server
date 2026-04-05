# ComfyUI RunPod Worker API Specification (IDL)

This document defines the API interface for the ComfyUI Serverless Worker running on RunPod.

**Base URL**: `https://api.runpod.ai/v2/{YOUR_ENDPOINT_ID}`  
**Authentication**: Headers must include `Authorization: Bearer <YOUR_RUNPOD_API_KEY>`

---

## 🚀 1. Image Generation (Synchronous)
Submit a ComfyUI workflow and receive images encoded in Base64. This route is smart-routed; you can send a raw ComfyUI JSON or wrap it.

- **Endpoint**: `/run` (Internal route)
- **Method**: `POST`
- **Request Body Options**:
  - **Option A (Raw ComfyUI API JSON)**: Directly send the JSON exported from ComfyUI (API format).
  - **Option B (Wrapped)**: `{"input": { ...workflow... }}`

- **Successful Response**:
```json
{
  "id": "job-uuid",
  "status": "COMPLETED",
  "output": {
    "id": "run-uuid",
    "status": "COMPLETED",
    "output": {
      "images": [
        {
          "filename": "result_00001_.png",
          "subfolder": "",
          "type": "output",
          "base64": "iVBORw0KGgoAAAANSUh..."
        }
      ]
    }
  }
}
```

---

## 🖼️ 1b. Register input image (for img2img / LoadImage)

Upload a reference image to the worker so ComfyUI `LoadImage` can load it by filename. Use **before** submitting a workflow that references this name in `LoadImage.inputs.image`.

- **Endpoint**: `/input/image` (Internal route)
- **Method**: `POST`
- **Request** (RunPod envelope):

```json
{
  "input": {
    "route": "/input/image",
    "method": "POST",
    "body": {
      "filename": "user-ref.png",
      "image_base64": "<raw base64, no data: URI prefix>",
      "content_type": "image/png"
    }
  }
}
```

- **Successful response** (worker body; may be nested under `output` per RunPod):

```json
{
  "name": "user-ref.png",
  "subfolder": "",
  "type": "input"
}
```

Use **`name`** as `LoadImage.inputs.image` in the ComfyUI workflow JSON.

- **Errors**: `image_base64` missing/invalid, unsupported type, or decoded size over server limit — response includes a readable `error` or `message` field.

---

## 📂 2. Model Management

### List Models
Fetch current files available in the persistent volume.
- **Endpoint**: `/models`
- **Method**: `GET`
- **Response**:
```json
{
  "output": {
    "checkpoints": ["juggernaut_xl.safetensors"],
    "loras": [],
    "vae": [],
    "controlnet": []
  }
}
```

### Download Model
Download a model from a URL (e.g., Civitai) directly to the persistent volume.
- **Endpoint**: `/models/download`
- **Method**: `POST`
- **Request Body**:
```json
{
  "input": {
    "route": "/models/download",
    "method": "POST",
    "body": {
      "url": "https://civitai.com/api/download/models/...",
      "type": "checkpoint",
      "filename": "model_name.safetensors",
      "civitai_api_key": "YOUR_API_KEY"
    }
  }
}
```

---

## 🛠️ 3. System Inspection

### Catalog (Object Info)
Get descriptions of all loaded ComfyUI nodes.
- **Endpoint**: `/catalog`
- **Method**: `GET`

---

## 📱 Android Implementation Tips

### 1. Retrofit Interface
```kotlin
interface RunPodService {
    @POST("run")
    suspend fun generateImage(@Body request: Map<String, Any>): Response<RunPodResponse>
}
```

### 2. Base64 Decoding
```kotlin
fun decodeBase64ToBitmap(base64Str: String): Bitmap {
    val decodedBytes = Base64.decode(base64Str, Base64.DEFAULT)
    return BitmapFactory.decodeByteArray(decodedBytes, 0, decodedBytes.size)
}
```

### 3. Timeout Settings
Since generation takes time, ensure your HTTP client has a long timeout:
- `connectTimeout`: 30s
- `readTimeout`: 300s
