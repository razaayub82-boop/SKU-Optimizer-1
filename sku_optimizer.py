"""
AI-Driven SKU Optimization — Careem Grocery
Prepared by: Muhammad Raza Ayub
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SKU Optimizer — Careem Grocery",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #F7F8FA; }
    
    /* Metric cards */
    div[data-testid="metric-container"] {
        background: #FFFFFF;
        border: 1px solid #E8ECF0;
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    div[data-testid="metric-container"] label {
        font-size: 12px !important;
        color: #6B7280 !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        font-size: 26px !important;
        font-weight: 600 !important;
        color: #111827 !important;
    }

    /* Section headers */
    .section-header {
        font-size: 14px;
        font-weight: 600;
        color: #374151;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin: 24px 0 12px 0;
        padding-bottom: 6px;
        border-bottom: 2px solid #E5E7EB;
    }

    /* Badges */
    .badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
    }
    .badge-keep    { background: #D1FAE5; color: #065F46; }
    .badge-promote { background: #DBEAFE; color: #1E40AF; }
    .badge-replace { background: #FEF3C7; color: #92400E; }
    .badge-delist  { background: #FEE2E2; color: #991B1B; }
    .badge-stockup { background: #EDE9FE; color: #5B21B6; }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #FFFFFF;
        border-right: 1px solid #E8ECF0;
    }

    /* Tab styling */
    button[data-baseweb="tab"] {
        font-size: 13px !important;
        font-weight: 500 !important;
    }

    /* Remove default padding */
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }

    /* Info boxes */
    .info-box {
        background: #EFF6FF;
        border-left: 4px solid #3B82F6;
        border-radius: 0 8px 8px 0;
        padding: 12px 16px;
        margin: 12px 0;
        font-size: 13px;
        color: #1E40AF;
        line-height: 1.6;
    }
    .warning-box {
        background: #FFFBEB;
        border-left: 4px solid #F59E0B;
        border-radius: 0 8px 8px 0;
        padding: 12px 16px;
        margin: 12px 0;
        font-size: 13px;
        color: #92400E;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# DATA GENERATION
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data
def generate_data():
    np.random.seed(42)

    CATEGORIES = {
        'Fresh Produce':    ['Tomatoes','Cucumbers','Spinach','Avocados','Strawberries',
                             'Bell Peppers','Broccoli','Mangoes','Bananas','Blueberries'],
        'Dairy & Eggs':     ['Full Cream Milk','Skimmed Milk','Greek Yogurt','Cheddar Cheese',
                             'Eggs (12pk)','Butter','Cream Cheese','Labneh','Feta Cheese','Sour Cream'],
        'Bakery':           ['White Bread','Whole Wheat Bread','Sourdough Loaf','Croissants',
                             'Pita Bread','Baguette','Multigrain Roll','Brioche','Rye Bread','Flatbread'],
        'Beverages':        ['Still Water 1.5L','Sparkling Water','Orange Juice','Apple Juice',
                             'Green Tea','Oat Milk','Almond Milk','Energy Drink','Coconut Water','Iced Coffee'],
        'Snacks & Confec':  ['Potato Chips','Rice Cakes','Dark Chocolate','Mixed Nuts',
                             'Protein Bar','Gummy Bears','Popcorn','Granola Bar','Pretzels','Trail Mix'],
        'Household Staples':['Basmati Rice 5kg','Pasta 500g','Olive Oil 1L','Canned Tomatoes',
                             'Chickpeas (can)','Lentils 1kg','Tahini','Soy Sauce','Honey 500g','Quinoa 500g']
    }

    SHELF_LIFE = {
        'Fresh Produce': 5, 'Dairy & Eggs': 14, 'Bakery': 7,
        'Beverages': 180, 'Snacks & Confec': 180, 'Household Staples': 365
    }

    SPACE_RANGE = {
        'Fresh Produce': (2,6), 'Dairy & Eggs': (1,5), 'Bakery': (1,4),
        'Beverages': (3,10), 'Snacks & Confec': (1,5), 'Household Staples': (2,8)
    }

    # Seasonality profiles
    SEASON_PROFILE = {
        'Tomatoes':'summer_peak','Cucumbers':'summer_peak','Spinach':'winter_peak',
        'Avocados':'flat','Strawberries':'summer_peak','Bell Peppers':'summer_peak',
        'Broccoli':'winter_peak','Mangoes':'summer_peak','Bananas':'flat','Blueberries':'summer_peak',
        'Full Cream Milk':'flat','Skimmed Milk':'flat','Greek Yogurt':'summer_peak',
        'Cheddar Cheese':'flat','Eggs (12pk)':'ramadan_peak','Butter':'flat',
        'Cream Cheese':'flat','Labneh':'ramadan_peak','Feta Cheese':'summer_peak','Sour Cream':'flat',
        'White Bread':'flat','Whole Wheat Bread':'flat','Sourdough Loaf':'flat',
        'Croissants':'flat','Pita Bread':'ramadan_peak','Baguette':'flat',
        'Multigrain Roll':'flat','Brioche':'flat','Rye Bread':'winter_peak','Flatbread':'ramadan_peak',
        'Still Water 1.5L':'summer_peak','Sparkling Water':'summer_peak','Orange Juice':'flat',
        'Apple Juice':'flat','Green Tea':'winter_peak','Oat Milk':'flat','Almond Milk':'flat',
        'Energy Drink':'summer_peak','Coconut Water':'summer_peak','Iced Coffee':'summer_peak',
        'Potato Chips':'flat','Rice Cakes':'flat','Dark Chocolate':'winter_peak',
        'Mixed Nuts':'ramadan_peak','Protein Bar':'flat','Gummy Bears':'flat',
        'Popcorn':'flat','Granola Bar':'flat','Pretzels':'flat','Trail Mix':'flat',
        'Basmati Rice 5kg':'ramadan_peak','Pasta 500g':'flat','Olive Oil 1L':'ramadan_peak',
        'Canned Tomatoes':'flat','Chickpeas (can)':'ramadan_peak','Lentils 1kg':'ramadan_peak',
        'Tahini':'ramadan_peak','Soy Sauce':'flat','Honey 500g':'ramadan_peak','Quinoa 500g':'flat'
    }

    # Off-season and peak months per profile (month index 0=Jan, 11=Dec)
    OFF_SEASON_MONTHS = {
        'flat': [],
        'summer_peak': [9,10,11,0,1,2],   # Oct–Mar
        'winter_peak': [3,4,5,6,7,8],     # Apr–Sep
        'ramadan_peak': [3,4,5,6,7,8,9,10,11,0,1]  # everything except Feb-Mar
    }
    PEAK_MONTHS = {
        'flat': [],
        'summer_peak': [5,6,7],    # Jun–Aug
        'winter_peak': [11,0,1],   # Dec–Feb
        'ramadan_peak': [1,2]      # Feb–Mar (Ramadan)
    }

    rows = []
    sku_id = 1000

    for category, skus in CATEGORIES.items():
        for sku_name in skus:
            units     = max(5, int(np.random.lognormal(4.5, 0.8)))
            price     = round(np.random.uniform(3, 45), 2)
            rev       = round(units * price, 1)
            mg_pct    = round(np.random.uniform(8, 52), 1)
            mg_sar    = round(rev * mg_pct / 100, 1)
            trend     = round(np.random.normal(2, 18), 1)
            dos       = int(np.random.uniform(1, 14) if category == 'Fresh Produce'
                           else np.random.uniform(3, 90))
            stock_val = round(dos * rev / 7, 1)
            sup       = int(np.random.uniform(40, 100))
            lead      = int(np.random.uniform(1, 21))
            ret       = round(np.random.uniform(0.2, 12), 1)
            rating    = round(np.random.uniform(2.5, 5.0), 1)
            sr        = SPACE_RANGE[category]
            space     = int(np.random.uniform(sr[0], sr[1]))
            shelf     = SHELF_LIFE[category]
            profile   = SEASON_PROFILE.get(sku_name, 'flat')

            # Wastage
            wast_days  = max(0, dos - shelf)
            wast_units = round(wast_days / 7 * units, 1)
            wast_cost  = round(wast_units * price * (1 - mg_pct / 100), 1)
            wast_cost  = min(wast_cost, mg_sar)  # cap at margin
            eff_mg_sar = round(mg_sar - wast_cost, 1)
            eff_mg_pct = round(eff_mg_sar / max(rev, 1) * 100, 1)
            wast_risk  = ('None' if wast_days == 0 else
                          'Low'  if wast_days <= 3 else
                          'Medium' if wast_days <= 7 else 'High')

            # Seasonality flags (simulated current month = March, index 2)
            current_month = 2
            next_month    = (current_month + 1) % 12
            in_off_season = current_month in OFF_SEASON_MONTHS.get(profile, [])
            peak_approaching = (next_month in PEAK_MONTHS.get(profile, []) or
                                current_month in PEAK_MONTHS.get(profile, []))

            # Space productivity
            rev_per_space = round(rev / max(space, 1), 1)
            mg_per_space  = round(mg_sar / max(space, 1), 1)
            sell_thru     = units / (dos + 1) * lead

            rows.append({
                'SKU_ID': f'SKU-{sku_id}',
                'SKU_Name': sku_name,
                'Category': category,
                'Avg_Price_SAR': price,
                'Weekly_Units_Sold': units,
                'Weekly_Revenue_SAR': rev,
                'Gross_Margin_Pct': mg_pct,
                'Margin_SAR_Weekly': mg_sar,
                'Revenue_Trend_MoM': trend,
                'Days_of_Stock': dos,
                'Stock_Value_SAR': stock_val,
                'Supplier_Score': sup,
                'Lead_Time_Days': lead,
                'Return_Rate_Pct': ret,
                'Customer_Rating': rating,
                'Space_Units': space,
                'Rev_Per_Space': rev_per_space,
                'Mg_Per_Space': mg_per_space,
                'Sell_Through': sell_thru,
                'Shelf_Life_Days': shelf,
                'Wastage_Days': wast_days,
                'Wastage_Cost_SAR': wast_cost,
                'Eff_Margin_SAR': eff_mg_sar,
                'Eff_Margin_Pct': eff_mg_pct,
                'Wastage_Risk': wast_risk,
                'Seasonality_Profile': profile,
                'In_Off_Season': in_off_season,
                'Peak_Approaching': peak_approaching,
            })
            sku_id += 1

    return pd.DataFrame(rows)


# ══════════════════════════════════════════════════════════════════════════════
# SCORING ENGINE
# ══════════════════════════════════════════════════════════════════════════════
def normalise(series, invert=False):
    mn, mx = series.min(), series.max()
    if mx == mn:
        return pd.Series([50.0] * len(series), index=series.index)
    n = (series - mn) / (mx - mn) * 100
    return (100 - n) if invert else n


def score_and_classify(df):
    WEIGHTS = {
        'n_mg_pct':      0.12,
        'n_mg_sar':      0.10,
        'n_eff_mg':      0.08,
        'n_trend':       0.13,
        'n_sell':        0.07,
        'n_dos':         0.10,
        'n_lead':        0.07,
        'n_sup':         0.05,
        'n_rating':      0.06,
        'n_ret':         0.03,
        'n_mg_space':    0.12,
        'n_rev_space':   0.07,
    }
    # Verify weights sum to 1.0
    assert abs(sum(WEIGHTS.values()) - 1.0) < 0.001

    df = df.copy()
    df['n_mg_pct']   = normalise(df['Gross_Margin_Pct'])
    df['n_mg_sar']   = normalise(df['Margin_SAR_Weekly'])
    df['n_eff_mg']   = normalise(df['Eff_Margin_Pct'])
    df['n_trend']    = normalise(df['Revenue_Trend_MoM'])
    df['n_sell']     = normalise(df['Sell_Through'])
    df['n_dos']      = normalise(df['Days_of_Stock'],    invert=True)
    df['n_lead']     = normalise(df['Lead_Time_Days'],   invert=True)
    df['n_sup']      = normalise(df['Supplier_Score'])
    df['n_rating']   = normalise(df['Customer_Rating'])
    df['n_ret']      = normalise(df['Return_Rate_Pct'],  invert=True)
    df['n_mg_space'] = normalise(df['Mg_Per_Space'])
    df['n_rev_space']= normalise(df['Rev_Per_Space'])

    df['Composite_Score'] = sum(df[k] * w for k, w in WEIGHTS.items())
    df['Composite_Score'] = df['Composite_Score'].round(1)

    def classify(row):
        s = row['Composite_Score']
        t = row['Revenue_Trend_MoM']
        if row['Peak_Approaching'] and s >= 40:
            return 'STOCK UP'
        elif s >= 65:
            return 'KEEP'
        elif s >= 50 and t >= 0:
            return 'PROMOTE'
        elif s >= 35 or row['Gross_Margin_Pct'] >= 25:
            return 'REPLACE'
        else:
            return 'DELIST'

    df['Recommendation'] = df.apply(classify, axis=1)
    return df


# ══════════════════════════════════════════════════════════════════════════════
# COLOUR MAPS
# ══════════════════════════════════════════════════════════════════════════════
REC_COLOURS = {
    'KEEP':     '#10B981',
    'PROMOTE':  '#3B82F6',
    'REPLACE':  '#F59E0B',
    'DELIST':   '#EF4444',
    'STOCK UP': '#8B5CF6',
}
RISK_COLOURS = {
    'None':   '#D1FAE5',
    'Low':    '#FEF3C7',
    'Medium': '#FED7AA',
    'High':   '#FEE2E2',
}
SEASON_COLOURS = {
    'flat':         '#9CA3AF',
    'summer_peak':  '#F59E0B',
    'winter_peak':  '#3B82F6',
    'ramadan_peak': '#8B5CF6',
}


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def fmt_sar(n):  return f"SAR {n:,.0f}"
def fmt_pct(n):  return f"{n:.1f}%"
def fmt_num(n):  return f"{n:,.0f}"

def rec_badge_html(rec):
    cls_map = {'KEEP':'keep','PROMOTE':'promote','REPLACE':'replace',
               'DELIST':'delist','STOCK UP':'stockup'}
    css_class = cls_map.get(rec, 'replace')
    return f'<span class="badge badge-{css_class}">{rec}</span>'

def generate_rationale(row):
    rec   = row['Recommendation']
    score = row['Composite_Score']
    trend = row['Revenue_Trend_MoM']
    mg    = row['Gross_Margin_Pct']
    dos   = row['Days_of_Stock']
    sup   = row['Supplier_Score']
    ret   = row['Return_Rate_Pct']
    off   = row['In_Off_Season']
    peak  = row['Peak_Approaching']

    season_note = " (Note: SKU is in off-season — trend signal may understate true demand.)" if off else ""
    peak_note   = " Peak season approaching — build stock now to avoid stockout." if peak else ""

    if rec == 'KEEP':
        return f"Strong performer (score {score:.0f}). {mg:.0f}% margin, {'+' if trend>=0 else ''}{trend:.1f}% MoM trend.{season_note} Maintain range and pricing."
    elif rec == 'PROMOTE':
        return f"Good potential (score {score:.0f}) with positive trend ({trend:+.1f}% MoM). Recommend shelf prominence or promotional pricing to lift volume.{season_note}"
    elif rec == 'REPLACE':
        gaps = []
        if mg < 20:  gaps.append(f"low margin ({mg:.0f}%)")
        if trend < -5: gaps.append(f"declining trend ({trend:.1f}% MoM)")
        if dos > 45: gaps.append(f"excess stock ({dos}d)")
        if sup < 60: gaps.append(f"weak supplier ({sup}/100)")
        if ret > 7:  gaps.append(f"high returns ({ret:.1f}%)")
        gap_str = ", ".join(gaps[:2]) if gaps else "below-average composite performance"
        return f"Underperforming (score {score:.0f}) due to {gap_str}. Source a stronger alternative.{season_note}"
    elif rec == 'STOCK UP':
        return f"Score {score:.0f} with peak season approaching.{peak_note} Increase order quantity now."
    else:
        return f"Poor performer (score {score:.0f}). {'+' if trend>=0 else ''}{trend:.1f}% MoM trend, {mg:.0f}% margin, {dos}d stock. Delist to free shelf space and working capital."


# ══════════════════════════════════════════════════════════════════════════════
# LOAD DATA
# ══════════════════════════════════════════════════════════════════════════════
df_raw  = generate_data()
df      = score_and_classify(df_raw)
df['Rationale'] = df.apply(generate_rationale, axis=1)

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 🛒 SKU Optimizer")
    st.markdown("**Careem Grocery** · Category Management")
    st.markdown("---")
    st.markdown("**Filters**")

    selected_cats = st.multiselect(
        "Category",
        options=sorted(df['Category'].unique()),
        default=sorted(df['Category'].unique())
    )
    selected_recs = st.multiselect(
        "Recommendation",
        options=['KEEP','PROMOTE','REPLACE','DELIST','STOCK UP'],
        default=['KEEP','PROMOTE','REPLACE','DELIST','STOCK UP']
    )
    score_range = st.slider("Composite score range", 0.0, 100.0, (0.0, 100.0), step=1.0)
    search_term = st.text_input("Search SKU name", "")

    st.markdown("---")
    st.markdown("**Simulated month:** March 2025")
    st.markdown("*Ramadan peak approaching*")
    st.markdown("---")
    st.caption("Prototype using dummy data. All weights, thresholds, and shelf-life values are configurable for production deployment.")

# ── Apply filters ─────────────────────────────────────────────────────────────
mask = (
    df['Category'].isin(selected_cats) &
    df['Recommendation'].isin(selected_recs) &
    df['Composite_Score'].between(score_range[0], score_range[1])
)
if search_term:
    mask &= df['SKU_Name'].str.contains(search_term, case=False)

df_filtered = df[mask].copy()

# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 🛒 AI-Driven SKU Optimization")
st.markdown("**Careem Grocery · Category Management Dashboard** · Prototype by Muhammad Raza Ayub")
st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Overview",
    "📋 SKU Recommendations",
    "📐 Sales to Space",
    "🗑️ Wastage",
    "📅 Seasonality",
    "💰 P&L Impact",
    "⚙️ Scoring Model"
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    total_rev  = df_filtered['Weekly_Revenue_SAR'].sum()
    total_mg   = df_filtered['Margin_SAR_Weekly'].sum()
    total_wast = df_filtered['Wastage_Cost_SAR'].sum()
    avg_mg_pct = total_mg / max(total_rev, 1) * 100

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("SKUs in view",          f"{len(df_filtered)}", f"of {len(df)} total")
    c2.metric("Weekly revenue (SAR)",  fmt_sar(total_rev))
    c3.metric("Weekly margin (SAR)",   fmt_sar(total_mg),     f"{avg_mg_pct:.1f}% avg margin")
    c4.metric("Weekly wastage cost",   fmt_sar(total_wast),   f"{total_wast/max(total_mg,1)*100:.1f}% of margin")

    st.markdown('<div class="section-header">Classification split</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        rec_counts = df_filtered['Recommendation'].value_counts().reset_index()
        rec_counts.columns = ['Recommendation', 'Count']
        fig_donut = px.pie(
            rec_counts, values='Count', names='Recommendation',
            hole=0.55,
            color='Recommendation',
            color_discrete_map=REC_COLOURS,
            title="SKU recommendation split"
        )
        fig_donut.update_traces(textposition='outside', textinfo='label+percent')
        fig_donut.update_layout(
            showlegend=False, height=320,
            title_font_size=13,
            margin=dict(t=40, b=0, l=0, r=0)
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with col2:
        fig_hist = px.histogram(
            df_filtered, x='Composite_Score', color='Recommendation',
            nbins=20, barmode='stack',
            color_discrete_map=REC_COLOURS,
            title="Score distribution by recommendation",
            labels={'Composite_Score': 'Composite score (0–100)', 'count': 'SKUs'}
        )
        fig_hist.add_vline(x=35, line_dash="dash", line_color="#EF4444", annotation_text="Delist (35)", annotation_font_size=10)
        fig_hist.add_vline(x=50, line_dash="dash", line_color="#F59E0B", annotation_text="Replace/Promote (50)", annotation_font_size=10)
        fig_hist.add_vline(x=65, line_dash="dash", line_color="#10B981", annotation_text="Keep (65)", annotation_font_size=10)
        fig_hist.update_layout(height=320, title_font_size=13, showlegend=False, margin=dict(t=40,b=0,l=0,r=0))
        st.plotly_chart(fig_hist, use_container_width=True)

    st.markdown('<div class="section-header">Margin vs revenue trend — quadrant view</div>', unsafe_allow_html=True)
    fig_scatter = px.scatter(
        df_filtered,
        x='Revenue_Trend_MoM', y='Gross_Margin_Pct',
        color='Recommendation', color_discrete_map=REC_COLOURS,
        hover_name='SKU_Name',
        hover_data={'Category':True, 'Composite_Score':True, 'Revenue_Trend_MoM':':.1f', 'Gross_Margin_Pct':':.1f'},
        labels={'Revenue_Trend_MoM':'Revenue trend MoM %', 'Gross_Margin_Pct':'Gross margin %'},
        title="Each dot = one SKU. Hover for details."
    )
    fig_scatter.add_vline(x=0,  line_dash="dot", line_color="#D1D5DB")
    fig_scatter.add_hline(y=20, line_dash="dot", line_color="#D1D5DB")
    fig_scatter.add_annotation(x=30,  y=48, text="Stars ⭐", showarrow=False, font=dict(size=11, color="#10B981"))
    fig_scatter.add_annotation(x=-35, y=48, text="High margin, declining", showarrow=False, font=dict(size=11, color="#F59E0B"))
    fig_scatter.add_annotation(x=30,  y=10, text="Growing, low margin", showarrow=False, font=dict(size=11, color="#3B82F6"))
    fig_scatter.add_annotation(x=-35, y=10, text="Delist zone ⚠️", showarrow=False, font=dict(size=11, color="#EF4444"))
    fig_scatter.update_layout(height=380, title_font_size=13, margin=dict(t=40,b=0,l=0,r=0))
    st.plotly_chart(fig_scatter, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — SKU RECOMMENDATIONS
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown(f"**{len(df_filtered)} SKUs** matching current filters · sorted by composite score")

    display_cols = ['SKU_Name','Category','Composite_Score','Recommendation',
                    'Gross_Margin_Pct','Revenue_Trend_MoM','Days_of_Stock',
                    'Wastage_Risk','Seasonality_Profile','Mg_Per_Space','Rationale']

    df_display = df_filtered[display_cols].sort_values('Composite_Score', ascending=False).copy()
    df_display.columns = ['SKU','Category','Score','Recommendation',
                          'Margin %','Trend MoM %','Days Stock',
                          'Wastage Risk','Season Profile','Margin/Space (SAR)','Rationale']

    def colour_rec(val):
        colours = {'KEEP':'background-color:#D1FAE5;color:#065F46',
                   'PROMOTE':'background-color:#DBEAFE;color:#1E40AF',
                   'REPLACE':'background-color:#FEF3C7;color:#92400E',
                   'DELIST':'background-color:#FEE2E2;color:#991B1B',
                   'STOCK UP':'background-color:#EDE9FE;color:#5B21B6'}
        return colours.get(val, '')

    def colour_risk(val):
        colours = {'None':'background-color:#D1FAE5','Low':'background-color:#FEF9C3',
                   'Medium':'background-color:#FED7AA','High':'background-color:#FEE2E2'}
        return colours.get(val, '')

    def colour_trend(val):
        try:
            return 'color:#10B981;font-weight:600' if float(val) >= 0 else 'color:#EF4444;font-weight:600'
        except: return ''

    styled = (df_display.style
              .applymap(colour_rec,   subset=['Recommendation'])
              .applymap(colour_risk,  subset=['Wastage Risk'])
              .applymap(colour_trend, subset=['Trend MoM %'])
              .format({'Score':'{:.1f}','Margin %':'{:.1f}%','Trend MoM %':'{:+.1f}%','Margin/Space (SAR)':'{:.0f}'})
              .set_properties(**{'font-size':'12px'})
    )
    st.dataframe(styled, use_container_width=True, height=500)

    st.markdown("---")
    st.markdown("**Export filtered recommendations**")
    csv = df_filtered[display_cols].to_csv(index=False)
    st.download_button(
        label="⬇️ Download as CSV",
        data=csv,
        file_name="sku_recommendations.csv",
        mime="text/csv"
    )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — SALES TO SPACE
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    total_space  = df_filtered['Space_Units'].sum()
    avg_mg_space = df_filtered['Mg_Per_Space'].mean()
    freed_space  = df_filtered[df_filtered['Recommendation']=='DELIST']['Space_Units'].sum()
    realloc_opp  = freed_space * avg_mg_space

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total storage units",        fmt_num(total_space))
    c2.metric("Avg margin / space (SAR)",   f"{avg_mg_space:.0f}")
    c3.metric("Space freed by delisting",   f"{freed_space} units")
    c4.metric("Reallocation opportunity",   fmt_sar(realloc_opp), "weekly margin if reallocated")

    st.markdown('<div class="section-header">Space efficiency analysis</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        cat_space = (df_filtered.groupby('Category')['Mg_Per_Space']
                     .mean().reset_index()
                     .sort_values('Mg_Per_Space', ascending=True))
        fig_space_bar = px.bar(
            cat_space, x='Mg_Per_Space', y='Category', orientation='h',
            title="Avg margin per storage unit by category (SAR)",
            labels={'Mg_Per_Space':'SAR per space unit','Category':''},
            color='Mg_Per_Space',
            color_continuous_scale=['#FEE2E2','#FEF3C7','#D1FAE5']
        )
        fig_space_bar.update_layout(height=300, title_font_size=13,
                                    coloraxis_showscale=False,
                                    margin=dict(t=40,b=0,l=0,r=0))
        st.plotly_chart(fig_space_bar, use_container_width=True)

    with col2:
        fig_space_sc = px.scatter(
            df_filtered, x='Space_Units', y='Mg_Per_Space',
            color='Recommendation', color_discrete_map=REC_COLOURS,
            hover_name='SKU_Name',
            hover_data={'Category':True,'Mg_Per_Space':':.0f','Space_Units':True},
            title="Space occupied vs margin per space unit",
            labels={'Space_Units':'Storage units occupied','Mg_Per_Space':'Margin per space unit (SAR)'}
        )
        fig_space_sc.update_layout(height=300, title_font_size=13,
                                   showlegend=False, margin=dict(t=40,b=0,l=0,r=0))
        st.plotly_chart(fig_space_sc, use_container_width=True)

    st.markdown('<div class="section-header">Top 10 vs Bottom 10 — margin per space unit</div>', unsafe_allow_html=True)
    space_sorted = df_filtered.sort_values('Mg_Per_Space', ascending=False)
    top10    = space_sorted.head(10).copy()
    bottom10 = space_sorted.tail(10).copy()
    top10['Rank']    = [f"Top {i+1}" for i in range(len(top10))]
    bottom10['Rank'] = [f"Bottom {i+1}" for i in range(len(bottom10))]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Top 10 — highest margin per space unit**")
        st.dataframe(
            top10[['SKU_Name','Category','Space_Units','Margin_SAR_Weekly','Mg_Per_Space','Recommendation']]
            .rename(columns={'SKU_Name':'SKU','Margin_SAR_Weekly':'Wkly Margin (SAR)','Mg_Per_Space':'Margin/Space','Space_Units':'Space Units'})
            .style.format({'Wkly Margin (SAR)':'{:.0f}','Margin/Space':'{:.0f}'})
            .set_properties(**{'font-size':'12px'}),
            use_container_width=True, height=320
        )
    with col2:
        st.markdown("**Bottom 10 — lowest margin per space unit**")
        st.dataframe(
            bottom10[['SKU_Name','Category','Space_Units','Margin_SAR_Weekly','Mg_Per_Space','Recommendation']]
            .rename(columns={'SKU_Name':'SKU','Margin_SAR_Weekly':'Wkly Margin (SAR)','Mg_Per_Space':'Margin/Space','Space_Units':'Space Units'})
            .style.format({'Wkly Margin (SAR)':'{:.0f}','Margin/Space':'{:.0f}'})
            .set_properties(**{'font-size':'12px'}),
            use_container_width=True, height=320
        )

    st.markdown("""
    <div class="info-box">
    <b>How to read this tab:</b> Margin per space unit tells you how much gross margin each storage unit generates weekly. 
    A SKU occupying 8 storage units but generating SAR 40/unit earns SAR 320/week in space. 
    A SKU occupying 2 units generating SAR 800/unit earns SAR 1,600/week. 
    The second SKU is 5× more space-productive despite occupying far less room.
    In production, space units would be pulled from WMS shelf/pallet data per SKU.
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — WASTAGE
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    at_risk      = df_filtered[df_filtered['Wastage_Days'] > 0]
    total_wast   = df_filtered['Wastage_Cost_SAR'].sum()
    total_mg_all = df_filtered['Margin_SAR_Weekly'].sum()
    new_wast     = df_filtered[df_filtered['Recommendation']!='DELIST']['Wastage_Cost_SAR'].sum() * 0.6
    wast_pct_mg  = total_wast / max(total_mg_all, 1) * 100

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("SKUs at wastage risk",        f"{len(at_risk)} of {len(df_filtered)}")
    c2.metric("Weekly wastage cost (SAR)",   fmt_sar(total_wast),    f"SAR {total_wast*52:,.0f} annualised")
    c3.metric("% of margin lost to wastage", f"{wast_pct_mg:.1f}%",  "of gross margin eroded weekly")
    c4.metric("Post-action wastage saving",  fmt_sar(total_wast - new_wast), "weekly, from reorder alignment")

    st.markdown('<div class="section-header">Wastage breakdown</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        wast_cat = (df_filtered.groupby('Category')['Wastage_Cost_SAR']
                    .sum().reset_index()
                    .sort_values('Wastage_Cost_SAR'))
        fig_wbar = px.bar(
            wast_cat, x='Wastage_Cost_SAR', y='Category', orientation='h',
            title="Weekly wastage cost by category (SAR)",
            labels={'Wastage_Cost_SAR':'SAR/week','Category':''},
            color='Wastage_Cost_SAR',
            color_continuous_scale=['#FEF3C7','#FED7AA','#FEE2E2']
        )
        fig_wbar.update_layout(height=300, title_font_size=13,
                               coloraxis_showscale=False, margin=dict(t=40,b=0,l=0,r=0))
        st.plotly_chart(fig_wbar, use_container_width=True)

    with col2:
        risk_counts = df_filtered['Wastage_Risk'].value_counts().reset_index()
        risk_counts.columns = ['Risk','Count']
        fig_wrisk = px.pie(
            risk_counts, values='Count', names='Risk',
            color='Risk',
            color_discrete_map={'None':'#D1FAE5','Low':'#FEF9C3','Medium':'#FED7AA','High':'#FEE2E2'},
            hole=0.55,
            title="Wastage risk distribution"
        )
        fig_wrisk.update_layout(height=300, title_font_size=13, margin=dict(t=40,b=0,l=0,r=0))
        st.plotly_chart(fig_wrisk, use_container_width=True)

    st.markdown('<div class="section-header">Top 10 SKUs by wastage cost</div>', unsafe_allow_html=True)
    top_wast = (df_filtered[df_filtered['Wastage_Cost_SAR'] > 0]
                .sort_values('Wastage_Cost_SAR', ascending=False)
                .head(10)
                [['SKU_Name','Category','Shelf_Life_Days','Days_of_Stock','Wastage_Days',
                  'Gross_Margin_Pct','Eff_Margin_Pct','Wastage_Cost_SAR','Wastage_Risk','Recommendation']])
    top_wast.columns = ['SKU','Category','Shelf Life (d)','Days Stock','Wastage Days',
                        'Gross Margin %','Eff Margin %','Wastage Cost/wk (SAR)','Risk','Recommendation']

    def colour_wast_risk(val):
        return {'None':'background-color:#D1FAE5','Low':'background-color:#FEF9C3',
                'Medium':'background-color:#FED7AA','High':'background-color:#FEE2E2'}.get(val,'')

    st.dataframe(
        top_wast.style
        .applymap(colour_wast_risk, subset=['Risk'])
        .format({'Gross Margin %':'{:.1f}%','Eff Margin %':'{:.1f}%','Wastage Cost/wk (SAR)':'{:.0f}'})
        .set_properties(**{'font-size':'12px'}),
        use_container_width=True, height=340
    )

    st.markdown("""
    <div class="info-box">
    <b>Wastage calculation:</b><br>
    Wastage days = max(0, Days of stock − Shelf life)<br>
    Wastage cost = (Wastage days / 7) × Weekly units × Price × (1 − Margin %)<br>
    Effective margin = (Margin SAR − Wastage cost) / Revenue × 100<br>
    Wastage cost is capped at weekly margin SAR — effective margin floors at 0%.
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — SEASONALITY
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    stock_up     = df_filtered[df_filtered['Recommendation']=='STOCK UP']
    off_season   = df_filtered[df_filtered['In_Off_Season']==True]
    ramadan_skus = df_filtered[df_filtered['Seasonality_Profile']=='ramadan_peak']

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Simulated month",      "March 2025",       "Ramadan peak approaching")
    c2.metric("Stock up candidates",  len(stock_up),      "peak season within 4 weeks")
    c3.metric("Off-season SKUs",      len(off_season),    "trend signal less reliable")
    c4.metric("Ramadan profile SKUs", len(ramadan_skus),  "peaking this period")

    st.markdown('<div class="section-header">Seasonality profiles</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        prof_counts = df_filtered['Seasonality_Profile'].value_counts().reset_index()
        prof_counts.columns = ['Profile','Count']
        fig_spie = px.pie(
            prof_counts, values='Count', names='Profile', hole=0.55,
            color='Profile', color_discrete_map=SEASON_COLOURS,
            title="SKUs by seasonality profile"
        )
        fig_spie.update_layout(height=300, title_font_size=13, margin=dict(t=40,b=0,l=0,r=0))
        st.plotly_chart(fig_spie, use_container_width=True)

    with col2:
        months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        SEA_IDX = {
            'flat':         [1.0]*12,
            'summer_peak':  [0.7,0.75,0.8,0.9,1.1,1.3,1.4,1.35,1.1,0.9,0.75,0.65],
            'winter_peak':  [1.3,1.2,1.0,0.85,0.8,0.7,0.65,0.7,0.85,1.0,1.2,1.35],
            'ramadan_peak': [0.85,0.9,1.5,1.3,0.9,0.8,0.8,0.85,0.9,0.95,0.9,0.85]
        }
        fig_line = go.Figure()
        for profile, colour in SEASON_COLOURS.items():
            fig_line.add_trace(go.Scatter(
                x=months, y=SEA_IDX[profile], name=profile.replace('_',' '),
                line=dict(color=colour, width=2), mode='lines+markers'
            ))
        fig_line.add_shape(type='line', x0=2, x1=2, y0=0, y1=1,
                           xref='x', yref='paper',
                           line=dict(dash='dash', color='#8B5CF6', width=1.5))
        fig_line.add_annotation(x=2, y=1.05, xref='x', yref='paper',
                                text='Mar (current)', showarrow=False,
                                font=dict(size=10, color='#8B5CF6'))
        fig_line.update_layout(
            title='Seasonality index curves (1.0 = average month)',
            title_font_size=13, height=300,
            yaxis_title='Index', xaxis_title='',
            legend=dict(font=dict(size=11)),
            margin=dict(t=40,b=0,l=0,r=0)
        )
        st.plotly_chart(fig_line, use_container_width=True)

    st.markdown('<div class="section-header">Stock up recommendations — peak approaching</div>', unsafe_allow_html=True)
    if len(stock_up) > 0:
        su_display = stock_up[['SKU_Name','Category','Seasonality_Profile',
                               'Revenue_Trend_MoM','Composite_Score','Rationale']].copy()
        su_display.columns = ['SKU','Category','Season Profile','Raw Trend MoM %','Score','Action rationale']
        st.dataframe(
            su_display.style
            .format({'Raw Trend MoM %':'{:+.1f}%','Score':'{:.1f}'})
            .set_properties(**{'font-size':'12px'}),
            use_container_width=True, height=300
        )
    else:
        st.info("No Stock Up candidates in current filter selection.")

    st.markdown('<div class="section-header">Off-season SKUs — treat trend with caution</div>', unsafe_allow_html=True)
    if len(off_season) > 0:
        off_display = off_season[['SKU_Name','Category','Seasonality_Profile',
                                  'Revenue_Trend_MoM','Composite_Score','Recommendation']].copy()
        off_display.columns = ['SKU','Category','Season Profile','Raw Trend MoM %','Score','Recommendation']
        st.dataframe(
            off_display.style
            .format({'Raw Trend MoM %':'{:+.1f}%','Score':'{:.1f}'})
            .set_properties(**{'font-size':'12px'}),
            use_container_width=True, height=300
        )
    else:
        st.info("No off-season SKUs in current filter selection.")

    st.markdown("""
    <div class="info-box">
    <b>Seasonality logic (simplified):</b><br>
    Rather than applying a numerical correction to the trend, this model uses two simple flags:<br>
    <b>Off-season flag</b> — SKU is in a below-average demand period. Raw trend signal may understate true demand. Category manager should weight this SKU's trend score with caution.<br>
    <b>Peak approaching flag</b> — Next month falls within the SKU's peak season. If composite score ≥ 40, action is overridden to STOCK UP regardless of trend.
    In production, these flags would be derived from SKU-level historical sales curves rather than category-level profiles.
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — P&L IMPACT
# ══════════════════════════════════════════════════════════════════════════════
with tab6:
    delists  = df_filtered[df_filtered['Recommendation']=='DELIST']
    promotes = df_filtered[df_filtered['Recommendation']=='PROMOTE']
    replaces = df_filtered[df_filtered['Recommendation']=='REPLACE']
    keeps    = df_filtered[df_filtered['Recommendation']=='KEEP']
    stockups = df_filtered[df_filtered['Recommendation']=='STOCK UP']

    b_rev  = df_filtered['Weekly_Revenue_SAR'].sum()
    b_mg   = df_filtered['Margin_SAR_Weekly'].sum()
    b_wast = df_filtered['Wastage_Cost_SAR'].sum()
    b_mg_pct = b_mg / max(b_rev, 1) * 100

    delist_loss   = -delists['Margin_SAR_Weekly'].sum()
    promote_gain  =  promotes['Margin_SAR_Weekly'].sum() * 0.25 * 1.03
    replace_gain  =  replaces['Margin_SAR_Weekly'].sum() * 0.15
    wast_saving   =  b_wast - df_filtered[df_filtered['Recommendation']!='DELIST']['Wastage_Cost_SAR'].sum() * 0.6
    new_mg   = b_mg + delist_loss + promote_gain + replace_gain + wast_saving
    new_rev  = (keeps['Weekly_Revenue_SAR'].sum() +
                promotes['Weekly_Revenue_SAR'].sum() * 1.25 +
                replaces['Weekly_Revenue_SAR'].sum() * 1.05 +
                stockups['Weekly_Revenue_SAR'].sum() * 1.15)
    new_mg_pct  = new_mg / max(new_rev, 1) * 100
    freed_cap   = delists['Stock_Value_SAR'].sum()
    freed_space = delists['Space_Units'].sum()

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Weekly margin uplift",    fmt_sar(new_mg - b_mg),    f"SAR {(new_mg-b_mg)*52:,.0f} annualised")
    c2.metric("Margin % improvement",    f"+{new_mg_pct - b_mg_pct:.1f}pp", f"{b_mg_pct:.1f}% → {new_mg_pct:.1f}%")
    c3.metric("Working capital freed",   fmt_sar(freed_cap),        f"{len(delists)} SKUs delisted")
    c4.metric("Storage units freed",     f"{freed_space} units",    "redeployable to better SKUs")

    st.markdown('<div class="section-header">Margin waterfall</div>', unsafe_allow_html=True)

    # Proper floating bar waterfall
    cursor = b_mg
    wf_steps = [
        {'label':'Baseline margin',  'bottom':0,                  'top':b_mg,                                    'colour':'#94A3B8'},
        {'label':'Delist loss',      'bottom':b_mg+delist_loss,   'top':b_mg,                                    'colour':'#EF4444'},
        {'label':'Promote uplift',   'bottom':cursor+delist_loss, 'top':cursor+delist_loss+promote_gain,         'colour':'#10B981'},
        {'label':'Replace uplift',   'bottom':cursor+delist_loss+promote_gain, 'top':cursor+delist_loss+promote_gain+replace_gain, 'colour':'#10B981'},
        {'label':'Wastage saving',   'bottom':cursor+delist_loss+promote_gain+replace_gain, 'top':cursor+delist_loss+promote_gain+replace_gain+wast_saving, 'colour':'#8B5CF6'},
        {'label':'New margin',       'bottom':0,                  'top':new_mg,                                  'colour':'#10B981'},
    ]
    raw_vals = [b_mg, delist_loss, promote_gain, replace_gain, wast_saving, new_mg]

    fig_wf = go.Figure()
    for i, step in enumerate(wf_steps):
        fig_wf.add_trace(go.Bar(
            name=step['label'],
            x=[step['label']],
            y=[step['top'] - step['bottom']],
            base=[step['bottom']],
            marker_color=step['colour'],
            text=[f"SAR {raw_vals[i]:+,.0f}" if i not in [0, len(wf_steps)-1] else f"SAR {raw_vals[i]:,.0f}"],
            textposition='outside',
            textfont=dict(size=11),
            showlegend=False,
            width=0.5
        ))
    fig_wf.update_layout(
        barmode='overlay', height=380,
        yaxis_title='Weekly gross margin (SAR)',
        yaxis_tickformat=',.0f',
        yaxis=dict(tickprefix='SAR '),
        title='Weekly margin waterfall — impact of acting on all recommendations',
        title_font_size=13,
        margin=dict(t=50,b=0,l=0,r=0),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    st.plotly_chart(fig_wf, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-header">Working capital freed by delisting</div>', unsafe_allow_html=True)
        cap_cat = (delists.groupby('Category')['Stock_Value_SAR']
                   .sum().reset_index().sort_values('Stock_Value_SAR'))
        if len(cap_cat) > 0:
            fig_cap = px.bar(
                cap_cat, x='Stock_Value_SAR', y='Category', orientation='h',
                labels={'Stock_Value_SAR':'SAR','Category':''},
                color='Stock_Value_SAR',
                color_continuous_scale=['#DBEAFE','#3B82F6'],
                title='By category'
            )
            fig_cap.update_layout(height=280, title_font_size=12,
                                  coloraxis_showscale=False, margin=dict(t=30,b=0,l=0,r=0))
            st.plotly_chart(fig_cap, use_container_width=True)
        else:
            st.info("No delist candidates in current filters.")

    with col2:
        st.markdown('<div class="section-header">Full P&L summary</div>', unsafe_allow_html=True)
        summary_data = {
            'Metric': ['Weekly revenue (SAR)','Weekly gross margin (SAR)',
                       'Gross margin %','Weekly wastage cost (SAR)',
                       'Active SKU count','Working capital freed (SAR)',
                       'Storage units freed','Annualised margin uplift (SAR)'],
            'Baseline': [f"{b_rev:,.0f}", f"{b_mg:,.0f}", f"{b_mg_pct:.1f}%",
                         f"{b_wast:,.0f}", str(len(df_filtered)), "—", "—", "—"],
            'Post-action': [f"{new_rev:,.0f}", f"{new_mg:,.0f}", f"{new_mg_pct:.1f}%",
                            f"{b_wast-wast_saving:,.0f}",
                            str(len(df_filtered)-len(delists)),
                            f"{freed_cap:,.0f}", str(freed_space),
                            f"{(new_mg-b_mg)*52:,.0f}"],
            'Change': [
                f"{(new_rev-b_rev)/max(b_rev,1)*100:+.1f}%",
                f"{(new_mg-b_mg)/max(b_mg,1)*100:+.1f}%",
                f"{new_mg_pct-b_mg_pct:+.1f}pp",
                f"{-wast_saving/max(b_wast,1)*100:+.1f}%",
                f"{-len(delists):+d}",
                "—","—",
                f"SAR {(new_mg-b_mg)*52:,.0f}"
            ]
        }
        df_summary = pd.DataFrame(summary_data)
        st.dataframe(df_summary.style.set_properties(**{'font-size':'12px'}),
                     use_container_width=True, height=320, hide_index=True)

    st.markdown("""
    <div class="warning-box">
    <b>Assumptions:</b> Promote = +25% revenue, +3% margin improvement. Replace = +15% margin from better supplier.
    Stock Up = +15% revenue uplift. Delist = full removal. Wastage saving = 60% reduction post reorder alignment.
    All figures are projections based on dummy data — calibrate against actual trading data before using in production.
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 7 — SCORING MODEL
# ══════════════════════════════════════════════════════════════════════════════
with tab7:
    st.markdown('<div class="section-header">Scoring pillars and weights</div>', unsafe_allow_html=True)

    model_data = {
        'Pillar': ['Profitability','Profitability','Profitability',
                   'Commercial momentum','Commercial momentum',
                   'Inventory health','Inventory health',
                   'Quality & supplier','Quality & supplier','Quality & supplier',
                   'Space productivity','Space productivity'],
        'Pillar weight': ['30%','30%','30%','20%','20%','17%','17%','14%','14%','14%','19%','19%'],
        'Metric': ['Gross margin %','Weekly margin SAR','Effective margin % (post-wastage)',
                   'Revenue trend MoM %','Sell-through efficiency',
                   'Days of stock','Lead time (days)',
                   'Supplier score','Customer rating','Return rate %',
                   'Margin per storage unit','Revenue per storage unit'],
        'Metric weight': ['12%','10%','8%','13%','7%','10%','7%','5%','6%','3%','12%','7%'],
        'Direction': ['Higher','Higher','Higher','Higher','Higher',
                      'Lower','Lower','Higher','Higher','Lower','Higher','Higher'],
        'Rationale': [
            'Core profitability signal',
            'Absolute margin contribution to P&L',
            'True margin after wastage cost deducted',
            'Raw MoM growth signal (seasonality-flagged)',
            'Units sold relative to stock held and lead time',
            'Less overstock = less capital tied up',
            'Shorter replenishment = more agile ordering',
            'Reliability, compliance, relationship strength',
            'Customer satisfaction and repeat purchase',
            'Product quality and description accuracy',
            'Margin generated per unit of storage space',
            'Revenue throughput per unit of space'
        ]
    }
    df_model = pd.DataFrame(model_data)

    def colour_direction(val):
        return 'color:#10B981;font-weight:600' if val=='Higher' else 'color:#EF4444;font-weight:600'

    st.dataframe(
        df_model.style
        .applymap(colour_direction, subset=['Direction'])
        .set_properties(**{'font-size':'12px'}),
        use_container_width=True, height=420, hide_index=True
    )

    st.markdown('<div class="section-header">Classification thresholds</div>', unsafe_allow_html=True)
    thresh_data = {
        'Score range': ['≥ 65','50–64','35–64','< 35','≥ 40 (override)'],
        'Additional condition': ['—','Raw trend ≥ 0','Raw trend < 0 or score < 50','—','Peak season within 4 weeks'],
        'Action': ['KEEP','PROMOTE','REPLACE','DELIST','STOCK UP'],
        'Rationale': [
            'Strong across all pillars. Protect range and pricing.',
            'Good foundations with growth momentum. Activate with visibility or promo investment.',
            'Below average. Source a stronger alternative SKU.',
            'Bottom tier. Drag on margin, space, and working capital. Remove from range.',
            'Seasonal demand surge imminent. Build stock to avoid stockout at peak.'
        ]
    }
    df_thresh = pd.DataFrame(thresh_data)
    st.dataframe(df_thresh.style.set_properties(**{'font-size':'12px'}),
                 use_container_width=True, height=220, hide_index=True)

    st.markdown('<div class="section-header">Normalisation formula</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.code("""
# Standard (higher is better)
Normalised = (Value − Min) / (Max − Min) × 100

# Inverted (lower is better)
Normalised = 100 − [(Value − Min) / (Max − Min) × 100]

# Applied to: days of stock, lead time, return rate,
# space units (inverted — fewer units = more efficient)
        """, language='python')
    with col2:
        st.markdown("""
        **Why min-max normalisation?**

        Every metric uses different units — SAR amounts, percentages, days. 
        Without normalisation, a weekly margin of SAR 2,000 would dominate 
        a customer rating of 4.2 simply because it's a larger number.

        Min-max converts every metric to 0–100, where:
        - **0** = worst performing SKU in the catalogue for that metric
        - **100** = best performing SKU in the catalogue

        This ensures weights are the only driver of relative importance.

        **Limitation:** sensitive to outliers — one unusually high SKU 
        compresses all others. In production, cap outliers before normalising.
        """)

    st.markdown("""
    <div class="info-box">
    <b>Production enhancements:</b>
    Weights should be calibrated against historical delist/keep outcomes using a trained classifier (e.g. XGBoost).
    Thresholds should be back-tested against actual category manager decisions.
    Shelf life values should be pulled from supplier spec sheets per SKU, not category averages.
    Seasonality flags should derive from SKU-level historical sales curves.
    Sales-to-space data should pull from WMS shelf/pallet records.
    </div>
    """, unsafe_allow_html=True)
