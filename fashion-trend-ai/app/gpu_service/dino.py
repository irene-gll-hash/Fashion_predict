from __future__ import annotations

import sys
from pathlib import Path

import torch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DINO_ROOT = PROJECT_ROOT / "external" / "GroundingDINO"

if str(DINO_ROOT) not in sys.path:
    sys.path.insert(0, str(DINO_ROOT))


def load_model(device: str = "cuda"):
    from groundingdino.models import build_model
    from groundingdino.util.slconfig import SLConfig
    from groundingdino.util.utils import clean_state_dict

    config_path = str(DINO_ROOT / "groundingdino" / "config" / "GroundingDINO_SwinT_OGC.py")
    checkpoint_path = str(DINO_ROOT / "weights" / "groundingdino_swint_ogc.pth")

    args = SLConfig.fromfile(config_path)
    args.text_encoder_type = "/app/hf_models/bert-base-uncased"

    model = build_model(args)

    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    model.load_state_dict(clean_state_dict(checkpoint["model"]), strict=False)

    model = model.to(device)
    model.eval()

    return model


def detect_image(
    model,
    image,
    device: str,
    text_prompt: str,
    box_threshold: float = 0.35,
    text_threshold: float = 0.25,
    nms_iou_threshold: float = 0.5,
):
    from groundingdino.util.inference import predict

    boxes, logits, phrases = predict(
        model=model,
        image=image,
        caption=text_prompt,
        box_threshold=box_threshold,
        text_threshold=text_threshold,
        device=device,
    )

    return {
        "boxes": boxes.tolist(),
        "scores": logits.tolist(),
        "phrases": phrases,
    }