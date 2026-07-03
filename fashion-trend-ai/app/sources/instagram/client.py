from __future__ import annotations
from typing import Any
from apify_client import ApifyClient
from app.config import settings

class ApifyInstagramClient:
    def __init__(self):
        if not settings.apify_api_token:
            raise ValueError("APIFY_API_TOKEN is not set")
        self.client = ApifyClient(settings.apify_api_token)

    def get_posts_by_urls(self, urls: list[str], limit: int) -> list[dict[str, Any]]:
        run_input = {
            "directUrls": urls,
            "resultsLimit": limit,
            "resultsType": "posts",
            "dataDetailLevel": "full",
            "skipPinnedPosts": False,
            "addParentData": False,
        }
        run = self.client.actor("apify/instagram-scraper").call(run_input=run_input)
        dataset_id = run.default_dataset_id
        return list(self.client.dataset(dataset_id).iterate_items())