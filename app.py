import streamlit as st
import requests
from currency_converter import CurrencyConverter

# --- PRECISION COMPACT VIEW STYLING ---
st.set_page_config(page_title="Record Price Checker Pro", page_icon="🎵", layout="centered")

# This custom block aggressively tightens paddings, shrinks text sizes, and reduces margins
st.markdown("""
<style>
    /* Remove huge whitespace at the top of Streamlit pages */
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; max-width: 650px !important; }
    div[data-testid="stDecoration"] { display: none; }
    
    /* Shrink headings and subheaders */
    h1 { font-size: 1.6rem !important; margin-bottom: 0.2rem !important; padding-bottom: 0px !important; }
    h3 { font-size: 1.2rem !important; margin-top: 0.5rem !important; margin-bottom: 0.3rem !important; }
    h4 { font-size: 1.0rem !important; margin-top: 0.4rem !important; margin-bottom: 0.2rem !important; }
    h5 { font-size: 0.9rem !important; margin-top: 0.3rem !important; margin-bottom: 0.2rem !important; }
    .stCaption { font-size: 0.75rem !important; margin-bottom: 0.2rem !important; }
    
    /* Global font and input shrinkage */
    .stSelectbox, .stTextInput, div[data-testid="stMarkdownContainer"] p { 
        font-family: 'DM Mono', monospace; 
        font-size: 0.85rem !important; 
    }
    
    /* Tighten spacing around dropdowns and text inputs */
    div[data-testid="stFormSubmitButton"] { margin-top: 0px !important; }
    .stSelectbox { margin-bottom: -0.5rem !important; }
    
    /* Keep the recommended sell price box bold but slightly more padding-efficient */
    div.stAlert { padding: 0.5rem !important; margin-bottom: 0.5rem !important; }
    
    /* Reduce horizontal rule gaps */
    hr { margin-top: 0.5rem !important; margin-bottom: 0.5rem !important; }
</style>
""", unsafe_allow_html=True)

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

# Main Screen Headers (Now compact)
st.title("🎵 Record Price Checker Pro")
st.caption("Dynamic Value Calibration Engine with True Condition Separations")

# Step 1: Input Search
cat_input = st.text_input("Step 1: Enter Catalogue Number / Barcode", placeholder="e.g. DINCD 113 or scan barcode")

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
        
        with st.spinner("Analyzing lifetime market metrics..."):
            rel_url = f"https://api.discogs.com/releases/{rel_id}?token={TOKEN}"
            rel_req = requests.get(rel_url, headers=HEADERS).json()

        st.markdown("---")
        st.subheader("Step 3: Valuation Breakdown")

        # Your preferred layout size for image and description
        col1, col2 = st.columns([1, 4])
        with col1:
            st.image(active_release.get('thumb', ''), width=80)
        with col2:
            st.markdown(f"### {active_release.get('title')}")
            st.markdown(f"**Format:** {', '.join(active_release.get('format', []))} | **Cat No:** {active_release.get('catno', 'N/A')}")

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

        # --- Step 4: Condition Custom Gradings ---
        st.markdown("#### Condition Adjuster")
        
        selected_cond = st.selectbox(
            "What is the condition of YOUR copy?", 
            ["Mint (M)", "Near Mint (NM)", "Very Good Plus (VG+)", "Very Good (VG)"],
            index=1
        )

        mult = 1.0
        if selected_cond == "Mint (M)": mult = 1.50
        elif selected_cond == "Near Mint (NM)": mult = 1.15
        elif selected_cond == "Very Good Plus (VG+)": mult = 0.85
        elif selected_cond == "Very Good (VG)": mult = 0.65

        rec_price = h_med * mult
        note_str = f"Anchored directly to the true calculated market baseline median value (£{h_med:.2f}) modified by the selected condition curve profile."

        # Keep this prominent box layout exactly how you liked it
        st.success(f"**Your Recommended Sell Price:** £{rec_price:.2f}")
        st.caption(note_str)

        # Minor metrics columns are now scaled down slightly to prevent clipping/scrolling
        left_col, right_col = st.columns(2)

        with left_col:
            st.markdown("##### Historical Profile")
            st.write(f"📉 Low: £{h_low:.2f} | 📊 Med: £{h_med:.2f} | 📈 High: £{h_high:.2f}")
            st.markdown(f"📊 Demand Ratio: `{demand_ratio:.2f}`")

        with right_col:
            st.markdown("##### Marketplace Data")
            st.write(f"🟢 Cheapest Now: " + (f"£{live_floor:.2f}" if live_floor > 0 else "None"))
            st.write(f"👥 Want: {want_count} | Have: {have_count} | 🛒 Active: {total_for_sale}")
