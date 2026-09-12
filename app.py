# -*- coding: utf-8 -*-
"""
Agregator i analityk ogłoszeń BMW (E30/E36/E46/E38) z OLX i Otomoto.
Odświeża dane co 5 minut, filtruje wg kryteriów i pokazuje TOP 30 ofert.

Uruchomienie:
    pip install -r requirements.txt
    streamlit run app.py
"""
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from scraper_olx import fetch_olx_listings
from scraper_otomoto import fetch_otomoto_listings
from facebook_helper import build_marketplace_links
from filters import rank_listings, MAX_BUDGET_PLN, MIN_ENGINE_L

REFRESH_INTERVAL_MS = 5 * 60 * 1000  # 5 minut

st.set_page_config(
    page_title="BMW Agregator Ofert",
    page_icon="🚗",
    layout="wide",
)

# Auto-odświeżanie co 5 minut
st_autorefresh(interval=REFRESH_INTERVAL_MS, key="auto_refresh")


@st.cache_data(ttl=300, show_spinner=False)
def load_all_listings():
    olx = []
    otomoto = []
    errors = []
    try:
        olx = fetch_olx_listings()
    except Exception as e:
        errors.append(f"OLX: {e}")
    try:
        otomoto = fetch_otomoto_listings()
    except Exception as e:
        errors.append(f"Otomoto: {e}")
    return olx + otomoto, errors


def render_header():
    st.title("🚗 Agregator ofert: BMW E30 / E36 / E46 / E38")
    st.caption(
        f"Budżet do {MAX_BUDGET_PLN} PLN · silnik > {MIN_ENGINE_L}L · "
        "nadwozie Sedan/Coupe/Compact · priorytet: pełna sprawność mechaniczna i LPG"
    )
    st.caption("Dane odświeżają się automatycznie co 5 minut. Źródła: OLX, Otomoto.")


def render_facebook_note():
    with st.expander("ℹ️ Facebook Marketplace – dlaczego nie ma automatycznego pobierania?"):
        st.write(
            "Facebook Marketplace nie udostępnia publicznego API i aktywnie blokuje "
            "zautomatyzowane pobieranie ofert (wymaga zalogowania, silne zabezpieczenia "
            "antybotowe). Nie da się tego zrobić rzetelnie bez łamania zabezpieczeń serwisu, "
            "dlatego zamiast tego przygotowałem gotowe linki wyszukiwania – wystarczy kliknąć."
        )
        for label, link in build_marketplace_links(MAX_BUDGET_PLN):
            st.markdown(f"- [{label}]({link})")


def render_listing_card(listing, col):
    with col:
        with st.container(border=True):
            if listing.image_url:
                st.image(listing.image_url, use_container_width=True)
            else:
                st.write("📷 *Brak zdjęcia*")

            st.markdown(f"**{listing.title}**")

            badges = []
            if listing.model:
                badges.append(f"`{listing.model}`")
            if listing.body_type:
                badges.append(f"`{listing.body_type}`")
            if listing.has_lpg:
                badges.append("`⛽ LPG`")
            if badges:
                st.markdown(" ".join(badges))

            price_str = f"{listing.price_pln:.0f} PLN" if listing.price_pln else "brak ceny"
            st.write(f"💰 **{price_str}**  ·  🔧 silnik: {listing.engine_l or '?'} L")
            if listing.location:
                st.write(f"📍 {listing.location}")
            st.write(f"🏷️ Źródło: {listing.source}  ·  ⭐ Wynik dopasowania: {listing.total_score}")

            if listing.description:
                summary = listing.description.strip().replace("\n", " ")
                if len(summary) > 160:
                    summary = summary[:160].rsplit(" ", 1)[0] + "…"
                st.caption(summary)

            st.link_button("Zobacz ogłoszenie ➜", listing.url, use_container_width=True)


def main():
    render_header()
    render_facebook_note()

    with st.spinner("Pobieranie i analiza ofert z OLX oraz Otomoto..."):
        raw_listings, errors = load_all_listings()
        top_listings = rank_listings(raw_listings, top_n=30)

    if errors:
        for err in errors:
            st.warning(
                f"Nie udało się pobrać danych ({err}). Serwis mógł zmienić "
                "strukturę strony lub tymczasowo zablokować zapytanie."
            )

    st.subheader(f"Znaleziono {len(top_listings)} ofert spełniających kryteria (z {len(raw_listings)} przeanalizowanych)")

    if not top_listings:
        st.info(
            "Brak ofert spełniających wszystkie kryteria w tej chwili. "
            "Spróbuj ponownie za chwilę – lista odświeża się co 5 minut, "
            "albo sprawdź linki do Facebook Marketplace powyżej."
        )
        return

    cols_per_row = 3
    rows = [top_listings[i:i + cols_per_row] for i in range(0, len(top_listings), cols_per_row)]
    for row in rows:
        cols = st.columns(cols_per_row)
        for listing, col in zip(row, cols):
            render_listing_card(listing, col)


if __name__ == "__main__":
    main()
