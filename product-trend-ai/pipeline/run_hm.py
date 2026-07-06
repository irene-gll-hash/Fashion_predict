from __future__ import annotations
import argparse
from pathlib import Path
from typing import Any
from config import DATA_DIR
from ai.product_gemini_analyzer import ProductGeminiAnalyzer
from sources.common.image_downloader import download_images
from sources.common.io import load_json, save_json
from sources.hm.loader import find_hm_input_file, load_hm_products
from sources.hm.normalizer import build_enriched_hm_product, get_hm_image_urls, normalize_hm_records

def _load_existing_gemini_results(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}

    data = load_json(path)
    if not isinstance(data, list):
        return {}

    result: dict[str, dict[str, Any]] = {}

    for item in data:
        if isinstance(item, dict) and item.get("product_id"):
            result[item["product_id"]] = item

    return result

def _save_gemini_results(path: Path, results_by_id: dict[str, dict[str, Any]]) -> None:
    save_json(path, list(results_by_id.values()))

def run_hm(
    date: str,
    input_file: Path | None,
    limit: int | None,
    max_images_per_product: int,
    skip_gemini: bool,
    sleep_seconds: float,
    max_retries: int,
) -> None:
    run_dir = DATA_DIR / "hm" / date
    run_dir.mkdir(parents=True, exist_ok=True)

    input_path = input_file or find_hm_input_file(DATA_DIR, date)

    normalized_file = run_dir / "normalized_hm.json"
    gemini_file = run_dir / "gemini_hm_analysis.json"
    enriched_file = run_dir / "enriched_hm.json"
    images_dir = run_dir / "images"

    raw_products = load_hm_products(input_path)

    if limit is not None:
        raw_products = raw_products[:limit]

    normalized_products = normalize_hm_records(raw_products)
    save_json(normalized_file, normalized_products)

    gemini_results = _load_existing_gemini_results(gemini_file)

    analyzer = None if skip_gemini else ProductGeminiAnalyzer(
        sleep_seconds=sleep_seconds,
        max_retries=max_retries,
    )

    for index, product in enumerate(normalized_products, start=1):
        product_id = product["product_id"]

        print(f"[{index}/{len(normalized_products)}] {product_id}")

        image_urls = get_hm_image_urls(product)
        product_images_dir = images_dir / product_id
        image_paths = download_images(
            image_urls,
            product_images_dir,
            max_images=max_images_per_product,
        )

        if skip_gemini:
            continue

        if product_id in gemini_results and gemini_results[product_id].get("status") == "ok":
            print(f"  Gemini already done: {product_id}")
            continue

        if analyzer is None:
            continue

        gemini_result = analyzer.analyze_product(product, image_paths)
        gemini_result["source"] = "hm"
        gemini_results[product_id] = gemini_result
        _save_gemini_results(gemini_file, gemini_results)

    enriched_products = []

    for product in normalized_products:
        product_id = product["product_id"]
        gemini_result = gemini_results.get(product_id)
        enriched_products.append(build_enriched_hm_product(product, gemini_result))

    save_json(enriched_file, enriched_products)

    print(f"Saved normalized: {normalized_file}")
    print(f"Saved Gemini: {gemini_file}")
    print(f"Saved enriched: {enriched_file}")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    parser.add_argument("--input-file", type=Path, default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--max-images-per-product", type=int, default=None)
    parser.add_argument("--skip-gemini", action="store_true")
    parser.add_argument("--sleep-seconds", type=float, default=1.0)
    parser.add_argument("--max-retries", type=int, default=3)
    return parser.parse_args()

def main() -> None:
    args = parse_args()

    run_hm(
        date=args.date,
        input_file=args.input_file,
        limit=args.limit,
        max_images_per_product=args.max_images_per_product,
        skip_gemini=args.skip_gemini,
        sleep_seconds=args.sleep_seconds,
        max_retries=args.max_retries,
    )

if __name__ == "__main__":
    main()