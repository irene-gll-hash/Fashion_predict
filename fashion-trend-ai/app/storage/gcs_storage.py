from __future__ import annotations
import os
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

def upload_run_dir_if_enabled(run_dir: Path) -> None:
    bucket_name = os.getenv("GCS_BUCKET")
    if not bucket_name:
        return
    gcs_prefix = f"runs/{run_dir.name}"
    print(f"Uploading run directory to gs://{bucket_name}/{gcs_prefix}")
    upload_directory_to_gcs(
        local_dir=run_dir,
        bucket_name=bucket_name,
        gcs_prefix=gcs_prefix,
    )
    print("Upload finished.")