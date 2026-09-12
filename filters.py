# -*- coding: utf-8 -*-
"""
Logika filtrowania i scoringu ofert samochodowych zgodnie z kryteriami:
- BMW Seria 3 (E30, E36, E46) oraz Seria 7 (E38)
- Nadwozie: Sedan, Coupe, Compact
- Budżet: max 6000 PLN
- Silnik > 1.8L
- Preferowana instalacja LPG i dobry stan mechaniczny
"""
import re
from dataclasses import dataclass, field
from typing import Optional

MAX_BUDGET_PLN = 6000
MIN_ENGINE_L = 1.8

MODEL_KEYWORDS = {
    "E30": ["e30"],
    "E36": ["e36"],
    "E46": ["e46"],
    "E38": ["e38"],
}

BODY_KEYWORDS = {
    "Sedan": ["sedan", "limuzyna"],
    "Coupe": ["coupe", "coupé", "kupe"],
    "Compact": ["compact", "kompakt"],
}

LPG_KEYWORDS = ["lpg", "gaz", "instalacja gazowa", "autogaz"]

GOOD_CONDITION_KEYWORDS = [
    "sprawny", "bezwypadkowy", "serwisowany", "zadbany", "bez rdzy",
    "bez korozji", "nowy rozrząd", "swieżo po przeglądzie", "świeżo po przeglądzie",
    "gotowy do jazdy", "bezawaryjny", "stan idealny", "wszystko działa",
]

BAD_CONDITION_KEYWORDS = [
    "do remontu", "uszkodzony", "powypadkowy", "silnik do naprawy",
    "nie odpala", "wymaga naprawy", "na części", "korozja", "rdza",
]

ENGINE_RE = re.compile(r"(\d[\.,]\d)\s*(?:l|dm3|litr)?", re.IGNORECASE)


@dataclass
class Listing:
    title: str
    price_pln: Optional[float]
    url: str
    image_url: Optional[str]
    description: str = ""
    source: str = ""
    location: str = ""

    # wyliczane
    model: Optional[str] = None
    body_type: Optional[str] = None
    engine_l: Optional[float] = None
    has_lpg: bool = False
    condition_score: int = 0
    total_score: float = field(default=0.0)

    def analyze(self):
        text = f"{self.title} {self.description}".lower()

        # model
        for model, kws in MODEL_KEYWORDS.items():
            if any(kw in text for kw in kws):
                self.model = model
                break

        # nadwozie
        for body, kws in BODY_KEYWORDS.items():
            if any(kw in text for kw in kws):
                self.body_type = body
                break

        # pojemność silnika - szukamy wzorców typu "2.0", "2,5", "1.9i"
        matches = ENGINE_RE.findall(text)
        candidates = []
        for m in matches:
            try:
                val = float(m.replace(",", "."))
                if 0.9 <= val <= 6.0:  # sensowny zakres pojemności silnika
                    candidates.append(val)
            except ValueError:
                continue
        if candidates:
            # bierzemy najbardziej prawdopodobną (najczęściej pierwszą sensowną)
            self.engine_l = max(candidates)

        # LPG
        self.has_lpg = any(kw in text for kw in LPG_KEYWORDS)

        # stan techniczny - prosty scoring
        self.condition_score = sum(1 for kw in GOOD_CONDITION_KEYWORDS if kw in text)
        self.condition_score -= sum(2 for kw in BAD_CONDITION_KEYWORDS if kw in text)

        self.total_score = self._compute_score()

    def _compute_score(self) -> float:
        score = 0.0
        if self.has_lpg:
            score += 5
        score += self.condition_score
        if self.price_pln is not None:
            # tańsze w ramach budżetu = lepiej, ale nie dominująco
            score += (MAX_BUDGET_PLN - self.price_pln) / MAX_BUDGET_PLN * 3
        if self.engine_l:
            # premiujemy silniki w rozsądnym przedziale 1.8-3.0L
            if 1.8 < self.engine_l <= 3.0:
                score += 2
        if self.model == "E38":
            score += 1  # rzadszy, bardziej pożądany model w tej cenie
        return round(score, 2)

    def passes_filters(self) -> bool:
        if self.model is None:
            return False
        if self.body_type is None:
            return False
        if self.price_pln is None or self.price_pln > MAX_BUDGET_PLN:
            return False
        if self.engine_l is None or self.engine_l <= MIN_ENGINE_L:
            return False
        if self.condition_score < 0:
            # wyraźne sygnały uszkodzeń / do remontu -> odrzucamy
            return False
        return True


def rank_listings(listings, top_n=30):
    valid = []
    for l in listings:
        l.analyze()
        if l.passes_filters():
            valid.append(l)
    valid.sort(key=lambda x: x.total_score, reverse=True)
    return valid[:top_n]
