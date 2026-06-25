from fastapi import FastAPI
from pydantic import BaseModel
import base64
import numpy as np
import cv2
import torch
import os
import uvicorn
from app.gpu_service.dino import load_model, detect_image
from app.taxonomy.fashion_taxonomy import FashionTaxonomy

app = FastAPI()

model = None
taxonomy = None
text_prompt = None
device = "cuda" if torch.cuda.is_available() else "cpu"


class Request(BaseModel):
    image: str  # base64


def init_model():
    global model, taxonomy, text_prompt

    model = load_model(device=device)
    model.eval()

    taxonomy = FashionTaxonomy.load()
    text_prompt = taxonomy.get_dino_prompt()


@app.on_event("startup")
def startup():
    init_model()


@app.post("/detect")
def detect(req: Request):
    img_bytes = base64.b64decode(req.image)
    np_arr = np.frombuffer(img_bytes, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

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