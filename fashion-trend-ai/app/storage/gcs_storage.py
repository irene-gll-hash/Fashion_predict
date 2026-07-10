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
def download_directory_from_gcs(bucket_name: str, gcs_prefix: str, local_dir: Path) -> None:
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    normalized_prefix = gcs_prefix.strip("/") + "/"
    blobs = list(client.list_blobs(bucket, prefix=normalized_prefix))
    if not blobs:
        raise FileNotFoundError(
            f"No files found in gs://{bucket_name}/{normalized_prefix}"
        )
    downloaded = 0
    for blob in blobs:
        if blob.name.endswith("/"):
            continue
        relative_path = blob.name[len(normalized_prefix):]
        if not relative_path:
            continue
        local_path = local_dir / relative_path
        local_path.parent.mkdir(parents=True, exist_ok=True)
        blob.download_to_filename(str(local_path))
        downloaded += 1
    print(
        f"Downloaded {downloaded} files from "
        f"gs://{bucket_name}/{normalized_prefix} to {local_dir}"
    )
def download_run_dir_if_needed(run_dir: Path) -> None:
    if run_dir.exists():
        return
    bucket_name = os.getenv("GCS_BUCKET")
    if not bucket_name:
        raise FileNotFoundError(
            f"Run directory does not exist locally and GCS_BUCKET is not set: {run_dir}"
        )
    gcs_prefix = f"runs/{run_dir.name}"
    print(f"Local run directory not found: {run_dir}")
    print(f"Downloading gs://{bucket_name}/{gcs_prefix}")
    download_directory_from_gcs(
        bucket_name=bucket_name,
        gcs_prefix=gcs_prefix,
        local_dir=run_dir,
    )
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