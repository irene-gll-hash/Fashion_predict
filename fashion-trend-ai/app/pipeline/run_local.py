from __future__ import annotations
from datetime import date
from pathlib import Path
from app.apify.client import ApifyInstagramClient
from app.apify.normalizer import normalize_apify_posts
from app.media.downloader import download_post_images
from app.storage.json_storage import save_models_json, save_raw_json
from app.media.video_processor import process_post_videos

def read_source_urls(path: str = "data/raw/source_urls.txt") -> list[str]:
    return [
        line.strip()
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

def main() -> None:
    run_date = date.today().isoformat()
    run_dir = f"data/processed/runs/{run_date}"
    source_urls = read_source_urls()
    client = ApifyInstagramClient()
    raw_posts = client.get_posts_by_urls(source_urls, limit=3)
    posts = normalize_apify_posts(raw_posts)
    for post in posts:
        post.local_image_paths = download_post_images(post, run_dir)
        post.local_frame_paths = process_post_videos(post, run_dir)
        print(f"Downloaded images: {post.source_username} images={len(post.local_image_paths)}")

    save_raw_json(raw_posts, f"{run_dir}/raw_apify_posts.json")
    save_models_json(posts, f"{run_dir}/normalized_posts.json")
    print(f"Run date: {run_date}")
    print(f"Sources: {len(source_urls)}")
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

if __name__ == "__main__":
    main()