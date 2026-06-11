from __future__ import annotations
from datetime import date
from pathlib import Path
from app.apify.client import ApifyInstagramClient
from app.apify.normalizer import normalize_apify_posts
from app.storage.json_storage import save_models_json, save_raw_json

def read_source_urls(path: str = "data/raw/source_urls.txt") -> list[str]:
    return [
        line.strip()
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

run_date = date.today().isoformat()
run_dir = f"data/processed/runs/{run_date}"

source_urls = read_source_urls()
client = ApifyInstagramClient()
raw_posts = client.get_posts_by_urls(source_urls, limit=5)
posts = normalize_apify_posts(raw_posts)

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
    print(f"videos={len(post.video_urls)}")