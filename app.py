import streamlit as st
import requests
from currency_converter import CurrencyConverter

# --- WIDESCREEN LAYOUT CONFIGURATION ---
st.set_page_config(page_title="Record Price Checker Pro", page_icon="🎵", layout="wide")

# Original clean font styling safely preserved
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

# --- DYNAMIC KEY ITERATOR ENGINE ---
if 'reset_counter' not in st.session_state:
    st.session_state.reset_counter = 0

st.title("🎵 Record Price Checker Pro")
st.caption("Widescreen Inventory Dashboard Architecture")

# Create two master columns for the landscape layout
left_panel, right_panel = st.columns([1, 1], gap="large")

with left_panel:
    st.subheader("📋 Control Panel")
    
    current_widget_key = f"barcode_input_run_{st.session_state.reset_counter}"
    
    cat_input = st.text_input(
        "Step 1: Enter Catalogue Number / Barcode", 
        placeholder="e.g. DINCD 113 or scan barcode", 
        key=current_widget_key
    )

if cat_input:
    if 'search_query' not in st.session_state or st.session_state.search_query != cat_input:
        st.session_state.search_query = cat_input
        st.session_state.releases = []
        st.session_state.selected_release_index = 0  

    if not st.session_state.releases:
        with left_panel:
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
        with left_panel:
            st.markdown("---")
            st.markdown("##### Step 2: Choose Exact Pressing")
            
            display_options = []
            for r in st.session_state.releases:
                fmt = r.get('format', ['Unknown'])[0]
                label = r.get('label', ['Unknown'])[0]
                year = r.get('year', 'N/A')
                catno = r.get('catno', 'N/A')
                title = r.get('title', 'Unknown')
                
                # NATIVE ADDITION: Safely pull the country string, default to 'Unknown' if missing
                country = r.get('country', 'Unknown')
                
                # Appending the [Country] tag cleanly into your display layout
                display_options.append(f"[{fmt.upper()}] {title} — {label} ({year}) [{country}] [Cat: {catno}]")

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

            # Step 4: Condition Custom Gradings inside the control panel
            st.markdown("##### Step 4: Condition Adjuster")
            selected_cond = st.selectbox(
                "What is the condition of YOUR copy?", 
                ["Mint (M)", "Near Mint (NM)", "Very Good Plus (VG+)", "Very Good (VG)"],
                index=1
            )
            
            st.markdown("---")
            if st.button("🔄 New Scan / Reset App"):
                st.session_state.reset_counter += 1
                for key in list(st.session_state.keys()):
                    if key != 'reset_counter':
                        del st.session_state[key]
                st.rerun()

        # Step 3: Analytics Execution
        rel_id = active_release['id']
        
        with right_panel:
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

        # Math Pricing calculations
        mult = 1.0
        if selected_cond == "Mint (M)": mult = 1.50
        elif selected_cond == "Near Mint (NM)": mult = 1.15
        elif selected_cond == "Very Good Plus (VG+)": mult = 0.85
        elif selected_cond == "Very Good (VG)": mult = 0.65

        rec_price = h_med * mult
        note_str = f"Anchored to calculated market baseline median value (£{h_med:.2f})."

        # --- INJECT ALL REAL-TIME RESULTS INTO THE RIGHT SIDE LANDSCAPE VIEW ---
        with right_panel:
            st.subheader("📈 Step 3: Valuation Breakdown")

            item_col1, item_col2 = st.columns([1, 3])
            with item_col1:
                st.image(active_release.get('thumb', ''), width=90)
            with item_col2:
                st.markdown(f"### {active_release.get('title')}")
                
                # NATIVE ADDITION: Also display the country clearly in the final dashboard summary text
                active_country = active_release.get('country', 'Unknown')
                st.markdown(f"**Format:** {', '.join(active_release.get('format', []))} | **Country:** {active_country} | **Cat No:** {active_release.get('catno', 'N/A')}")

            st.success(f"**Your Recommended Sell Price:** £{rec_price:.2f}")
            st.caption(note_str)

            metric_left, metric_right = st.columns(2)
            with metric_left:
                st.markdown("##### Historical Profile")
                st.write(f"📉 **Archived Low:** £{h_low:.2f}")
                st.write(f"📊 **Archived Median:** £{h_med:.2f}")
                st.write(f"📈 **Archived High:** £{h_high:.2f}")
                st.markdown(f"📊 **Demand Index:** `{demand_ratio:.2f}`")

            with metric_right:
                st.markdown("##### Marketplace Data")
                st.write(f"🟢 **Cheapest Now:** £{live_floor:.2f}" if live_floor > 0 else "🟢 **Cheapest Now:** None")
                st.text(f"• Users Wanting This: {want_count}")
                st.text(f"• Users Owning This: {have_count}")
                st.markdown(f"**Total Listings Active:** `{total_for_sale}`")
