# BMW Agregator Ofert (E30 / E36 / E46 / E38)

Aplikacja Streamlit, która pobiera ogłoszenia z OLX i Otomoto, filtruje je wg
kryteriów i pokazuje TOP 30 najlepiej dopasowanych ofert w siatce.

## Uruchomienie

```bash
pip install -r requirements.txt
streamlit run app.py
```

Aplikacja otworzy się w przeglądarce pod `http://localhost:8501`.

## Kryteria filtrowania (edytowalne w `filters.py`)

- Model: BMW E30, E36, E46 lub E38
- Nadwozie: Sedan, Coupe lub Compact
- Cena: maksymalnie 6000 PLN
- Silnik: powyżej 1.8L
- Priorytet: pełna sprawność mechaniczna, instalacja LPG

## Odświeżanie

Lista odświeża się automatycznie co 5 minut (`streamlit-autorefresh`), a wyniki
scrapowania są cache'owane na 300 sekund (`st.cache_data(ttl=300)`), żeby nie
odpytywać serwisów przy każdym renderze strony.

## Ważne ograniczenia, o których trzeba wiedzieć

1. **OLX i Otomoto**: scraper korzysta z danych JSON osadzonych w kodzie
   strony (`__NEXT_DATA__`). To nieoficjalna metoda — jeśli serwisy zmienią
   strukturę strony, parsowanie może przestać działać i trzeba będzie
   zaktualizować ścieżki kluczy w `scraper_olx.py` / `scraper_otomoto.py`.
2. **Facebook Marketplace**: nie jest scrapowany automatycznie. FB wymaga
   zalogowanej sesji i aktywnie blokuje boty — nie da się tego zrobić w sposób
   stabilny i zgodny z zasadami. Aplikacja zamiast tego generuje gotowe linki
   wyszukiwania z filtrami (zakładka "ℹ️ Facebook Marketplace" w interfejsie).
3. **Wykrywanie parametrów** (model, nadwozie, pojemność silnika, LPG, stan
   techniczny) odbywa się przez dopasowywanie słów kluczowych w tytule i
   opisie ogłoszenia — nie jest to analiza w 100% niezawodna, bo zależy od
   tego, co sprzedający napisał w treści.
4. Używaj odpowiedzialnie — throttling requestów jest wbudowany
   (`REQUEST_DELAY_SEC`), ale intensywne, ciągłe odpytywanie serwisów może
   naruszać ich regulaminy.

## Struktura projektu

```
app.py                 - główna aplikacja Streamlit / UI
filters.py             - logika filtrowania i scoringu ofert
scraper_olx.py         - pobieranie ofert z OLX
scraper_otomoto.py     - pobieranie ofert z Otomoto
facebook_helper.py     - generator linków do FB Marketplace
requirements.txt       - zależności
```
