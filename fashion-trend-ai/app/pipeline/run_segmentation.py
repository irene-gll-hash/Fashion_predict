from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from typing import Any
from PIL import Image
from app.storage.gcs_storage import upload_run_dir_if_enabled

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CROP_PADDING = 0.12
MIN_CROP_SIZE = 96
DEDUP_IOU_THRESHOLD = 0.75
MAX_CROPS_PER_IMAGE = 5
SKIP_TINY_CROPS = True

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

def clamp(value: int, min_value: int, max_value: int) -> int:
    return max(min_value, min(value, max_value))

def clamp_box(box: list[float], width: int, height: int) -> list[int]:
    x1, y1, x2, y2 = box
    x1 = clamp(int(round(x1)), 0, width - 1)
    y1 = clamp(int(round(y1)), 0, height - 1)
    x2 = clamp(int(round(x2)), 1, width)
    y2 = clamp(int(round(y2)), 1, height)
    if x2 <= x1:
        x2 = min(width, x1 + 1)
    if y2 <= y1:
        y2 = min(height, y1 + 1)
    return [x1, y1, x2, y2]

def pad_box(box_xyxy: list[int], image_width: int, image_height: int) -> list[int]:
    x1, y1, x2, y2 = box_xyxy
    box_width = x2 - x1
    box_height = y2 - y1
    pad_x = int(box_width * CROP_PADDING)
    pad_y = int(box_height * CROP_PADDING)
    x1 -= pad_x
    y1 -= pad_y
    x2 += pad_x
    y2 += pad_y
    current_width = x2 - x1
    current_height = y2 - y1
    if current_width < MIN_CROP_SIZE:
        extra = (MIN_CROP_SIZE - current_width) // 2
        x1 -= extra
        x2 += extra
    if current_height < MIN_CROP_SIZE:
        extra = (MIN_CROP_SIZE - current_height) // 2
        y1 -= extra
        y2 += extra
    return [
        clamp(x1, 0, image_width - 1),
        clamp(y1, 0, image_height - 1),
        clamp(x2, 1, image_width),
        clamp(y2, 1, image_height),
    ]

def get_crop_quality(box_xyxy: list[int], image_width: int, image_height: int) -> dict[str, Any]:
    x1, y1, x2, y2 = box_xyxy
    box_width = max(0, x2 - x1)
    box_height = max(0, y2 - y1)
    box_area = box_width * box_height
    image_area = image_width * image_height
    area_ratio = box_area / image_area if image_area else 0
    return {
        "box_width": box_width,
        "box_height": box_height,
        "box_area": box_area,
        "image_area": image_area,
        "area_ratio": round(area_ratio, 6),
        "is_tiny": box_width < 64 or box_height < 64 or area_ratio < 0.001,
        "is_small": box_width < 96 or box_height < 96 or area_ratio < 0.003,
    }

def box_area(box_xyxy: list[int]) -> int:
    x1, y1, x2, y2 = box_xyxy
    return max(0, x2 - x1) * max(0, y2 - y1)

def box_iou(box_a: list[int], box_b: list[int]) -> float:
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b
    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)
    inter_area = box_area([ix1, iy1, ix2, iy2])
    if inter_area <= 0:
        return 0.0
    union_area = box_area(box_a) + box_area(box_b) - inter_area
    if union_area <= 0:
        return 0.0
    return inter_area / union_area

def is_duplicate_box(candidate_box: list[int], kept_boxes: list[list[int]], threshold: float) -> bool:
    return any(box_iou(candidate_box, kept_box) >= threshold for kept_box in kept_boxes)

