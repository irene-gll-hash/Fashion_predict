from __future__ import annotations
import argparse
import base64
import json
import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

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


def collect_media_items(normalized_posts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []

    for post_index, post in enumerate(normalized_posts, start=1):
        post_url = post.get("post_url")
        source_username = post.get("source_username")
        raw_type = post.get("raw_type")

        for image_index, image_path in enumerate(post.get("local_image_paths") or [], start=1):
            items.append(
                {
                    "image_id": f"post_{post_index:04d}_image_{image_index:03d}",
                    "image_path": image_path,
                    "media_type": "image",
                    "post_url": post_url,
                    "source_username": source_username,
                    "raw_type": raw_type,
                }
            )

        for frame_index, frame_path in enumerate(post.get("local_frame_paths") or [], start=1):
            items.append(
                {
                    "image_id": f"post_{post_index:04d}_frame_{frame_index:03d}",
                    "image_path": frame_path,
                    "media_type": "frame",
                    "post_url": post_url,
                    "source_username": source_username,
                    "raw_type": raw_type,
                }
            )

    return items


def encode_image_base64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("utf-8")


def call_gpu_detection(gpu_service_url: str, image_path: Path) -> dict[str, Any]:
    payload = {"image": encode_image_base64(image_path)}
    response = requests.post(
        f"{gpu_service_url.rstrip('/')}/detect",
        json=payload,
        timeout=600,
    )
    response.raise_for_status()
    return response.json()


def normalize_detection_result(raw_result: dict[str, Any]) -> list[dict[str, Any]]:
    boxes = raw_result.get("boxes") or []
    scores = raw_result.get("scores") or []
    phrases = raw_result.get("phrases") or []

    detections: list[dict[str, Any]] = []
    for box, score, phrase in zip(boxes, scores, phrases):
        detections.append(
            {
                "label": phrase,
                "score": float(score),
                "box_xyxy": box,
            }
        )
    return detections


def get_image_size(image_path: Path) -> tuple[int, int]:
    from PIL import Image

    with Image.open(image_path) as image:
        return image.size


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-date", help="Run date folder, for example 2026-06-19")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--box-threshold", type=float, default=0.35)
    parser.add_argument("--text-threshold", type=float, default=0.25)
    parser.add_argument("--nms-iou-threshold", type=float, default=0.5)
    args = parser.parse_args()

    load_dotenv(PROJECT_ROOT / ".env")

    gpu_service_url = os.getenv("GPU_SERVICE_URL")
    if not gpu_service_url:
        raise ValueError("GPU_SERVICE_URL is not set")

    run_dir = PROJECT_ROOT / "data" / "processed" / "runs" / args.run_date if args.run_date else get_latest_run_dir()
    if not run_dir.exists():
        raise FileNotFoundError(f"Run directory not found: {run_dir}")

    normalized_posts_path = run_dir / "normalized_posts.json"
    if not normalized_posts_path.exists():
        raise FileNotFoundError(f"Normalized posts file not found: {normalized_posts_path}")

    normalized_posts = load_json(normalized_posts_path)
    if not isinstance(normalized_posts, list):
        raise ValueError(f"Normalized posts file must contain a list: {normalized_posts_path}")

    media_items = collect_media_items(normalized_posts)
    if args.limit:
        media_items = media_items[: args.limit]

    if not media_items:
        raise ValueError(f"No media items found in {normalized_posts_path}")

    results: list[dict[str, Any]] = []

    print(f"Run dir: {run_dir}")
    print(f"Gpu service url: {gpu_service_url}")
    print(f"Media items: {len(media_items)}")

    for index, item in enumerate(media_items, start=1):
        image_path = PROJECT_ROOT / item["image_path"]
        if not image_path.exists():
            print(f"[{index}/{len(media_items)}] Missing image: {image_path}")
            continue

        print(f"[{index}/{len(media_items)}] Detect: {image_path.name}")

        width, height = get_image_size(image_path)
        raw_result = call_gpu_detection(
            gpu_service_url=gpu_service_url,
            image_path=image_path,
        )

        detections = normalize_detection_result(raw_result)

        results.append(
            {
                **item,
                "width": width,
                "height": height,
                "detections": detections,
            }
        )

    output_path = run_dir / "detections.json"
    save_json(results, output_path)

    print()
    print(f"Saved detections: {output_path}")
    print(f"Images processed: {len(results)}")

    upload_run_dir_if_enabled(run_dir)


if __name__ == "__main__":
    main()