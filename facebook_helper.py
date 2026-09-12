# -*- coding: utf-8 -*-
"""
Facebook Marketplace NIE udostępnia publicznego API i aktywnie blokuje
automatyczne pobieranie danych (wymaga zalogowanej sesji, renderuje treść
przez JS, stosuje zaawansowaną detekcję botów). Rzetelny, stabilny scraper
nie jest tu technicznie wykonalny bez łamania zabezpieczeń serwisu.

Zamiast tego generujemy gotowe linki wyszukiwania z filtrami, które
użytkownik może otworzyć ręcznie i przejrzeć jednym kliknięciem.
"""
from urllib.parse import urlencode

BASE_URL = "https://www.facebook.com/marketplace/search/"

QUERIES = ["BMW E30", "BMW E36", "BMW E46", "BMW E38"]


def build_marketplace_links(max_price=6000):
    links = []
    for q in QUERIES:
        params = {
            "query": q,
            "maxPrice": max_price,
            "vehicleType": "car_truck",
        }
        links.append((q, f"{BASE_URL}?{urlencode(params)}"))
    return links
