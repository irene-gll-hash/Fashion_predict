from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
import numpy as np
import torch
from PIL import Image
from segment_anything import SamPredictor, sam_model_registry

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAM_MODEL_TYPE = "vit_b"
SAM_CHECKPOINT_PATH = PROJECT_ROOT / "external" / "SAM" / "checkpoints" / "sam_vit_b_01ec64.pth"

def get_latest_run_dir() -> Path:
    runs_dir = PROJECT_ROOT / "data" / "processed" / "runs"
    run_dirs = [path for path in runs_dir.iterdir() if path.is_dir()]
    if not run_dirs:
        raise FileNotFoundError(f"No run directories found in {runs_dir}")
    return sorted(run_dirs)[-1]

def safe_name(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_") or "object"

def clamp_box(box: list[float], width: int, height: int) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = box
    x1 = max(0, min(int(round(x1)), width - 1))
    y1 = max(0, min(int(round(y1)), height - 1))
    x2 = max(0, min(int(round(x2)), width))
    y2 = max(0, min(int(round(y2)), height))
    if x2 <= x1:
        x2 = min(width, x1 + 1)
    if y2 <= y1:
        y2 = min(height, y1 + 1)
    return x1, y1, x2, y2

def load_detections(run_dir: Path) -> list[dict]:
    detections_path = run_dir / "detections.json"
    if not detections_path.exists():
        raise FileNotFoundError(f"Detections file not found: {detections_path}")
    with detections_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_crop(
    image_rgb: np.ndarray,
    mask: np.ndarray,
    box_xyxy: list[float],
    image_id: str,
    label: str,
    detection_index: int,
    output_dir: Path,
) -> dict:
    height, width = image_rgb.shape[:2]
    x1, y1, x2, y2 = clamp_box(box_xyxy, width=width, height=height)
    label_name = safe_name(label)
    file_stem = f"{image_id}_{detection_index:03d}_{label_name}"
    crops_dir = output_dir / "crops"
    crops_dir.mkdir(parents=True, exist_ok=True)
    mask_crop = mask[y1:y2, x1:x2]
    image_crop = image_rgb[y1:y2, x1:x2]
    alpha = mask_crop.astype(np.uint8) * 255
    rgba_crop = np.dstack([image_crop, alpha])
    crop_path = crops_dir / f"{file_stem}_crop.png"
    Image.fromarray(rgba_crop).save(crop_path)
    return {
        "crop_path": crop_path.relative_to(PROJECT_ROOT).as_posix(),
        "box_xyxy": [x1, y1, x2, y2],
    }

def segment_image(predictor: SamPredictor, image_result: dict, output_dir: Path) -> dict:
    image_path = PROJECT_ROOT / image_result["image_path"]
    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")
    with Image.open(image_path).convert("RGB") as img:
        image_rgb = np.array(img)
    predictor.set_image(image_rgb)
    segmentations = []
    for detection_index, detection in enumerate(image_result["detections"], start=1):
        box_xyxy = detection["box_xyxy"]
        input_box = np.array(box_xyxy, dtype=np.float32)
        masks, sam_scores, _ = predictor.predict(box=input_box, multimask_output=False)
        saved = save_crop(
            image_rgb=image_rgb,
            mask=masks[0],
            box_xyxy=box_xyxy,
            image_id=image_result["image_id"],
            label=detection["label"],
            detection_index=detection_index,
            output_dir=output_dir,
        )
        segmentations.append(
            {
                "label": detection["label"],
                "dino_score": detection["score"],
                "sam_score": round(float(sam_scores[0]), 4),
                "box_xyxy": saved["box_xyxy"],
                "crop_path": saved["crop_path"],
            }
        )
    return {
        "image_id": image_result["image_id"],
        "image_path": image_result["image_path"],
        "media_type": image_result["media_type"],
        "width": image_result["width"],
        "height": image_result["height"],
        "segmentations": segmentations,
    }

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-date", help="Run date folder, for example 2026-06-15")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    if args.run_date:
        run_dir = PROJECT_ROOT / "data" / "processed" / "runs" / args.run_date
    else:
        run_dir = get_latest_run_dir()
    if not run_dir.exists():
        raise FileNotFoundError(f"Run directory not found: {run_dir}")
    detections = load_detections(run_dir)
    if args.limit:
        detections = detections[: args.limit]
    if not detections:
        raise ValueError(f"No detections to segment in {run_dir}")
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")
    print(f"Run dir: {run_dir}")
    print(f"Images: {len(detections)}")
    
    sam = sam_model_registry[SAM_MODEL_TYPE](checkpoint=str(SAM_CHECKPOINT_PATH))
    sam.to(device=device)
    predictor = SamPredictor(sam)
    output_dir = run_dir / "segmentation"
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []

    for index, image_result in enumerate(detections, start=1):
        print(f"[{index}/{len(detections)}] {image_result['image_id']}")
        result = segment_image(predictor=predictor, image_result=image_result, output_dir=output_dir)
        results.append(result)
    output_path = output_dir / "segmentations.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nSaved segmentations: {output_path}")

if __name__ == "__main__":
    main()