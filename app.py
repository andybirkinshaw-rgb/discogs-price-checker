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
        # Currency fallback safe metrics if exchange arrays are momentarily busy
        if currency == "EUR": return float(amount) * 0.85
        if currency == "USD": return float(amount) * 0.79
        return float(amount)

st.title("🎵 Record Price Checker Pro")
st.caption("Streamlined Pricing Architecture Driven by Open Database Token Access")

# Step 1: Input Search
cat_input = st.text_input("Step 1: Enter Catalogue Number", placeholder="e.g. MCR1402 or PCD-17746")

if cat_input:
    # Memory State Management: Wipe out selection queues cleanly if a new search is executed
    if 'search_query' not in st.session_state or st.session_state.search_query != cat_input:
        st.session_state.search_query = cat_input
        st.session_state.releases = []
        st.session_state.selected_release_index = 0  

    if not st.session_state.releases:
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

    # Step 2: Selection Box with State Tracking
    if st.session_state.releases:
        st.subheader("Step 2: Choose Exact Pressing")
        
        display_options = []
        for r in st.session_state.releases:
            fmt = r.get('format', ['Unknown'])[0]
            label = r.get('label', ['Unknown'])[0]
            year = r.get('year', 'N/A')
            catno = r.get('catno', 'N/A')
            title = r.get('title', 'Unknown')
            display_options.append(f"[{fmt.upper()}] {title} — {label} ({year}) [Cat: {catno}]")

        # Fallback bounds check to protect switching between items safely
        if st.session_state.selected_release_index >= len(display_options):
            st.session_state.selected_release_index = 0

        selected_display = st.selectbox(
            "Select Version:", 
            options=display_options,
            index=st.session_state.selected_release_index,
            key="version_selector"
        )
        
        # Save exact dropdown choices straight into session memory logs
        current_index = display_options.index(selected_display)
        st.session_state.selected_release_index = current_index
        active_release = st.session_state.releases[current_index]

        # Step 3: Streamlined Pricing Framework
        rel_id = active_release['id']
        
        with st.spinner("Calculating live values..."):
            # Fetch base release metadata (This endpoint is completely unblocked and reliable)
            rel_url = f"https://api.discogs.com/releases/{rel_id}?token={TOKEN}"
            rel_req = requests.get(rel_url, headers=HEADERS).json()

        st.markdown("---")
        st.subheader("Step 3: Valuation Breakdown")

        col1, col2 = st.columns([1, 4])
        with col1:
            st.image(active_release.get('thumb', ''), width=80)
        with col2:
            st.markdown(f"### {active_release.get('title')}")
            st.markdown(f"**Format:** {', '.join(active_release.get('format', []))} | **Cat No:** {active_release.get('catno', 'N/A')}")

        # --- EXTRACT LIVE METRICS SAFELY FROM OPEN ENDPOINT ---
        total_for_sale = rel_req.get('num_for_sale', 0) if isinstance(rel_req, dict) else 0
        raw_lowest_price = rel_req.get('lowest_price', 0) if isinstance(rel_req, dict) else 0
        
        # Translate currency dynamically to British Pounds
        live_floor = to_gbp(raw_lowest_price, "USD")
        
        # Build logical estimates for spreads based directly off the true floor baseline anchor
        live_ceiling = live_floor * 2.2 if live_floor > 0 else 0.0

        # --- DYNAMIC INVENTORY CONDITION DISTRIBUTION MATRIX ---
        m_count, nm_count, vg_count = 0, 0, 0
        if total_for_sale == 1:
            nm_count = 1
        elif total_for_sale > 1:
            m_count = int(total_for_sale * 0.15) or 1
            nm_count = int(total_for_sale * 0.35) or 1
            vg_count = max(0, total_for_sale - m_count - nm_count)

        # --- THE CONDITION ADJUSTER INTERFACE ENGINE ---
        st.markdown("#### Condition Adjuster")
        selected_cond = st.selectbox("What is the condition of YOUR copy?", ["Mint (M)", "Near Mint (NM)", "Very Good Plus (VG+)", "Very Good (VG)"])

        # Multiplier scaling factors mapping value cleanly against condition thresholds
        mult = 1.0
        if "Mint" in selected_cond: mult = 1.45
        elif "Near Mint" in selected_cond: mult = 1.20
        elif "Very Good Plus" in selected_cond: mult = 1.0
        elif "Very Good" in selected_cond and "+" not in selected_cond: mult = 0.75

        # Live calculation engine using the true floor price anchor
        if live_floor > 0:
            rec_price = live_floor * mult
            note_str = f"Calculated dynamically by indexing the live market floor (£{live_floor:.2f}) against selection criteria multipliers."
        else:
            rec_price = 0.0
            note_str = "No active seller listings or floor value parameters found to scale valuation from."

        st.success(f"**Your Recommended Sell Price:** £{rec_price:.2f}")
        st.caption(note_str)

        # Dashboard layout components rendering panels clean and scannable
        left_col, right_col = st.columns(2)

        with left_col:
            st.markdown("##### Live Marketplace Spreads")
            st.write(f"🟢 **Cheapest Now:** " + (f"£{live_floor:.2f}" if live_floor > 0 else "None"))
            st.write(f"🔴 **Highest Estimated:** " + (f"£{live_ceiling:.2f}" if live_ceiling > 0 else "None"))
            st.markdown(f"**Total Listings Active:** `{total_for_sale}`")

        with right_col:
            st.markdown("##### Inventory Layout Distribution")
            st.text(f"• Mint Copies (Est): {m_count}")
            st.text(f"• Near Mint Copies (Est): {nm_count}")
            st.text(f"• VG+ or lower (Est): {vg_count}")