from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
from PIL import Image
from torchvision.ops import box_convert, nms
from groundingdino.util.inference import load_image, load_model, predict

from app.taxonomy.fashion_taxonomy import FashionTaxonomy

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "external" / "GroundingDINO" / "groundingdino" / "config" / "GroundingDINO_SwinT_OGC.py"
WEIGHTS_PATH = PROJECT_ROOT / "external" / "GroundingDINO" / "weights" / "groundingdino_swint_ogc.pth"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

def apply_label_nms(
    boxes_xyxy: torch.Tensor,
    scores: torch.Tensor,
    labels: list[str],
    iou_threshold: float,
) -> list[int]:
    keep_indices: list[int] = []
    for label in set(labels):
        label_indices = [i for i, item in enumerate(labels) if item == label]
        label_indices_tensor = torch.tensor(label_indices, dtype=torch.long)
        kept_local_indices = nms(
            boxes_xyxy[label_indices_tensor],
            scores[label_indices_tensor],
            iou_threshold,
        )
        keep_indices.extend(label_indices_tensor[kept_local_indices].tolist())
    return sorted(keep_indices, key=lambda i: float(scores[i]), reverse=True)

def get_latest_run_dir() -> Path:
    runs_dir = PROJECT_ROOT / "data" / "processed" / "runs"
    run_dirs = [path for path in runs_dir.iterdir() if path.is_dir()]
    if not run_dirs:
        raise FileNotFoundError(f"No run directories found in {runs_dir}")
    return sorted(run_dirs)[-1]

def collect_images(run_dir: Path) -> list[tuple[Path, str]]:
    media_dir = run_dir / "media"
    image_dirs = [
        (media_dir / "images", "image"),
        (media_dir / "frames", "video_frame"),
    ]
    result: list[tuple[Path, str]] = []
    for folder, media_type in image_dirs:
        if not folder.exists():
            continue
        for path in sorted(folder.rglob("*")):
            if path.suffix.lower() in IMAGE_EXTENSIONS:
                result.append((path, media_type))
    return result

def detect_image(
    model,
    image_path: Path,
    media_type: str,
    device: str,
    text_prompt: str,
    box_threshold: float,
    text_threshold: float,
    nms_iou_threshold: float,
) -> dict:
    _, image = load_image(str(image_path))
    boxes, logits, phrases = predict(
        model=model,
        image=image,
        caption=text_prompt,
        box_threshold=box_threshold,
        text_threshold=text_threshold,
        device=device,
    )
    with Image.open(image_path) as img:
        width, height = img.size

    if len(boxes) == 0:
        return {
            "image_id": image_path.stem,
            "image_path": image_path.relative_to(PROJECT_ROOT).as_posix(),
            "media_type": media_type,
            "width": width,
            "height": height,
            "detections": [],
        }

    boxes_xyxy = box_convert(boxes=boxes, in_fmt="cxcywh", out_fmt="xyxy")
    boxes_xyxy = boxes_xyxy * torch.tensor([width, height, width, height])
    keep_indices = apply_label_nms(
        boxes_xyxy=boxes_xyxy,
        scores=logits,
        labels=phrases,
        iou_threshold=nms_iou_threshold,
    )
    boxes_xyxy = boxes_xyxy[keep_indices]
    logits = logits[keep_indices]
    phrases = [phrases[i] for i in keep_indices]

    detections = []
    for phrase, score, box in zip(phrases, logits.tolist(), boxes_xyxy.tolist()):
        detections.append(
            {
                "label": phrase,
                "score": round(float(score), 4),
                "box_xyxy": [round(float(value), 2) for value in box],
            }
        )

    return {
        "image_id": image_path.stem,
        "image_path": image_path.relative_to(PROJECT_ROOT).as_posix(),
        "media_type": media_type,
        "width": width,
        "height": height,
        "detections": detections,
    }

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-date", help="Run date folder, for example 2026-06-19")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--box-threshold", type=float, default=0.35)
    parser.add_argument("--text-threshold", type=float, default=0.25)
    parser.add_argument("--nms-iou-threshold", type=float, default=0.5)
    args = parser.parse_args()

    taxonomy = FashionTaxonomy.load()
    text_prompt = taxonomy.get_dino_prompt()

    if args.run_date:
        run_dir = PROJECT_ROOT / "data" / "processed" / "runs" / args.run_date
    else:
        run_dir = get_latest_run_dir()

    if not run_dir.exists():
        raise FileNotFoundError(f"Run directory not found: {run_dir}")

    image_paths = collect_images(run_dir)
    if args.limit:
        image_paths = image_paths[: args.limit]
    if not image_paths:
        raise FileNotFoundError(f"No images or frames found in {run_dir / 'media'}")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")
    print(f"Run dir: {run_dir}")
    print(f"Images: {len(image_paths)}")
    print(f"Categories: {len(taxonomy.get_categories())}")
    print(f"Box threshold: {args.box_threshold}")
    print(f"Text threshold: {args.text_threshold}")
    print(f"NMS IOU threshold: {args.nms_iou_threshold}")

    model = load_model(str(CONFIG_PATH), str(WEIGHTS_PATH), device=device)
    results = []

    for index, (image_path, media_type) in enumerate(image_paths, start=1):
        print(f"[{index}/{len(image_paths)}] {image_path.name}")
        result = detect_image(
            model=model,
            image_path=image_path,
            media_type=media_type,
            device=device,
            text_prompt=text_prompt,
            box_threshold=args.box_threshold,
            text_threshold=args.text_threshold,
            nms_iou_threshold=args.nms_iou_threshold,
        )
        results.append(result)

    output_path = run_dir / "detections.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    total_detections = sum(len(item["detections"]) for item in results)
    print()
    print(f"Saved detections: {output_path}")
    print(f"Images processed: {len(results)}")
    print(f"Objects detected: {total_detections}")

if __name__ == "__main__":
    main()