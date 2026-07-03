from __future__ import annotations
import argparse
from datetime import date
from pathlib import Path
from app.instagram.client import ApifyInstagramClient
from app.instagram.normalizer import normalize_apify_posts
from app.media.downloader import download_post_images
from app.media.video_processor import process_post_videos
from app.storage.json_storage import save_models_json, save_raw_json
import os
from app.storage.gcs_storage import upload_run_dir_if_enabled
PROJECT_ROOT = Path(__file__).resolve().parents[2]

def read_source_urls(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=5, help="Posts per Instagram source URL")
    parser.add_argument("--frame-every-seconds", type=int, default=3, help="Extract one frame every N seconds")
    parser.add_argument("--max-frames-per-video", type=int, default=2, help="Maximum frames extracted from one video")
    parser.add_argument("--keep-video", action="store_true", help="Keep downloaded mp4 files for debugging")
    args = parser.parse_args()
    run_date = date.today().isoformat()
    run_dir = PROJECT_ROOT / "data" / "processed" / "runs" / run_date
    source_urls_path = PROJECT_ROOT / "data" / "raw" / "source_urls.txt"
    source_urls = read_source_urls(source_urls_path)
    source_urls = list(dict.fromkeys(source_urls))
    client = ApifyInstagramClient()
    raw_posts = client.get_posts_by_urls(source_urls, limit=args.limit)
    save_raw_json(raw_posts, str(run_dir / "raw_apify_posts.json"))
    posts = normalize_apify_posts(raw_posts)
    for post in posts:
        post.local_image_paths = download_post_images(post, str(run_dir))
        post.local_frame_paths = process_post_videos(
            post=post,
            run_dir=str(run_dir),
            keep_video=args.keep_video,
            every_seconds=args.frame_every_seconds,
            max_frames=args.max_frames_per_video,
        )
        print(
            f"Downloaded media: {post.source_username} "
            f"images={len(post.local_image_paths)} "
            f"frames={len(post.local_frame_paths)}"
        )
    save_models_json(posts, str(run_dir / "normalized_posts.json"))
    print(f"Run date: {run_date}")
    print(f"Sources: {len(source_urls)}")
    print(f"Posts per source limit: {args.limit}")
    print(f"Frame every seconds: {args.frame_every_seconds}")
    print(f"Max frames per video: {args.max_frames_per_video}")
    print(f"Keep video: {args.keep_video}")
    print(f"Raw posts: {len(raw_posts)}")
    print(f"Normalized posts: {len(posts)}")
    print(f"Saved to: {run_dir}")
    for post in posts:
        print()
        print(post.source_username)
        print(post.post_url)
        print(f"type={post.raw_type}")
        print(f"images={len(post.image_urls)}")
        print(f"local_images={len(post.local_image_paths)}")
        print(f"videos={len(post.video_urls)}")
        print(f"frames={len(post.local_frame_paths)}")
    

    upload_run_dir_if_enabled(run_dir)

if __name__ == "__main__":
    main()