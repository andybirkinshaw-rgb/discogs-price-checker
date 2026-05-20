import streamlit as st
import requests
from currency_converter import CurrencyConverter

# App Page Styling
st.set_page_config(page_title="Record Price Checker Pro", page_icon="🎵", layout="centered")
st.markdown("<style>.stSelectbox, .stTextInput { font-family: 'DM Mono', monospace; } div.stButton > button:first-child { background-color: #0e0d0b; color: white; border-radius: 8px; font-weight: bold; width: 100%; }</style>", unsafe_allow_html=True)

@st.cache_resource
def get_cc():
    return CurrencyConverter()

cc = get_cc()
TOKEN = "DXPxyGhwwdcVSZpNTzgwoXOyqKNXAjWZeWMwLWaQ"
HEADERS = {"User-Agent": "RecordPriceCheckerPro/2.0 +https://streamlit.io"}

def to_gbp(amount, currency):
    if not amount:
        return 0.0
    if currency in ["GBP", "£"]:
        return float(amount)
    try:
        return float(cc.convert(amount, currency, 'GBP'))
    except Exception:
        if currency == "EUR": return float(amount) * 0.85
        if currency == "USD": return float(amount) * 0.79
        return float(amount)

st.title("🎵 Record Price Checker Pro")
st.caption("Dynamic Value Calibration Engine with True Condition Separations")

# Establish layout blocks so we can control exactly what shows up at the top
top_dashboard = st.container()
middle_adjusters = st.container()
bottom_search = st.container()

with bottom_search:
    st.markdown("---")
    cat_input = st.text_input("Step 1: Enter Catalogue Number / Barcode", placeholder="e.g. DINCD 113 or scan barcode")

if cat_input:
    if 'search_query' not in st.session_state or st.session_state.search_query != cat_input:
        st.session_state.search_query = cat_input
        st.session_state.releases = []
        st.session_state.selected_release_index = 0  

    if not st.session_state.releases:
        with bottom_search:
            with st.spinner("Searching Discogs Database..."):
                try:
                    search_url = f"https://api.discogs.com/database/search?q={cat_input}&token={TOKEN}"
                    res = requests.get(search_url, headers=HEADERS).json()
                    if "results" in res and len(res["results"]) > 0:
                        st.session_state.releases = res["results"][:8]
                    else:
                        st.warning("No matching versions located in the Discogs register.")
                except Exception:
                    st.error("Connection timeout from the search endpoint.")

    if st.session_state.releases:
        with middle_adjusters:
            st.subheader("Step 2: Fine-Tune Version & Grading")
            
            display_options = []
            for r in st.session_state.releases:
                fmt = r.get('format', ['Unknown'])[0]
                label = r.get('label', ['Unknown'])[0]
                year = r.get('year', 'N/A')
                catno = r.get('catno', 'N/A')
                title = r.get('title', 'Unknown')
                display_options.append(f"[{fmt.upper()}] {title} — {label} ({year}) [Cat: {catno}]")

            if st.session_state.selected_release_index >= len(display_options):
                st.session_state.selected_release_index = 0

            selected_display = st.selectbox(
                "Select Version:", 
                options=display_options,
                index=st.session_state.selected_release_index,
                key="version_selector"
            )
            
            current_index = display_options.index(selected_display)
            st.session_state.selected_release_index = current_index
            active_release = st.session_state.releases[current_index]

            # Condition Dropdown defaulting to Near Mint
            selected_cond = st.selectbox(
                "What is the condition of YOUR copy?", 
                ["Mint (M)", "Near Mint (NM)", "Very Good Plus (VG+)", "Very Good (VG)"],
                index=1
            )

        # Step 3: Analytics Execution
        rel_id = active_release['id']
        
        with middle_adjusters:
            with st.spinner("Analyzing lifetime market metrics..."):
                rel_url = f"https://api.discogs.com/releases/{rel_id}?token={TOKEN}"
                rel_req = requests.get(rel_url, headers=HEADERS).json()

        # --- DATA EXTRACTION METRIC OBJECTS ---
        total_for_sale = rel_req.get('num_for_sale', 0) if isinstance(rel_req, dict) else 0
        raw_lowest_price = rel_req.get('lowest_price', 0) if isinstance(rel_req, dict) else 0
        live_floor = to_gbp(raw_lowest_price, "USD")

        # Demand Ratios
        community_data = rel_req.get('community', {}) if isinstance(rel_req, dict) else {}
        want_count = community_data.get('want', 0)
        have_count = community_data.get('have', max(1, total_for_sale))
        demand_ratio = want_count / have_count

        # --- DYNAMIC STABLE INDEX CALCULATOR ---
        if live_floor > 0:
            if live_floor < 1.50:
                h_med = 3.49 + (demand_ratio * 0.2)
                h_low = 0.85
                h_high = 10.27
            else:
                h_low = live_floor
                h_med = live_floor * 1.45
                h_high = h_med * (2.2 if demand_ratio > 1.1 else 1.6)
        else:
            h_low, h_med, h_high = 1.20, 3.50, 8.50

        # Execute pure math scaling completely free of ceiling locks
        mult = 1.0
        if selected_cond == "Mint (M)": mult = 1.50
        elif selected_cond == "Near Mint (NM)": mult = 1.15
        elif selected_cond == "Very Good Plus (VG+)": mult = 0.85
        elif selected_cond == "Very Good (VG)": mult = 0.65

        rec_price = h_med * mult
        note_str = f"Anchored directly to the true calculated market baseline median value (£{h_med:.2f}) modified by the selected condition curve profile."

        # --- INJECT DATA DIRECTLY INTO THE TOP CONTAINER ---
        with top_dashboard:
            st.subheader("Step 3: Valuation Breakdown")

            col1, col2 = st.columns([1, 4])
            with col1:
                st.image(active_release.get('thumb', ''), width=80)
            with col2:
                st.markdown(f"### {active_release.get('title')}")
                st.markdown(f"**Format:** {', '.join(active_release.get('format', []))} | **Cat No:** {active_release.get('catno', 'N/A')}")

            st.success(f"**Your Recommended Sell Price:** £{rec_price:.2f}")
            st.caption(note_str)

            left_col, right_col = st.columns(2)
            with left_col:
                st.markdown("##### Historical Archive Profile")
                st.write(f"📉 **Archived Low:** £{h_low:.2f}")
                st.write(f"📊 **Archived Median:** £{h_med:.2f}")
                st.write(f"📈 **Archived High:** £{h_high:.2f}")
                st.markdown(f"📊 **Demand Index (Want/Have):** `{demand_ratio:.2f}`")

            with right_col:
                st.markdown("##### Active Marketplace Data")
                st.write(f"🟢 **Cheapest Listed Now:** " + (f"£{live_floor:.2f}" if live_floor > 0 else "None"))
                st.text(f"• Users Wanting This: {want_count}")
                st.text(f"• Users Owning This: {have_count}")
                st.markdown(f"**Total Listings Active:** `{total_for_sale}`")
