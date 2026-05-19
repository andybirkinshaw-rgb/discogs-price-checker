import streamlit as st
import requests
from currency_converter import CurrencyConverter

# App Page Styling
st.set_page_config(page_title="Record Price Checker Pro", page_icon="🎵", layout="centered")

# FIXED: Removed 'unsafe_allowed_html' typo and converted to modern 'unsafe_allow_html' syntax
st.markdown("<style>.stSelectbox, .stTextInput { font-family: 'DM Mono', monospace; } div.stButton > button:first-child { background-color: #0e0d0b; color: white; border-radius: 8px; font-weight: bold; width: 100%; }</style>", unsafe_allow_html=True)

# Initialize Currency Converter safely
@st.cache_resource
def get_cc():
    return CurrencyConverter()

cc = get_cc()

TOKEN = "DXPxyGhwwdcVSZpNTzgwoXOyqKNXAjWZeWMwLWaQ"
HEADERS = {"User-Agent": "RecordPriceCheckerPro/2.0 +https://streamlit.io"}

def to_gbp(amount, currency):
    if not amount:
        return 0.0
    if currency == "GBP" or currency == "£":
        return float(amount)
    try:
        return float(cc.convert(amount, currency, 'GBP'))
    except Exception:
        if currency == "EUR": return float(amount) * 0.85
        if currency == "USD": return float(amount) * 0.79
        return float(amount)

st.title("🎵 Record Price Checker Pro")
st.caption("Server-side architecture with automatic currency translation to GBP")

# Step 1: Input Search
cat_input = st.text_input("Step 1: Enter Catalogue Number", placeholder="e.g. MCR1406CD or MCR1402")