def prepare_detections_for_cropping(
    detections: list[dict[str, Any]],
    image_width: int,
    image_height: int,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    prepared = []
    skipped_tiny = 0
    skipped_duplicate = 0
    skipped_over_limit = 0

    for detection in detections:
        box_xyxy = clamp_box(detection["box_xyxy"], width=image_width, height=image_height)
        padded_box_xyxy = pad_box(box_xyxy, image_width=image_width, image_height=image_height)
        crop_quality = get_crop_quality(
            box_xyxy=box_xyxy,
            image_width=image_width,
            image_height=image_height,
        )
        if SKIP_TINY_CROPS and crop_quality["is_tiny"]:
            skipped_tiny += 1
            continue
        prepared.append(
            {
                **detection,
                "box_xyxy": box_xyxy,
                "padded_box_xyxy": padded_box_xyxy,
                "crop_quality": crop_quality,
            }
        )

    prepared.sort(key=lambda item: float(item.get("score", 0)), reverse=True)
    kept = []
    kept_boxes = []

    for detection in prepared:
        candidate_box = detection["box_xyxy"]
        if is_duplicate_box(candidate_box, kept_boxes, DEDUP_IOU_THRESHOLD):
            skipped_duplicate += 1
            continue
        if len(kept) >= MAX_CROPS_PER_IMAGE:
            skipped_over_limit += 1
            continue
        kept.append(detection)
        kept_boxes.append(candidate_box)

    stats = {
        "input_detections": len(detections),
        "prepared_detections": len(prepared),
        "kept_detections": len(kept),
        "skipped_tiny": skipped_tiny,
        "skipped_duplicate": skipped_duplicate,
        "skipped_over_limit": skipped_over_limit,
    }
    return kept, stats

def load_detections(run_dir: Path) -> list[dict[str, Any]]:
    detections_path = run_dir / "detections.json"
    if not detections_path.exists():
        raise FileNotFoundError(f"Detections file not found: {detections_path}")
    with detections_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Detections file must contain a list: {detections_path}")
    return data

def save_crop(
    image: Image.Image,
    box_xyxy: list[int],
    padded_box_xyxy: list[int],
    image_id: str,
    label: str,
    detection_index: int,
    output_dir: Path,
) -> dict[str, Any]:
    label_name = safe_name(label)
    file_stem = f"{image_id}_{detection_index:03d}_{label_name}"
    crops_dir = output_dir / "crops"
    crops_dir.mkdir(parents=True, exist_ok=True)
    crop = image.crop(tuple(padded_box_xyxy))
    crop_path = crops_dir / f"{file_stem}_crop.png"
    crop.save(crop_path)
    return {
        "crop_path": crop_path.relative_to(PROJECT_ROOT).as_posix(),
        "box_xyxy": box_xyxy,
        "padded_box_xyxy": padded_box_xyxy,
    }

def process_image(image_result: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    image_path = PROJECT_ROOT / image_result["image_path"]
    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    with Image.open(image_path).convert("RGB") as image:
        image_width, image_height = image.size
        segmentations = []

        detections, dedup_stats = prepare_detections_for_cropping(
            detections=image_result.get("detections", []),
            image_width=image_width,
            image_height=image_height,
        )

        for detection_index, detection in enumerate(detections, start=1):
            label = detection["label"]
            box_xyxy = detection["box_xyxy"]
            padded_box_xyxy = detection["padded_box_xyxy"]

            saved = save_crop(
                image=image,
                box_xyxy=box_xyxy,
                padded_box_xyxy=padded_box_xyxy,
                image_id=image_result["image_id"],
                label=label,
                detection_index=detection_index,
                output_dir=output_dir,
            )

            segmentations.append(
                {
                    "label": label,
                    "dino_score": detection["score"],
                    "box_xyxy": saved["box_xyxy"],
                    "padded_box_xyxy": saved["padded_box_xyxy"],
                    "crop_quality": detection["crop_quality"],
                    "crop_path": saved["crop_path"],
                }
            )

    return {
        "image_id": image_result["image_id"],
        "image_path": image_result["image_path"],
        "media_type": image_result["media_type"],
        "width": image_result["width"],
        "height": image_result["height"],
        "dedup_stats": dedup_stats,
        "segmentations": segmentations,
    }

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-date", help="Run date folder, for example 2026-06-19")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    run_dir = PROJECT_ROOT / "data" / "processed" / "runs" / args.run_date if args.run_date else get_latest_run_dir()
    if not run_dir.exists():
        raise FileNotFoundError(f"Run directory not found: {run_dir}")

    detections = load_detections(run_dir)
    if args.limit:
        detections = detections[: args.limit]
    if not detections:
        raise ValueError(f"No detections to process in {run_dir}")

    output_dir = run_dir / "segmentation"
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    print(f"Run dir: {run_dir}")
    print(f"Images: {len(detections)}")
    print(f"Crop padding: {CROP_PADDING}")
    print(f"Min crop size: {MIN_CROP_SIZE}")
    print(f"Skip tiny crops: {SKIP_TINY_CROPS}")
    print(f"Dedup IoU threshold: {DEDUP_IOU_THRESHOLD}")
    print(f"Max crops per image: {MAX_CROPS_PER_IMAGE}")

    for index, image_result in enumerate(detections, start=1):
        print(f"[{index}/{len(detections)}] {image_result['image_id']}")
        result = process_image(image_result=image_result, output_dir=output_dir)
        stats = result["dedup_stats"]
        print(
            "  "
            f"input={stats['input_detections']}, "
            f"kept={stats['kept_detections']}, "
            f"tiny={stats['skipped_tiny']}, "
            f"duplicates={stats['skipped_duplicate']}, "
            f"over_limit={stats['skipped_over_limit']}"
        )
        results.append(result)

    output_path = output_dir / "segmentations.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    total_input = sum(item["dedup_stats"]["input_detections"] for item in results)
    total_crops = sum(len(item["segmentations"]) for item in results)
    total_tiny_skipped = sum(item["dedup_stats"]["skipped_tiny"] for item in results)
    total_duplicates_skipped = sum(item["dedup_stats"]["skipped_duplicate"] for item in results)
    total_over_limit_skipped = sum(item["dedup_stats"]["skipped_over_limit"] for item in results)
    tiny_crops = sum(
        1
        for item in results
        for segment in item["segmentations"]
        if segment["crop_quality"]["is_tiny"]
    )

    print()
    print(f"Saved segmentations: {output_path}")
    print(f"Input detections: {total_input}")
    print(f"Crops saved: {total_crops}")
    print(f"Skipped tiny detections: {total_tiny_skipped}")
    print(f"Skipped duplicate detections: {total_duplicates_skipped}")
    print(f"Skipped over limit: {total_over_limit_skipped}")
    print(f"Tiny crops saved: {tiny_crops}")

    upload_run_dir_if_enabled(run_dir)

if __name__ == "__main__":
    main()