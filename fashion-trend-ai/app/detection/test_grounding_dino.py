from __future__ import annotations

from pathlib import Path

import torch
from torchvision.ops import box_convert
from PIL import Image

from groundingdino.util.inference import load_model, load_image, predict


PROJECT_ROOT = Path(__file__).resolve().parents[2]

CONFIG_PATH = PROJECT_ROOT / "external" / "GroundingDINO" / "groundingdino" / "config" / "GroundingDINO_SwinT_OGC.py"
WEIGHTS_PATH = PROJECT_ROOT / "external" / "GroundingDINO" / "weights" / "groundingdino_swint_ogc.pth"
IMAGE_PATH = PROJECT_ROOT / "test.jpg"

TEXT_PROMPT = "dress. top. jacket. jeans. pants. shoes. sandals. handbag. sunglasses. belt."

BOX_THRESHOLD = 0.30
TEXT_THRESHOLD = 0.25


def main() -> None:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")
    print(f"Image: {IMAGE_PATH}")
    model = load_model(str(CONFIG_PATH), str(WEIGHTS_PATH), device=device)
    image_source, image = load_image(str(IMAGE_PATH))
    boxes, logits, phrases = predict(
        model=model,
        image=image,
        caption=TEXT_PROMPT,
        box_threshold=BOX_THRESHOLD,
        text_threshold=TEXT_THRESHOLD,
        device=device,
    )
    with Image.open(IMAGE_PATH) as img:
        width, height = img.size
    boxes_xyxy = box_convert(boxes=boxes, in_fmt="cxcywh", out_fmt="xyxy")
    boxes_xyxy = boxes_xyxy * torch.tensor([width, height, width, height])
    print()
    print(f"Detections: {len(phrases)}")
    for phrase, score, box in zip(phrases, logits.tolist(), boxes_xyxy.tolist()):
        box = [round(value, 2) for value in box]
        print(f"{phrase}: {score:.3f} box={box}")


if __name__ == "__main__":
    main()