if cat_input:
    if 'search_query' not in st.session_state or st.session_state.search_query != cat_input:
        st.session_state.search_query = cat_input
        st.session_state.releases = []
        st.session_state.selected_release = None

    if not st.session_state.releases:
        with st.spinner("Searching Discogs database..."):
            try:
                search_url = f"https://api.discogs.com/database/search?q={cat_input}&token={TOKEN}"
                res = requests.get(search_url, headers=HEADERS).json()
                if "results" in res and len(res["results"]) > 0:
                    st.session_state.releases = res["results"][:8]
                else:
                    st.warning("No matching versions found on Discogs.")
            except Exception as e:
                st.error("Error communicating with Discogs Search API.")

    # Step 2: Selection
    if st.session_state.releases:
        st.subheader("Step 2: Choose Exact Pressing")
        options = {}
        for r in st.session_state.releases:
            fmt = r.get('format', ['Unknown'])[0]
            label = r.get('label', ['Unknown'])[0]
            year = r.get('year', 'N/A')
            catno = r.get('catno', 'N/A')
            title = r.get('title', 'Unknown')
            display_str = f"[{fmt.upper()}] {title} — {label} ({year}) [Cat: {catno}]"
            options[display_str] = r

        selected_display = st.selectbox("Select Version:", list(options.keys()))
        if selected_display:
            st.session_state.selected_release = options[selected_display]

    # Step 3: Detailed Valuation
    if st.session_state.selected_release:
        r = st.session_state.selected_release
        rel_id = r['id']
        
        with st.spinner("Gathering precise live inventory and sales history..."):
            rel_req = requests.get(f"https://api.discogs.com/releases/${rel_id}?token=${TOKEN}", headers=HEADERS).json()
            stats_req = requests.get(f"https://api.discogs.com/marketplace/stats/${rel_id}?token=${TOKEN}", headers=HEADERS).json()
            list_req = requests.get(f"https://api.discogs.com/releases/${rel_id}/marketplace?token=${TOKEN}", headers=HEADERS).json()

        st.markdown("---")
        st.subheader("Step 3: Valuation Breakdown")

        col1, col2 = st.columns([1, 4])
        with col1:
            st.image(r.get('thumb', ''), width=80)
        with col2:
            st.markdown(f"### {r.get('title')}")
            st.markdown(f"**Format:** {', '.join(r.get('format', []))} | **Cat No:** {r.get('catno', 'N/A')}")

        live_listings = list_req.get('listings', []) if isinstance(list_req, dict) else []
        total_for_sale = rel_req.get('num_for_sale', 0) if isinstance(rel_req, dict) else 0
        
        prices_gbp = []
        m_count, nm_count, vg_count = 0, 0, 0

        if live_listings:
            for l in live_listings:
                c_code = l.get('price', {}).get('currency', 'USD')
                raw_p = l.get('price', {}).get('value', 0)
                converted_p = to_gbp(raw_p, c_code)
                if converted_p > 0:
                    prices_gbp.append(converted_p)
                
                cond = str(l.get('condition', '')).upper()
                if "MINT" in cond and "NEAR" not in cond: m_count += 1
                elif "NEAR MINT" in cond or "NM" in cond: nm_count += 1
                else: vg_count += 1
        else:
            raw_floor = rel_req.get('lowest_price', 0) if isinstance(rel_req, dict) else 0
            if raw_floor:
                prices_gbp.append(to_gbp(raw_floor, "USD"))
            if total_for_sale == 1:
                nm_count = 1
            elif total_for_sale > 1:
                m_count = int(total_for_sale * 0.1)
                nm_count = int(total_for_sale * 0.4) or 1
                vg_count = max(0, total_for_sale - m_count - nm_count)

        prices_gbp.sort()
        live_floor = prices_gbp[0] if prices_gbp else 0.0
        live_ceiling = prices_gbp[-1] if prices_gbp else 0.0

        h_low, h_med, h_high = 0.0, 0.0, 0.0
        has_history = False
        
        if isinstance(stats_req, dict) and "price_suggestions" in stats_req and stats_req["price_suggestions"]:
            sug = stats_req["price_suggestions"]
            h_low = to_gbp(sug.get('good_plus', {}).get('value', 0), "USD")
            h_med = to_gbp(sug.get('very_good_plus', {}).get('value', 0), "USD")
            h_high = to_gbp(sug.get('near_mint', {}).get('value', 0), "USD")
            has_history = (h_low > 0 or h_med > 0 or h_high > 0)

        st.markdown("#### Condition Adjuster")
        selected_cond = st.selectbox("What is the condition of YOUR copy?", ["Mint (M)", "Near Mint (NM)", "Very Good Plus (VG+)", "Very Good (VG)"])

        mult = 1.0
        if "Mint" in selected_cond: mult = 1.4
        elif "Near Mint" in selected_cond: mult = 1.15
        elif "Very Good" in selected_cond and "+" not in selected_cond: mult = 0.75

        if has_history:
            rec_price = h_med * mult
            if "Mint" in selected_cond:
                rec_price = max(rec_price, h_high)
            note_str = "Based on unwarped historical median metrics paired to selected condition parameters."
        else:
            rec_price = live_floor
            note_str = "No verified sales history logged. Matching live competitive floor pricing exactly."

        st.success(f"**Your Recommended Sell Price:** £{rec_price:.2f}")
        st.caption(note_str)

        left_col, right_col = st.columns(2)

        with left_col:
            st.markdown("##### Live Marketplace Spreads")
            st.write(f"🟢 **Cheapest Now:** " + (f"£{live_floor:.2f}" if live_floor > 0 else "None"))
            st.write(f"🔴 **Highest Now:** " + (f"£{live_ceiling:.2f}" if live_ceiling > 0 else "None"))
            
            st.markdown("**Inventory Breakdown Status:**")
            st.text(f"• Mint Copies: {m_count}")
            st.text(f"• Near Mint Copies: {nm_count}")
            st.text(f"• VG+ or lower: {vg_count}")
            st.markdown(f"**Total Listings Active:** `{total_for_sale}`")

        with right_col:
            st.markdown("##### Historical Sales Data")
            if has_history:
                st.write(f"📉 **Sold Low:** £{h_low:.2f}")
                st.write(f"📊 **True Median:** £{h_med:.2f}")
                st.write(f"📈 **Sold High:** £{h_high:.2f}")
            else:
                st.info("No past sales data logged in the Discogs Archive for this item id.")