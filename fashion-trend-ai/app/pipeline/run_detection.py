from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import torch
from dotenv import load_dotenv
from PIL import Image

from app.gpu_service.dino import detect_image, load_model
from app.storage.gcs_storage import upload_run_dir_if_enabled
from app.taxonomy.fashion_taxonomy import FashionTaxonomy

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DINO_ROOT = PROJECT_ROOT / "external" / "GroundingDINO"

if str(DINO_ROOT) not in sys.path:
    sys.path.insert(0, str(DINO_ROOT))


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


def build_transform():
    import groundingdino.datasets.transforms as T

    return T.Compose(
        [
            T.RandomResize([800], max_size=1333),
            T.ToTensor(),
            T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )


def load_image_tensor(image_path: Path, transform):
    image_pil = Image.open(image_path).convert("RGB")
    image_tensor, _ = transform(image_pil, None)
    return image_tensor


def normalize_detection_result(
    raw_result: dict[str, Any],
    image_width: int,
    image_height: int,
) -> list[dict[str, Any]]:
    boxes = raw_result.get("boxes") or []
    scores = raw_result.get("scores") or []
    phrases = raw_result.get("phrases") or []

    detections: list[dict[str, Any]] = []

    for box, score, phrase in zip(boxes, scores, phrases):
        cx, cy, w, h = box

        x1 = (cx - w / 2) * image_width
        y1 = (cy - h / 2) * image_height
        x2 = (cx + w / 2) * image_width
        y2 = (cy + h / 2) * image_height

        x1 = max(0.0, min(float(x1), float(image_width)))
        y1 = max(0.0, min(float(y1), float(image_height)))
        x2 = max(0.0, min(float(x2), float(image_width)))
        y2 = max(0.0, min(float(y2), float(image_height)))

        if x2 <= x1 or y2 <= y1:
            continue

        detections.append(
            {
                "label": phrase,
                "score": float(score),
                "box_xyxy": [x1, y1, x2, y2],
                "box_cxcywh_norm": box,
            }
        )

    return detections


def get_image_size(image_path: Path) -> tuple[int, int]:
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

    require_cuda = os.getenv("REQUIRE_CUDA", "0") == "1"

    cuda_available = torch.cuda.is_available()

    print(f"torch version: {torch.__version__}")
    print(f"torch cuda build: {torch.version.cuda}")
    print(f"torch cuda available: {cuda_available}")

    if cuda_available:
        print(f"gpu name: {torch.cuda.get_device_name(0)}")

    if require_cuda and not cuda_available:
        raise RuntimeError("CUDA is required, but torch.cuda.is_available() is False")

    device = "cuda" if cuda_available else "cpu"

    print(f"Detection device: {device}")

    run_dir = (
        PROJECT_ROOT / "data" / "processed" / "runs" / args.run_date
        if args.run_date
        else get_latest_run_dir()
    )

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

    print(f"Run dir: {run_dir}")
    print(f"Media items: {len(media_items)}")
    print("Loading GroundingDINO...")

    taxonomy = FashionTaxonomy.load()
    text_prompt = taxonomy.get_dino_prompt()

    model = load_model(device=device)
    transform = build_transform()

    print("GroundingDINO loaded")

    results: list[dict[str, Any]] = []

    for index, item in enumerate(media_items, start=1):
        image_path = PROJECT_ROOT / item["image_path"]

        if not image_path.exists():
            print(f"[{index}/{len(media_items)}] Missing image: {image_path}")
            continue

        print(f"[{index}/{len(media_items)}] Detect: {image_path.name}")

        width, height = get_image_size(image_path)
        image_tensor = load_image_tensor(image_path, transform)

        raw_result = detect_image(
            model=model,
            image=image_tensor,
            device=device,
            text_prompt=text_prompt,
            box_threshold=args.box_threshold,
            text_threshold=args.text_threshold,
            nms_iou_threshold=args.nms_iou_threshold,
        )

        detections = normalize_detection_result(
            raw_result=raw_result,
            image_width=width,
            image_height=height,
        )

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