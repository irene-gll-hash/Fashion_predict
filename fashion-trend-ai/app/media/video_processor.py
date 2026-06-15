from __future__ import annotations
import hashlib
from pathlib import Path
import cv2
import requests

def make_video_filename(post_url: str, video_url: str, index: int) -> str:
    raw = f"{post_url}_{video_url}_{index}".encode("utf-8")
    digest = hashlib.md5(raw).hexdigest()
    return f"{digest}.mp4"

def make_frame_filename(video_path: Path, frame_index: int) -> str:
    return f"{video_path.stem}_frame_{frame_index:03d}.jpg"

def download_video(video_url: str, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        return output_path
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(video_url, timeout=(10, 180), headers=headers)
    response.raise_for_status()
    output_path.write_bytes(response.content)
    return output_path

def extract_frames(video_path: Path, frames_dir: Path, every_seconds: int = 5, max_frames: int = 15) -> list[str]:
    frames_dir.mkdir(parents=True, exist_ok=True)
    video = cv2.VideoCapture(str(video_path))
    if not video.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")
    fps = video.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        fps = 25
    frame_step = int(fps * every_seconds)
    saved_frames = []
    frame_number = 0
    saved_count = 0
    while saved_count < max_frames:
        success, frame = video.read()
        if not success:
            break
        if frame_number % frame_step == 0:
            frame_path = frames_dir / make_frame_filename(video_path, saved_count)
            cv2.imwrite(str(frame_path), frame)
            saved_frames.append(str(frame_path))
            saved_count += 1
        frame_number += 1
    video.release()
    return saved_frames

def process_post_videos(post, run_dir: str, keep_video: bool = False) -> list[str]:
    frame_paths = []
    videos_dir = Path(run_dir) / "media" / "videos_temp"
    frames_dir = Path(run_dir) / "media" / "frames"
    for index, video_url in enumerate(post.video_urls):
        filename = make_video_filename(post.post_url, video_url, index)
        video_path = videos_dir / filename
        downloaded_video = download_video(video_url, video_path)
        frames = extract_frames(downloaded_video, frames_dir)
        frame_paths.extend(frames)
        if not keep_video and downloaded_video.exists():
            downloaded_video.unlink()
    return frame_paths
