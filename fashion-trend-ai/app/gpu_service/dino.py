import torch
import numpy as np
from external.GroundingDINO.groundingdino.util.inference import predict

def load_model(device="cuda"):
    from external.GroundingDINO.groundingdino.models import build_model
    from external.GroundingDINO.groundingdino.util.slconfig import SLConfig
    from external.GroundingDINO.groundingdino.util.utils import clean_state_dict

    config_path = "external/GroundingDINO/groundingdino/config/GroundingDINO_SwinT_OGC.py"
    checkpoint_path = "external/GroundingDINO/weights/groundingdino_swint_ogc.pth"

    args = SLConfig.fromfile(config_path)
    model = build_model(args)

    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    model.load_state_dict(clean_state_dict(checkpoint["model"]), strict=False)

    model = model.to(device)
    return model


def detect_image(
    model,
    image,
    device,
    text_prompt,
    box_threshold=0.35,
    text_threshold=0.25,
    nms_iou_threshold=0.5
):

    boxes, logits, phrases = predict(
        model=model,
        image=image,
        caption=text_prompt,
        box_threshold=box_threshold,
        text_threshold=text_threshold,
        device=device
    )

    return {
        "boxes": boxes.tolist(),
        "scores": logits.tolist(),
        "phrases": phrases
    }