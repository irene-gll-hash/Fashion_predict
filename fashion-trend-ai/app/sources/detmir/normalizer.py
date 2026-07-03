from __future__ import annotations
from app.sources.common.media_asset import MediaAsset
from app.sources.detmir.schemas import DetmirProduct
def product_to_media_assets(
    product: DetmirProduct,
    *,
    profile: str = "kids_goods",
) -> list[MediaAsset]:
    assets: list[MediaAsset] = []
    for index, image_url in enumerate(product.image_urls, start=1):
        assets.append(
            MediaAsset(
                asset_id=f"{product.product_id}_image_{index:03d}",
                parent_id=product.product_id,
                source="detmir",
                source_type="product_catalog",
                profile=profile,
                media_type="image",
                url=image_url,
                context={
                    "product_url": product.url,
                    "title": product.title,
                    "description": product.description,
                    "brand": product.brand,
                    "category_path": product.category_path,
                    "price": product.price,
                    "currency": product.currency,
                    "age_group": product.age_group,
                    "attributes": product.attributes,
                },
            )
        )
    return assets
