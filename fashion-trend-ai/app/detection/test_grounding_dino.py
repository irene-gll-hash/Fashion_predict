from __future__ import annotations

import json
from pathlib import Path

import torch
from PIL import Image, ImageDraw
from torchvision.ops import box_convert, nms

from groundingdino.util.inference import load_image, load_model, predict


PROJECT_ROOT = Path(__file__).resolve().parents[2]

CONFIG_PATH = (
    PROJECT_ROOT
    / "external"
    / "GroundingDINO"
    / "groundingdino"
    / "config"
    / "GroundingDINO_SwinT_OGC.py"
)

WEIGHTS_PATH = (
    PROJECT_ROOT
    / "external"
    / "GroundingDINO"
    / "weights"
    / "groundingdino_swint_ogc.pth"
)

IMAGE_PATH = PROJECT_ROOT / "test.jpg"

TEXT_PROMPT = "dress. top. jacket. jeans. pants. shoes. sandals. handbag. sunglasses. belt."

BOX_THRESHOLD = 0.30
TEXT_THRESHOLD = 0.25
NMS_IOU_THRESHOLD = 0.5


def apply_label_nms(
    boxes_xyxy: torch.Tensor,
    scores: torch.Tensor,
    labels: list[str],
    iou_threshold: float,
) -> list[int]:
    keep_indices = []

    for label in set(labels):
        label_indices = [i for i, item in enumerate(labels) if item == label]
        label_indices_tensor = torch.tensor(label_indices, dtype=torch.long)

        kept_local_indices = nms(
            boxes_xyxy[label_indices_tensor],
            scores[label_indices_tensor],
            iou_threshold,
        )

        kept_original_indices = label_indices_tensor[kept_local_indices].tolist()
        keep_indices.extend(kept_original_indices)

    return sorted(keep_indices, key=lambda i: float(scores[i]), reverse=True)


def main() -> None:
    device = "cuda" if torch.cuda.is_available() else "cpu"

    print(f"Device: {device}")
    print(f"Image: {IMAGE_PATH}")

    model = load_model(str(CONFIG_PATH), str(WEIGHTS_PATH), device=device)

    _, image = load_image(str(IMAGE_PATH))

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

    keep_indices = apply_label_nms(
        boxes_xyxy=boxes_xyxy,
        scores=logits,
        labels=phrases,
        iou_threshold=NMS_IOU_THRESHOLD,
    )

    boxes_xyxy = boxes_xyxy[keep_indices]
    logits = logits[keep_indices]
    phrases = [phrases[i] for i in keep_indices]

    print()
    print(f"Detections after NMS: {len(phrases)}")

    for phrase, score, box in zip(phrases, logits.tolist(), boxes_xyxy.tolist()):
        rounded_box = [round(value, 2) for value in box]
        print(f"{phrase}: {score:.3f} box={rounded_box}")

    result_image_path = PROJECT_ROOT / "test_grounding_dino_result.jpg"
    detections_path = PROJECT_ROOT / "test_grounding_dino_detections.json"

    detections = []

    with Image.open(IMAGE_PATH).convert("RGB") as img:
        draw = ImageDraw.Draw(img)

        for phrase, score, box in zip(phrases, logits.tolist(), boxes_xyxy.tolist()):
            x1, y1, x2, y2 = box

            draw.rectangle((x1, y1, x2, y2), outline="red", width=3)
            draw.text((x1, max(0, y1 - 18)), f"{phrase} {score:.2f}", fill="red")

            detections.append(
                {
                    "label": phrase,
                    "score": round(float(score), 4),
                    "box_xyxy": [round(float(value), 2) for value in box],
                }
            )

        img.save(result_image_path)

    with detections_path.open("w", encoding="utf-8") as f:
        json.dump(detections, f, ensure_ascii=False, indent=2)

    print(f"\nSaved result image: {result_image_path}")
    print(f"Saved detections: {detections_path}")


if __name__ == "__main__":
    main()