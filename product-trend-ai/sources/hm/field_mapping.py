from __future__ import annotations

HM_REQUIRED_FIELDS = [
    "id",
    "productName",
    "brandName",
    "productUrl",
    "price",
    "stockState",
    "colorName",
    "imageProductSrc",
]

HM_OPTIONAL_FIELDS = [
    "trackingId",
    "formattedPrice",
    "priceMin",
    "priceMax",
    "isComingSoon",
    "isOnline",
    "isNewProduct",
    "colorCode",
    "swatchColorNames",
    "swatchColorCodes",
    "allSizes",
    "availableSizes",
    "outOfStockSizes",
    "sizesCount",
    "imageModelSrc",
    "galleryImages",
    "mainCatCode",
    "searchQuery",
    "locale",
    "pageNumber",
]

HM_ALLOWED_MAIN_CATEGORY_PREFIXES = [
    "ladies_",
]