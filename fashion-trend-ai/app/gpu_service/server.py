from fastapi import FastAPI
from pydantic import BaseModel
import base64
import io
import os
from threading import Lock
import torch
import uvicorn
from PIL import Image
import groundingdino.datasets.transforms as T
from app.gpu_service.dino import load_model, detect_image
from app.taxonomy.fashion_taxonomy import FashionTaxonomy
app = FastAPI()

model = None
taxonomy = None
text_prompt = None
model_lock = Lock()
device = "cuda" if torch.cuda.is_available() else "cpu"
transform = T.Compose(
    [
        T.RandomResize([800], max_size=1333),
        T.ToTensor(),
        T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ]
)


class Request(BaseModel):
    image: str

@app.get("/health")
def health():
    return {
        "status": "ok",
        "cuda_available": torch.cuda.is_available(),
        "device": device,
    }

def ensure_model_loaded():
    global model, taxonomy, text_prompt
    if model is not None:
        return
    with model_lock:
        if model is not None:
            return
        print(f"torch cuda available: {torch.cuda.is_available()}")
        print(f"device: {device}")
        if torch.cuda.is_available():
            print(f"gpu name: {torch.cuda.get_device_name(0)}")
        model = load_model(device=device)
        model.eval()
        taxonomy = FashionTaxonomy.load()
        text_prompt = taxonomy.get_dino_prompt()
        print("GroundingDINO model loaded")

def decode_image(image_base64: str) -> torch.Tensor:
    img_bytes = base64.b64decode(image_base64)
    image_pil = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    image_tensor, _ = transform(image_pil, None)
    return image_tensor

@app.post("/detect")
def detect(req: Request):
    ensure_model_loaded()
    image = decode_image(req.image)
    result = detect_image(
        model=model,
        image=image,
        device=device,
        text_prompt=text_prompt,
        box_threshold=0.35,
        text_threshold=0.25,
        nms_iou_threshold=0.5,
    )
    return result

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)