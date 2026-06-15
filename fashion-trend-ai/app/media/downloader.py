from __future__ import annotations
import hashlib
from pathlib import Path
import requests

def get_file_extension(url: str) -> str:
    clean_url = url.split("?")[0].lower()
    if clean_url.endswith(".png"):
        return ".png"
    if clean_url.endswith(".webp"):
        return ".webp"
    return ".jpg"

def make_image_filename(post_url: str, image_url: str, index: int) -> str:
    raw = f"{post_url}_{image_url}_{index}".encode("utf-8")
    digest = hashlib.md5(raw).hexdigest()
    return f"{digest}{get_file_extension(image_url)}"

def download_image(image_url: str, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        return output_path
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(image_url, timeout=(10, 120), headers=headers)
    response.raise_for_status()
    output_path.write_bytes(response.content)
    return output_path

def download_post_images(post, run_dir: str) -> list[str]:
    local_paths = []
    images_dir = Path(run_dir) / "media" / "images"
    for index, image_url in enumerate(post.image_urls):
        filename = make_image_filename(post.post_url, image_url, index)
        image_path = images_dir / filename
        saved_path = download_image(image_url, image_path)
        local_paths.append(str(saved_path))
    return local_paths