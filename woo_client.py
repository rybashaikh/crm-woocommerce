import os

import requests

import mock_data


def use_mock():
    return os.getenv("USE_MOCK", "true").lower() == "true"


def fetch_all(endpoint):
    """Fetch every record from a WooCommerce endpoint ('customers' or 'orders'), handling pagination."""
    if use_mock():
        return mock_data.CUSTOMERS if endpoint == "customers" else mock_data.ORDERS

    base = os.getenv("WOO_BASE_URL", "").rstrip("/")
    auth = (os.getenv("WOO_CONSUMER_KEY"), os.getenv("WOO_CONSUMER_SECRET"))
    results, page = [], 1
    while True:
        resp = requests.get(
            f"{base}/wp-json/wc/v3/{endpoint}",
            auth=auth,
            params={"per_page": 100, "page": page},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        results.extend(data)
        if len(data) < 100:
            break
        page += 1
    return results