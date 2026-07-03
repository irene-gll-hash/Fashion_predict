from __future__ import annotations
import argparse
import os
from pathlib import Path
from typing import Any
from ai.product_gemini_analyzer import ProductGeminiAnalyzer
from sources.common.image_downloader import download_images, sanitize_filename
from sources.common.io import load_json, save_json
from sources.lamoda.loader import find_lamoda_input_file, load_lamoda_products
from sources.lamoda.normalizer import (
    build_enriched_lamoda_product,
    get_lamoda_image_urls,
    normalize_lamoda_records,
)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True, help="Run date, for example: 2026-07-03")
    parser.add_argument("--input-file", default=None, help="Optional explicit Lamoda input file path.")
    parser.add_argument("--limit", type=int, default=None, help="Limit products for test runs.")
    parser.add_argument("--max-images-per-product", type=int, default=2)
    parser.add_argument("--skip-gemini", action="store_true", help="Only normalize and download images.")
    parser.add_argument("--sleep-seconds", type=float, default=2.0)
    parser.add_argument("--max-retries", type=int, default=3)
    args = parser.parse_args()
    run_date = args.date
    compact_date = run_date.replace("-", "")
    date_dir = DATA_DIR / "lamoda" / run_date
    images_dir = date_dir / "images"
    input_file = Path(args.input_file) if args.input_file else find_lamoda_input_file(DATA_DIR, run_date)
    normalized_output = date_dir / f"normalized_lamoda_products_{compact_date}.json"
    gemini_output = date_dir / f"gemini_lamoda_analysis_{compact_date}.json"
    enriched_output = date_dir / f"enriched_lamoda_products_{compact_date}.json"
    print(f"[INFO] Input file: {input_file}")
    raw_records = load_lamoda_products(input_file)
    if args.limit:
        raw_records = raw_records[: args.limit]
    normalized_products = normalize_lamoda_records(raw_records)
    save_json(normalized_output, normalized_products)
    print(f"[INFO] Saved normalized products: {normalized_output}")
    print(f"[INFO] Products count: {len(normalized_products)}")
    existing_analysis = _load_existing_analysis(gemini_output)
    analyzer = None if args.skip_gemini else ProductGeminiAnalyzer(
        sleep_seconds=args.sleep_seconds,
        max_retries=args.max_retries,
    )
    gemini_results_by_product_id: dict[str, dict[str, Any]] = dict(existing_analysis)
    for index, product in enumerate(normalized_products, start=1):
        product_id = str(product["product_id"])
        product_image_dir = images_dir / sanitize_filename(product_id)
        image_urls = get_lamoda_image_urls(product)
        image_paths = download_images(
            image_urls=image_urls,
            output_dir=product_image_dir,
            max_images=args.max_images_per_product,
        )
        print(
            f"[INFO] {index}/{len(normalized_products)} "
            f"{product_id}: downloaded/available images={len(image_paths)}"
        )
        if args.skip_gemini:
            continue
        if product_id in gemini_results_by_product_id:
            print(f"[INFO] {product_id}: Gemini analysis already exists, skipping.")
            continue
        if not image_paths:
            gemini_results_by_product_id[product_id] = {
                "product_id": product_id,
                "source": "lamoda",
                "status": "error",
                "gemini_analysis": None,
                "analysis_meta": {
                    "error": "No images available for product.",
                    "images_used": [],
                },
            }
            save_json(gemini_output, list(gemini_results_by_product_id.values()))
            continue
        assert analyzer is not None
        result = analyzer.analyze_lamoda_product(
            product=product["original"],
            image_paths=image_paths,
        )
        gemini_results_by_product_id[product_id] = result
        save_json(gemini_output, list(gemini_results_by_product_id.values()))
        print(f"[INFO] {product_id}: Gemini status={result.get('status')}")
    enriched_products = []
    for product in normalized_products:
        product_id = str(product["product_id"])
        gemini_result = gemini_results_by_product_id.get(product_id)
        enriched_products.append(
            build_enriched_lamoda_product(
                product=product,
                gemini_result=gemini_result,
            )
        )
    save_json(enriched_output, enriched_products)
    print(f"[INFO] Saved Gemini analysis: {gemini_output}")
    print(f"[INFO] Saved enriched products: {enriched_output}")
def _load_existing_analysis(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    data = load_json(path)
    if not isinstance(data, list):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for item in data:
        if not isinstance(item, dict):
            continue
        product_id = item.get("product_id")
        if product_id:
            result[str(product_id)] = item
    return result
if __name__ == "__main__":
    main()
