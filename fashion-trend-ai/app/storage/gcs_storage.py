from __future__ import annotations
from pathlib import Path
from google.cloud import storage

def upload_directory_to_gcs(local_dir: Path, bucket_name: str, gcs_prefix: str) -> None:
    if not local_dir.exists():
        raise FileNotFoundError(f"Local directory not found: {local_dir}")
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    for local_path in local_dir.rglob("*"):
        if not local_path.is_file():
            continue
        relative_path = local_path.relative_to(local_dir).as_posix()
        blob_name = f"{gcs_prefix.rstrip('/')}/{relative_path}"
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(str(local_path))