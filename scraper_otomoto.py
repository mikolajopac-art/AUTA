# -*- coding: utf-8 -*-
"""
Scraper Otomoto.pl dla ogłoszeń BMW.
Otomoto (podobnie jak OLX, ta sama grupa OLX Group) też korzysta z Next.js
i osadza dane w <script id="__NEXT_DATA__">. Struktura JSON-a może się
zmieniać wraz z aktualizacjami serwisu - w razie awarii sprawdź ścieżki kluczy.
"""
import json
import time
import requests
from typing import List
from filters import Listing

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pl-PL,pl;q=0.9",
}

# Otomoto pozwala filtrować cenę od razu w URL (search[filter_float_price:to])
SEARCH_MODELS = ["e30", "e36", "e46", "e38"]
BASE_URL = (
    "https://www.otomoto.pl/osobowe/bmw/seria-3?"
    "search%5Bfilter_float_price%3Ato%5D=6000&search%5Bqr%5D={model}"
)
REQUEST_DELAY_SEC = 2


def _safe_get(url: str, timeout: int = 15):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        if resp.status_code == 200:
            return resp
    except requests.RequestException:
        return None
    return None


def _extract_next_data(html: str):
    marker = 'id="__NEXT_DATA__"'
    idx = html.find(marker)
    if idx == -1:
        return None
    start = html.find(">", idx) + 1
    end = html.find("</script>", start)
    if start == -1 or end == -1:
        return None
    raw_json = html[start:end]
    try:
        return json.loads(raw_json)
    except json.JSONDecodeError:
        return None


def _dig_ads(data: dict):
    """Otomoto zagnieżdża dane inaczej niż OLX - próbujemy kilku ścieżek."""
    candidates = []
    try:
        candidates = (
            data.get("props", {})
            .get("pageProps", {})
            .get("urqlState", {})
        )
        # urqlState to słownik cache'y GraphQL - trzeba przeszukać wartości
        for _, cache_entry in candidates.items():
            try:
                parsed = json.loads(cache_entry.get("data", "{}"))
                edges = parsed.get("advertSearch", {}).get("edges", [])
                if edges:
                    return [e.get("node", {}) for e in edges]
            except Exception:
                continue
    except Exception:
        pass
    return []


def _parse_listings_from_ads(ads) -> List[Listing]:
    listings = []
    for ad in ads:
        try:
            title = ad.get("title", "")
            url = ad.get("url", "")
            price_obj = ad.get("price", {}) or {}
            price_pln = None
            amount = price_obj.get("amount") or price_obj.get("value")
            if amount is not None:
                price_pln = float(amount)

            images = ad.get("images", []) or []
            image_url = images[0].get("url") if images else None

            location = ""
            loc_obj = ad.get("location", {})
            if isinstance(loc_obj, dict):
                location = loc_obj.get("city", "") or ""

            description = ad.get("description", "") or ""

            listings.append(
                Listing(
                    title=title,
                    price_pln=price_pln,
                    url=url,
                    image_url=image_url,
                    description=description,
                    source="Otomoto",
                    location=location,
                )
            )
        except Exception:
            continue
    return listings


def fetch_otomoto_listings() -> List[Listing]:
    all_listings = []
    for model in SEARCH_MODELS:
        url = BASE_URL.format(model=model)
        resp = _safe_get(url)
        if resp is None:
            continue
        data = _extract_next_data(resp.text)
        if data is None:
            continue
        ads = _dig_ads(data)
        all_listings.extend(_parse_listings_from_ads(ads))
        time.sleep(REQUEST_DELAY_SEC)
    return all_listings
