from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import torch
from PIL import Image
PROJECT_ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("HF_HOME", str(PROJECT_ROOT / "external" / "hf_cache"))
from transformers import CLIPModel, CLIPProcessor

MODEL_NAME = "patrickjohncyh/fashion-clip"
CATEGORY_LABELS = ["dress", "top", "shirt", "skirt", "jacket", "jeans", "pants", "shoes", "sandals", "handbag", "sunglasses", "belt"]
STYLE_LABELS = ["casual style", "streetwear style", "minimalist style", "business style", "evening style", "romantic style", "sporty style", "boho style", "classic style"]
MATERIAL_LABELS = ["denim", "leather", "knitwear", "cotton fabric", "silk satin", "lace", "wool", "suede", "synthetic fabric", "transparent fabric"]

def get_latest_run_dir() -> Path:
    runs_dir = PROJECT_ROOT / "data" / "processed" / "runs"
    run_dirs = [path for path in runs_dir.iterdir() if path.is_dir()]
    if not run_dirs:
        raise FileNotFoundError(f"No run directories found in {runs_dir}")
    return sorted(run_dirs)[-1]

def load_segmentations(run_dir: Path) -> list[dict]:
    segmentations_path = run_dir / "segmentation" / "segmentations.json"
    if not segmentations_path.exists():
        raise FileNotFoundError(f"Segmentations file not found: {segmentations_path}")
    with segmentations_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def load_crop_rgb(crop_path: Path) -> Image.Image:
    image = Image.open(crop_path).convert("RGBA")
    background = Image.new("RGBA", image.size, (255, 255, 255, 255))
    return Image.alpha_composite(background, image).convert("RGB")

def encode_texts(model: CLIPModel, processor: CLIPProcessor, texts: list[str], device: str) -> torch.Tensor:
    inputs = processor(text=texts, return_tensors="pt", padding=True).to(device)
    with torch.no_grad():
        features = model.get_text_features(**inputs)
    return features / features.norm(dim=-1, keepdim=True)

def encode_image(model: CLIPModel, processor: CLIPProcessor, image: Image.Image, device: str) -> torch.Tensor:
    inputs = processor(images=image, return_tensors="pt").to(device)
    with torch.no_grad():
        features = model.get_image_features(**inputs)
    return features / features.norm(dim=-1, keepdim=True)

def all_matches(image_features: torch.Tensor, text_features: torch.Tensor, labels: list[str]) -> list[dict]:
    scores = (image_features @ text_features.T).squeeze(0)
    values, indices = torch.sort(scores, descending=True)
    return [{"label": labels[int(index)], "score": round(float(value), 4)} for value, index in zip(values, indices)]

def classify_crop(
    model: CLIPModel,
    processor: CLIPProcessor,
    crop_path: Path,
    device: str,
    category_features: torch.Tensor,
    style_features: torch.Tensor,
    material_features: torch.Tensor,
) -> dict:
    image = load_crop_rgb(crop_path)
    image_features = encode_image(model, processor, image, device)
    return {
        "category_scores": all_matches(image_features, category_features, CATEGORY_LABELS),
        "style_scores": all_matches(image_features, style_features, STYLE_LABELS),
        "material_scores": all_matches(image_features, material_features, MATERIAL_LABELS),
    }

def flatten_segmentations(segmentations: list[dict]) -> list[dict]:
    result = []
    for image_result in segmentations:
        for item in image_result["segmentations"]:
            result.append(
                {
                    "image_id": image_result["image_id"],
                    "image_path": image_result["image_path"],
                    "media_type": image_result["media_type"],
                    "dino_label": item["label"],
                    "dino_score": item["dino_score"],
                    "sam_score": item["sam_score"],
                    "box_xyxy": item["box_xyxy"],
                    "crop_path": item["crop_path"],
                }
            )
    return result

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-date", help="Run date folder, for example 2026-06-15")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    if args.run_date:
        run_dir = PROJECT_ROOT / "data" / "processed" / "runs" / args.run_date
    else:
        run_dir = get_latest_run_dir()
    if not run_dir.exists():
        raise FileNotFoundError(f"Run directory not found: {run_dir}")
    segmentations = flatten_segmentations(load_segmentations(run_dir))
    if args.limit:
        segmentations = segmentations[: args.limit]
    if not segmentations:
        raise ValueError(f"No crops to classify in {run_dir}")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")
    print(f"Run dir: {run_dir}")
    print(f"Crops: {len(segmentations)}")
    model = CLIPModel.from_pretrained(MODEL_NAME).to(device)
    processor = CLIPProcessor.from_pretrained(MODEL_NAME)
    category_features = encode_texts(model, processor, CATEGORY_LABELS, device)
    style_features = encode_texts(model, processor, STYLE_LABELS, device)
    material_features = encode_texts(model, processor, MATERIAL_LABELS, device)
    results = []
    for index, item in enumerate(segmentations, start=1):
        print(f"[{index}/{len(segmentations)}] {item['crop_path']}")
        crop_path = PROJECT_ROOT / item["crop_path"]
        predictions = classify_crop(
            model=model,
            processor=processor,
            crop_path=crop_path,
            device=device,
            category_features=category_features,
            style_features=style_features,
            material_features=material_features,
        )
        results.append({**item, "fashion_clip": predictions})
    output_path = run_dir / "fashion_clip_results.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nSaved FashionCLIP results: {output_path}")

if __name__ == "__main__":
    main()