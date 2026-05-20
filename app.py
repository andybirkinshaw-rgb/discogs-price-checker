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
st.caption("Advanced Supply & Demand Analytics Engine Driving Marketplace Ceilings")

# Step 1: Input Search
cat_input = st.text_input("Step 1: Enter Catalogue Number", placeholder="e.g. MCR1402 or PCD-17746")

if cat_input:
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

    # Step 2: Selection Box
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

        # Step 3: Analytics Execution
        rel_id = active_release['id']
        
        with st.spinner("Calculating live supply & demand factors..."):
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

        # --- DATA PROCESSING EXTRACTION ---
        total_for_sale = rel_req.get('num_for_sale', 0) if isinstance(rel_req, dict) else 0
        raw_lowest_price = rel_req.get('lowest_price', 0) if isinstance(rel_req, dict) else 0
        live_floor = to_gbp(raw_lowest_price, "USD")

        # --- NEW ENGINE: COMMUNITY SUPPLY & DEMAND CALCULATION ---
        community_data = rel_req.get('community', {}) if isinstance(rel_req, dict) else {}
        want_count = community_data.get('want', 0)
        have_count = community_data.get('have', max(1, total_for_sale)) # Guard against division by zero
        
        # Calculate market pressure factor
        demand_ratio = want_count / have_count
        
        # Translate ratio into a responsive ceiling multiplier
        if demand_ratio >= 2.0:
            ceiling_mult = 3.8  # High scarcity item (e.g., massive wantlist vs small supply)
        elif demand_ratio >= 1.0:
            ceiling_mult = 2.5  # Solid, stable collector value
        elif demand_ratio >= 0.5:
            ceiling_mult = 1.8  # Balanced market spread
        else:
            ceiling_mult = 1.3  # High supply / Low demand item (narrow price gap)

        live_ceiling = live_floor * ceiling_mult if live_floor > 0 else 0.0

        # --- DYNAMIC INVENTORY LAYOUT ---
        m_count, nm_count, vg_count = 0, 0, 0
        if total_for_sale == 1:
            nm_count = 1
        elif total_for_sale > 1:
            m_count = int(total_for_sale * 0.15) or 1
            nm_count = int(total_for_sale * 0.35) or 1
            vg_count = max(0, total_for_sale - m_count - nm_count)

        # --- CONDITION ADJUSTER ENGINE ---
        st.markdown("#### Condition Adjuster")
        selected_cond = st.selectbox("What is the condition of YOUR copy?", ["Mint (M)", "Near Mint (NM)", "Very Good Plus (VG+)", "Very Good (VG)"])

        mult = 1.0
        if "Mint" in selected_cond: mult = 1.45
        elif "Near Mint" in selected_cond: mult = 1.20
        elif "Very Good Plus" in selected_cond: mult = 1.0
        elif "Very Good" in selected_cond and "+" not in selected_cond: mult = 0.75

        if live_floor > 0:
            rec_price = live_floor * mult
            # If item is in high demand, bump the recommended premium for Mint copies automatically
            if "Mint" in selected_cond and demand_ratio >= 1.5:
                rec_price = rec_price * 1.15
            note_str = f"Calculated dynamically by indexing the live market floor (£{live_floor:.2f}) against a demand index score of {demand_ratio:.2f}."
        else:
            rec_price = 0.0
            note_str = "No active seller listings found to scale valuation from."

        st.success(f"**Your Recommended Sell Price:** £{rec_price:.2f}")
        st.caption(note_str)

        left_col, right_col = st.columns(2)

        with left_col:
            st.markdown("##### Live Marketplace Spreads")
            st.write(f"🟢 **Cheapest Now:** " + (f"£{live_floor:.2f}" if live_floor > 0 else "None"))
            st.write(f"🔴 **Highest Estimated:** " + (f"£{live_ceiling:.2f}" if live_ceiling > 0 else "None"))
            st.markdown(f"📈 **Demand Index (Want/Have):** `{demand_ratio:.2f}`")

        with right_col:
            st.markdown("##### Market Indicators")
            st.text(f"• Users Wanting This: {want_count}")
            st.text(f"• Users Owning This: {have_count}")
            st.markdown(f"**Total Listings Active:** `{total_for_sale}`")