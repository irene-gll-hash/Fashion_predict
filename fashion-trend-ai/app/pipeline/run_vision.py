from __future__ import annotations
import json
from datetime import date
from pathlib import Path
from app.config import settings
from app.storage.json_storage import save_raw_json
from app.vision.client import GoogleVisionClient

def load_normalized_posts(run_dir: Path) -> list[dict]:
    path = run_dir / "normalized_posts.json"
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))

def analyze_media_paths(client: GoogleVisionClient, paths: list[str], media_type: str) -> list[dict]:
    results = []
    for path in paths:
        result = client.analyze_image_file(path)
        result["media_type"] = media_type
        results.append(result)
    return results

def main() -> None:
    if not settings.google_vision_api_key:
        raise RuntimeError("GOOGLE_VISION_API_KEY is not set")
    run_date = date.today().isoformat()
    run_dir = Path(f"data/processed/runs/{run_date}")
    posts = load_normalized_posts(run_dir)
    client = GoogleVisionClient(api_key=settings.google_vision_api_key)
    results = []
    for post in posts:
        image_results = analyze_media_paths(client, post.get("local_image_paths", []), "image")
        frame_results = analyze_media_paths(client, post.get("local_frame_paths", []), "video_frame")
        post_result = {
            "post_url": post["post_url"],
            "source_username": post["source_username"],
            "published_at": post["published_at"],
            "media": image_results + frame_results,
        }
        results.append(post_result)
        print(f"Vision done: {post['source_username']} images={len(image_results)} frames={len(frame_results)}")
    save_raw_json(results, f"{run_dir}/vision_results.json")
    print(f"Saved to: {run_dir}/vision_results.json")

if __name__ == "__main__":
    main()