# -*- coding: utf-8 -*-
"""
Scraper OLX.pl dla ogłoszeń BMW.
OLX renderuje wyniki wyszukiwania w Next.js - dane json znajdują się
w tagu <script id="__NEXT_DATA__">. Jeśli struktura strony się zmieni,
funkcja _parse_next_data przestanie działać i trzeba będzie zaktualizować
ścieżki kluczy w JSON-ie.
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

SEARCH_QUERIES = ["bmw e30", "bmw e36", "bmw e46", "bmw e38"]
BASE_URL = "https://www.olx.pl/motoryzacja/samochody/q-{query}/"
REQUEST_DELAY_SEC = 2  # żeby nie bombardować serwera requestami


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


def _parse_listings_from_next_data(data: dict) -> List[Listing]:
    listings = []
    try:
        ads = (
            data.get("props", {})
            .get("pageProps", {})
            .get("data", {})
            .get("listing", {})
            .get("ads", [])
        )
    except AttributeError:
        ads = []

    for ad in ads:
        try:
            title = ad.get("title", "")
            url = ad.get("url", "")
            description = ad.get("description", "") or ""
            price_info = ad.get("params", [])
            price_pln = None
            for p in price_info:
                if p.get("key") == "price":
                    val = p.get("value", {}).get("value")
                    if val is not None:
                        price_pln = float(val)
            if price_pln is None:
                price_pln = ad.get("price", {}).get("regularPrice", {}).get("value")

            photos = ad.get("photos", [])
            image_url = None
            if photos:
                link_tpl = photos[0].get("link", "")
                image_url = link_tpl.replace("{width}", "400").replace("{height}", "300") if link_tpl else None

            location = ad.get("location", {}).get("city", {}).get("name", "")

            listings.append(
                Listing(
                    title=title,
                    price_pln=price_pln,
                    url=url,
                    image_url=image_url,
                    description=description,
                    source="OLX",
                    location=location,
                )
            )
        except Exception:
            continue
    return listings


def fetch_olx_listings() -> List[Listing]:
    all_listings = []
    for query in SEARCH_QUERIES:
        url = BASE_URL.format(query=query.replace(" ", "-"))
        resp = _safe_get(url)
        if resp is None:
            continue
        data = _extract_next_data(resp.text)
        if data is None:
            continue
        all_listings.extend(_parse_listings_from_next_data(data))
        time.sleep(REQUEST_DELAY_SEC)
    return all_listings
