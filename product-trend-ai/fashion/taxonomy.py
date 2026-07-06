# fashion/taxonomy.py

PRODUCT_TAXONOMY = {
    "top": [
        "t_shirt",
        "longsleeve",
        "shirt",
        "blouse",
        "tank_top",
        "crop_top",
        "polo",
        "bodysuit",
        "corset_top"
    ],
    "knitwear": [
        "jumper",
        "sweater",
        "cardigan",
        "knit_vest",
        "turtleneck",
        "knit_top"
    ],
    "sweatshirts": [
        "hoodie",
        "zip_hoodie",
        "sweatshirt"
    ],
    "bottom": [
        "jeans",
        "trousers",
        "wide_leg_trousers",
        "straight_trousers",
        "slim_trousers",
        "cargo_pants",
        "joggers",
        "leggings",
        "palazzo_pants",
        "culottes",
        "shorts",
        "bermuda_shorts"
    ],
    "skirt": [
        "mini_skirt",
        "midi_skirt",
        "maxi_skirt",
        "denim_skirt",
        "pleated_skirt",
        "pencil_skirt"
    ],
    "dress": [
        "mini_dress",
        "midi_dress",
        "maxi_dress",
        "shirt_dress",
        "slip_dress",
        "knit_dress",
        "bodycon_dress",
        "wrap_dress"
    ],
    "outerwear": [
        "blazer",
        "jacket",
        "bomber_jacket",
        "denim_jacket",
        "leather_jacket",
        "coat",
        "trench_coat",
        "puffer_jacket",
        "parka",
        "vest"
    ],
    "shoes": [
        "sneakers",
        "loafers",
        "boots",
        "ankle_boots",
        "sandals",
        "heels",
        "ballet_flats",
        "mules"
    ],
    "bags": [
        "shoulder_bag",
        "tote_bag",
        "crossbody_bag",
        "clutch",
        "backpack"
    ],
    "accessories": [
        "belt",
        "scarf",
        "hat",
        "cap",
        "sunglasses",
        "jewelry"
    ]
}


def format_taxonomy_for_prompt() -> str:
    lines = []
    for category, items in PRODUCT_TAXONOMY.items():
        lines.append(f"{category}: {', '.join(items)}")
    return "\n".join(lines)