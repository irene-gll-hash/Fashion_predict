# fashion/attributes.py

COMMON_ATTRIBUTES = {
    "colors": [
        "black",
        "white",
        "grey",
        "beige",
        "brown",
        "navy",
        "blue",
        "light_blue",
        "red",
        "pink",
        "green",
        "yellow",
        "orange",
        "purple",
        "metallic",
        "multicolor"
    ],
    "patterns": [
        "solid",
        "striped",
        "checked",
        "floral",
        "animal_print",
        "polka_dot",
        "abstract",
        "logo",
        "graphic",
        "text_print"
    ],
    "style_tags": [
        "basic",
        "minimal",
        "office",
        "casual",
        "sporty",
        "evening",
        "streetwear",
        "romantic",
        "boho",
        "classic",
        "y2k",
        "old_money",
        "quiet_luxury",
        "utility",
        "preppy"
    ],
    "seasonality": [
        "spring",
        "summer",
        "autumn",
        "winter",
        "all_season"
    ]
}


CATEGORY_ATTRIBUTES = {
    "bottom": {
        "fit": [
            "skinny",
            "slim",
            "straight",
            "relaxed",
            "wide",
            "oversized"
        ],
        "rise": [
            "low_waist",
            "mid_waist",
            "high_waist"
        ],
        "length": [
            "mini",
            "knee_length",
            "cropped",
            "ankle_length",
            "full_length"
        ],
        "leg_shape": [
            "skinny",
            "straight",
            "wide",
            "flared",
            "tapered",
            "cargo",
            "palazzo"
        ],
        "details": [
            "pleats",
            "belt_loops",
            "drawstring",
            "pockets",
            "cargo_pockets",
            "slits",
            "cuffs"
        ]
    },
    "top": {
        "fit": [
            "tight",
            "regular",
            "relaxed",
            "oversized",
            "cropped"
        ],
        "sleeve_length": [
            "sleeveless",
            "short_sleeve",
            "three_quarter_sleeve",
            "long_sleeve"
        ],
        "neckline": [
            "crew_neck",
            "v_neck",
            "round_neck",
            "square_neck",
            "halter",
            "off_shoulder",
            "collared",
            "turtleneck"
        ],
        "details": [
            "buttons",
            "zipper",
            "ruffles",
            "lace",
            "ribbed",
            "cut_out",
            "embroidery",
            "logo"
        ]
    },
    "knitwear": {
        "fit": [
            "regular",
            "relaxed",
            "oversized",
            "cropped"
        ],
        "neckline": [
            "crew_neck",
            "v_neck",
            "round_neck",
            "turtleneck",
            "polo_collar",
            "cardigan_neck"
        ],
        "knit_type": [
            "fine_knit",
            "chunky_knit",
            "ribbed_knit",
            "openwork_knit"
        ],
        "details": [
            "buttons",
            "zipper",
            "ribbed_cuffs",
            "cable_knit",
            "pockets"
        ]
    },
    "dress": {
        "length": [
            "mini",
            "midi",
            "maxi"
        ],
        "silhouette": [
            "straight",
            "a_line",
            "bodycon",
            "wrap",
            "slip",
            "shirt_dress",
            "fit_and_flare"
        ],
        "sleeve_length": [
            "sleeveless",
            "short_sleeve",
            "long_sleeve"
        ],
        "neckline": [
            "v_neck",
            "round_neck",
            "square_neck",
            "halter",
            "off_shoulder",
            "collared"
        ]
    },
    "outerwear": {
        "length": [
            "cropped",
            "hip_length",
            "mid_length",
            "long"
        ],
        "fit": [
            "regular",
            "relaxed",
            "oversized",
            "tailored"
        ],
        "closure": [
            "buttons",
            "zipper",
            "belted",
            "open_front",
            "double_breasted"
        ],
        "details": [
            "lapels",
            "hood",
            "belt",
            "pockets",
            "padding",
            "quilting"
        ]
    }
}


def format_attributes_for_prompt() -> str:
    parts = []

    parts.append("Common attributes:")
    for key, values in COMMON_ATTRIBUTES.items():
        parts.append(f"- {key}: {', '.join(values)}")

    parts.append("\nCategory-specific attributes:")
    for category, attrs in CATEGORY_ATTRIBUTES.items():
        parts.append(f"\n{category}:")
        for attr_name, values in attrs.items():
            parts.append(f"- {attr_name}: {', '.join(values)}")

    return "\n".join(parts)