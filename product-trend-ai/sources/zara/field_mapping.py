from __future__ import annotations


ZARA_REQUIRED_FIELDS = [
    "id",
    "reference",
    "brand",
    "name",
    "price",
    "mainImage",
    "colorsSizesImagesJSON",
    "productPage",
]


ZARA_OPTIONAL_FIELDS = [
    "displayReference",
    "description",
    "colors",
    "sizes",
    "oldPrice",
    "displayDiscountPercentage",
    "discountPercentage",
    "discountLabel",
    "isOnSale",
    "category",
    "keyword",
    "availability",
    "state",
    "firstVisibleDate",
    "detailedComposition",
    "productCare",
    "origin",
    "website",
    "categoryPage",
]


ZARA_COLOR_VARIANT_FIELDS = [
    "id",
    "displayReference",
    "hexCode",
    "productId",
    "name",
    "reference",
    "stylingId",
    "xmedia",
    "price",
    "oldPrice",
    "displayDiscountPercentage",
    "discountPercentage",
    "discountLabel",
    "availability",
    "sizes",
    "description",
    "rawDescription",
    "isOnSale",
    "productPageSelectedColor",
    "pdpMedia",
]