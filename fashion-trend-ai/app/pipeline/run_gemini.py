from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
from typing import Any
from dotenv import load_dotenv
from app.ai.gemini_client import GeminiFashionClient
from app.storage.gcs_storage import upload_run_dir_if_enabled

PROJECT_ROOT = Path(__file__).resolve().parents[2]

def get_latest_run_dir() -> Path:
    runs_dir = PROJECT_ROOT / "data" / "processed" / "runs"
    run_dirs = [path for path in runs_dir.iterdir() if path.is_dir()]
    if not run_dirs:
        raise FileNotFoundError(f"No run directories found in {runs_dir}")
    return sorted(run_dirs)[-1]

def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_json(data: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_segmentations(run_dir: Path) -> list[dict[str, Any]]:
    path = run_dir / "segmentation" / "segmentations.json"
    if not path.exists():
        raise FileNotFoundError(f"Segmentations file not found: {path}")
    data = load_json(path)
    if not isinstance(data, list):
        raise ValueError(f"Segmentations file must contain a list: {path}")
    return data

def load_existing_results(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    data = load_json(path)
    if not isinstance(data, list):
        raise ValueError(f"Existing Gemini results must contain a list: {path}")
    result = {}
    for item in data:
        crop_path = item.get("crop_path")
        if crop_path:
            result[crop_path] = item
    return result

def collect_crop_items(segmentations_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for image_item in segmentations_data:
        segmentations = image_item.get("segmentations") or []
        if not isinstance(segmentations, list):
            continue
        for object_index, segmentation in enumerate(segmentations, start=1):
            crop_path = segmentation.get("crop_path")
            if not crop_path:
                continue
            items.append(
                {
                    "image_id": image_item.get("image_id"),
                    "image_path": image_item.get("image_path"),
                    "media_type": image_item.get("media_type"),
                    "width": image_item.get("width"),
                    "height": image_item.get("height"),
                    "object_index": object_index,
                    "dino_label": segmentation.get("label"),
                    "dino_score": segmentation.get("dino_score"),
                    "sam_score": segmentation.get("sam_score"),
                    "box_xyxy": segmentation.get("box_xyxy"),
                    "padded_box_xyxy": segmentation.get("padded_box_xyxy"),
                    "crop_quality": segmentation.get("crop_quality"),
                    "crop_path": crop_path,
                }
            )
    return items

def resolve_crop_path(crop_path: str) -> Path:
    path = Path(crop_path)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path

def is_successfully_processed(item: dict[str, Any] | None) -> bool:
    if not item:
        return False
    gemini = item.get("gemini") or {}
    return gemini.get("attributes") is not None and gemini.get("error") is None

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-date", help="Run date folder, for example 2026-06-19")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--force", action="store_true", help="Reprocess all crops, including successful ones")
    args = parser.parse_args()
    load_dotenv(PROJECT_ROOT / ".env")
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    if not project:
        raise ValueError("GOOGLE_CLOUD_PROJECT is not set in .env")
    run_dir = PROJECT_ROOT / "data" / "processed" / "runs" / args.run_date if args.run_date else get_latest_run_dir()
    if not run_dir.exists():
        raise FileNotFoundError(f"Run directory not found: {run_dir}")
    output_path = run_dir / "fashion_attributes.json"
    segmentations_data = load_segmentations(run_dir)
    crop_items = collect_crop_items(segmentations_data)
    if args.limit:
        crop_items = crop_items[: args.limit]
    if not crop_items:
        raise FileNotFoundError(f"No crop items found in {run_dir / 'segmentation'}")
    results_by_crop = load_existing_results(output_path)
    client = GeminiFashionClient(project=project, location=location, model=model)
    print(f"Run dir: {run_dir}")
    print(f"Model: {model}")
    print(f"Crops selected: {len(crop_items)}")
    print(f"Existing results: {len(results_by_crop)}")
    processed_now = 0
    skipped = 0
    errors_now = 0
    for index, item in enumerate(crop_items, start=1):
        crop_key = item["crop_path"]
        existing = results_by_crop.get(crop_key)
        if is_successfully_processed(existing) and not args.force:
            skipped += 1
            print(f"[{index}/{len(crop_items)}] Skip existing: {Path(crop_key).name}")
            continue
        crop_path = resolve_crop_path(crop_key)
        dino_label = item.get("dino_label") or "unknown"
        if not crop_path.exists():
            error = f"Crop file not found: {crop_path}"
            result = {**item, "gemini": {"model": model, "attributes": None, "error": error}}
            results_by_crop[crop_key] = result
            save_json(list(results_by_crop.values()), output_path)
            upload_run_dir_if_enabled(run_dir)
            errors_now += 1
            print(f"[{index}/{len(crop_items)}] Missing crop: {crop_path}")
            continue
        print(f"[{index}/{len(crop_items)}] Analyze: {crop_path.name} | dino_label={dino_label}")
        try:
            attributes = client.analyze_crop(crop_path=crop_path, dino_label=dino_label)
            error = None
        except Exception as exc:
            attributes = None
            error = str(exc)
            errors_now += 1
        result = {**item, "gemini": {"model": model, "attributes": attributes, "error": error}}
        results_by_crop[crop_key] = result
        save_json(list(results_by_crop.values()), output_path)
        upload_run_dir_if_enabled(run_dir)
        processed_now += 1
    final_results = list(results_by_crop.values())
    total_errors = sum(1 for item in final_results if (item.get("gemini") or {}).get("error"))
    total_success = sum(1 for item in final_results if is_successfully_processed(item))
    print()
    print(f"Saved Gemini fashion attributes: {output_path}")
    print(f"Processed now: {processed_now}")
    print(f"Skipped existing: {skipped}")
    print(f"Errors now: {errors_now}")
    print(f"Total successful: {total_success}")
    print(f"Total errors: {total_errors}")

if __name__ == "__main__":
    main()