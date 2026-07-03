from __future__ import annotations
import re
import time
import urllib.request
from pathlib import Path
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0 Safari/537.36"
)
def sanitize_filename(value: str) -> str:
    value = value.strip()
    value = re.sub(r"[^\w\-.]+", "_", value, flags=re.UNICODE)
    value = value.strip("_")
    return value or "unknown"
def download_images(
    image_urls: list[str],
    output_dir: Path,
    *,
    max_images: int = 3,
    delay_seconds: float = 0.3,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    downloaded_paths: list[Path] = []
    selected_urls = []
    for url in image_urls:
        if url and url not in selected_urls:
            selected_urls.append(url)
    for index, image_url in enumerate(selected_urls[:max_images], start=1):
        output_path = output_dir / f"image_{index:03d}.jpg"
        if output_path.exists() and output_path.stat().st_size > 0:
            downloaded_paths.append(output_path)
            continue
        try:
            download_image(image_url, output_path)
            downloaded_paths.append(output_path)
            if delay_seconds > 0:
                time.sleep(delay_seconds)
        except Exception as exc:
            print(f"[WARN] Failed to download image: {image_url}. Error: {exc}")
    return downloaded_paths
def download_image(url: str, output_path: Path) -> None:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        content = response.read()
    if not content:
        raise ValueError(f"Empty image response: {url}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(content)
