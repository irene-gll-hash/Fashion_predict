# app/sources/lamoda/normalizer.py

from app.sources.lamoda.schemas import Product


def products_to_media_assets(
    products: list[Product],
    profile: str,
) -> list[dict]:
    assets = []

    for product in products:
        parent_id = product.product_url

        for index, image_url in enumerate(product.image_urls):
            asset = {
                "asset_id": f"lamoda_{abs(hash(product.product_url))}_{index}",
                "parent_id": parent_id,
                "source": "lamoda",
                "source_type": "product_catalog",
                "profile": profile,
                "media_type": "image",
                "url": image_url,
                "context": {
                    "product_url": product.product_url,
                    "title": product.title,
                    "description": product.description,
                    "brand": product.brand,
                    "price": product.price,
                    "old_price": product.old_price,
                    "currency": product.currency,
                    "source_category": product.source_category,
                    "source_category_url": product.source_category_url,
                    "brand_url": product.brand_url,
                    "brand_category": product.brand_category,
                    "brand_category_url": product.brand_category_url,
                    "category_path": product.category_path,
                    "attributes": product.attributes,
                },
            }

            assets.append(asset)

    return assets