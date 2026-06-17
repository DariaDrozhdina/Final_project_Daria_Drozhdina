"""
Weather and Socioeconomic Factors Associated with Antidepressant Prescribing
England vs Spain (2021–2025)  ·  Streamlit Presentation
"""

import numpy as np
import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import plotly.express as px
import streamlit.components.v1 as components
px_colors = px.colors.qualitative.Safe

st.set_page_config(
    page_title="Prescriptions England vs Spain",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  [data-testid="stAppViewContainer"] { background: #FAFAFA; }
  [data-baseweb="tab"] { font-size: 0.55rem !important; padding: 3px 7px !important; }
  [data-baseweb="tab-list"] { gap: 1px !important; }
  .kpi-box {
      background: white;
      border-radius: 10px;
      padding: 14px 16px 10px;
      box-shadow: 0 2px 6px rgba(0,0,0,0.08);
      text-align: center;
      position: relative;
      margin-bottom: 8px;
  }
  /* Global base font size bump */
  html, body, [class*="css"] { font-size: 16px; }
  .kpi-label { font-size: 1.0rem; color: #999; text-transform: uppercase; letter-spacing: 0.05em; }
  .kpi-value { font-size: 2.6rem; font-weight: 700; line-height: 1.15; margin: 3px 0 1px; }
  .kpi-sub   { font-size: 1.0rem; color: #bbb; }
  .kpi-growth { font-size: 1.0rem; position: absolute; bottom: 7px; right: 9px; }
  .up   { color: #CC0000; }
  .down { color: #1a7a1a; }
  .eng  { color: #012169; }
  .esp  { color: #D95427; }
  .sec-title {
      font-size: 1.0rem; font-weight: 700; letter-spacing: 0.1em;
      text-transform: uppercase; color: #555; margin: 0 0 8px;
  }
  /* Tabs — equal width, full spread, rounded */
  [data-testid="stTabs"] [role="tablist"] { display: flex; width: 100%; gap: 8px; border-bottom: none !important; }
  [data-testid="stTabs"] [role="tab"] { flex: 1; text-align: center; font-size: 1.25rem !important; font-weight: 800 !important; color: #D95427 !important; border-radius: 10px !important; border: 2px solid #D95427 !important; background: #fff !important; padding: 14px 0 !important; transition: all 0.2s; }
  [data-testid="stTabs"] [role="tab"][aria-selected="true"] { color: #fff !important; background: #D95427 !important; border: 2px solid #D95427 !important; border-radius: 10px !important; }
  [data-testid="stTabs"] [role="tab"] p { font-size: 1.25rem !important; font-weight: 800 !important; }
  /* Sidebar text white */
  [data-testid="stSidebar"],
  [data-testid="stSidebar"] *,
  [data-testid="stSidebar"] p,
  [data-testid="stSidebar"] span,
  [data-testid="stSidebar"] label,
  [data-testid="stSidebar"] div,
  [data-testid="stSidebar"] .st-emotion-cache-1gulkj5,
  section[data-testid="stSidebar"] label,
  section[data-testid="stSidebar"] span,
  section[data-testid="stSidebar"] p { color: white !important; }
  /* Slider and radio label text */
  [data-testid="stSlider"] label, [data-testid="stRadio"] label,
  [data-testid="stSlider"] p, [data-testid="stRadio"] p,
  [data-testid="stSlider"] span, [data-testid="stRadio"] span,
  .stSlider label, .stRadio label { color: #222 !important; font-size: 1.1rem !important; }
  /* Radio option text */
  [data-testid="stRadio"] div[role="radiogroup"] label span { color: #222 !important; font-size: 1.1rem !important; }
  /* Select slider tick labels */
  [data-testid="stSlider"] [data-testid="stMarkdownContainer"] p { color: #222 !important; font-size: 1.1rem !important; }
  /* Selectbox label text — dark */
  [data-testid="stSelectbox"] label,
  [data-testid="stSelectbox"] label p { color: #222 !important; }
  /* Selectbox — medium gray matching label text */
  [data-testid="stSelectbox"] > div > div {
    background-color: #555 !important;
    border: none !important;
    border-radius: 6px !important;
  }
  [data-testid="stSelectbox"] > div > div > div,
  [data-testid="stSelectbox"] span,
  [data-testid="stSelectbox"] p {
    color: #fff !important;
    font-size: 1.2rem !important;
    font-weight: 500 !important;
  }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# DATA
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data
def load_master():
    df = pd.read_csv("../EDA/data/Master_table_Spain_England.csv")
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    return df

@st.cache_data
def load_england_cities():
    df = pd.read_csv("../EDA/data/England_all_per_city.csv")
    df.columns = df.columns.str.strip()
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    return df

SOCIO_FILES = {
    "Median Age":                       ("../EDA/data/socioeconomic/median_age.csv",                      "wide"),
    "Housing Affordability Ratio":      ("../EDA/data/socioeconomic/housing_affordability_ratio.csv",     "wide"),
    "Gross Disposable Income (£/head)": ("../EDA/data/socioeconomic/gross_disposable_household_income.csv","wide"),
    "Unemployment Rate (%)":            ("../EDA/data/socioeconomic/unemployment_rate.csv",                "long"),
}

@st.cache_data
def load_socio(label):
    path, fmt = SOCIO_FILES[label]
    df = pd.read_csv(path)
    if fmt == "wide":
        df = df.melt(id_vars="city", var_name="year", value_name="value")
        df["year"] = df["year"].astype(int)
    else:
        df = df[["city", "year", "value"]]
    return df

@st.cache_data
def load_england_country_geojson():
    r = requests.get(
        "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
        "Countries_December_2022_UK_BUC/FeatureServer/0/query",
        params={"where": "CTRY22NM='England'", "outFields": "CTRY22NM", "f": "geojson", "outSR": "4326"},
        timeout=30,
    )
    data = r.json()
    for feat in data.get("features", []):
        feat["id"] = "England"
    return data

@st.cache_data
def load_combined_map_geojson():
    """England (ONS) + Spain (world GeoJSON) combined for Mapbox choropleth."""
    # England
    r_eng = requests.get(
        "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
        "Countries_December_2022_UK_BUC/FeatureServer/0/query",
        params={"where": "CTRY22NM='England'", "outFields": "CTRY22NM", "f": "geojson", "outSR": "4326"},
        timeout=30,
    )
    eng_feats = r_eng.json().get("features", [])
    for f in eng_feats:
        f["id"] = "England"

    # Spain
    r_esp = requests.get(
        "https://raw.githubusercontent.com/johan/world.geo.json/master/countries/ESP.geo.json",
        timeout=30,
    )
    esp_data = r_esp.json()
    # Support both FeatureCollection and single Feature
    if esp_data.get("type") == "FeatureCollection":
        esp_feats = esp_data["features"]
    else:
        esp_feats = [esp_data]
    for f in esp_feats:
        f["id"] = "Spain"

    return {"type": "FeatureCollection", "features": eng_feats + esp_feats}

@st.cache_data
def load_city_boundaries():
    NAME_MAP = {
        "Birmingham": "Birmingham", "Brighton": "Brighton and Hove",
        "Bristol": "Bristol, City of", "Canterbury": "Canterbury",
        "Exeter": "Exeter", "Leeds": "Leeds", "Manchester": "Manchester",
        "Middlesbrough": "Middlesbrough", "Newcastle upon Tyne": "Newcastle upon Tyne",
        "Nottingham": "Nottingham", "Peterborough": "Peterborough",
        "Plymouth": "Plymouth", "Sunderland": "Sunderland", "York": "York",
    }
    reverse = {v: k for k, v in NAME_MAP.items()}
    lad_url = "https://raw.githubusercontent.com/martinjc/UK-GeoJSON/master/json/administrative/eng/lad.json"
    rgn_url = ("https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
               "Regions_December_2022_EN_BUC/FeatureServer/0/query")
    ctr_url = ("https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
               "Countries_December_2022_UK_BUC/FeatureServer/0/query")

    all_lad = requests.get(lad_url, timeout=30).json()["features"]
    name_field = next(k for k in all_lad[0]["properties"] if k.upper().endswith("NM"))
    features = []
    for feat in all_lad:
        city = reverse.get(feat["properties"].get(name_field, ""))
        if city:
            feat["id"] = city; feat["properties"]["city"] = city; features.append(feat)

    r_lon = requests.get(rgn_url, params={"where": "RGN22NM='London'", "outFields": "RGN22NM", "f": "geojson", "outSR": "4326"})
    for feat in r_lon.json().get("features", []):
        feat["id"] = "London"; feat["properties"]["city"] = "London"; features.append(feat)

    geojson = {"type": "FeatureCollection", "features": features}

    def rings(geometry):
        out = []
        polys = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
        for poly in polys:
            for ring in poly:
                out.append(([c[1] for c in ring], [c[0] for c in ring]))
        return out

    england_rings = [r for feat in requests.get(ctr_url, params={"where": "CTRY22NM='England'", "outFields": "CTRY22NM", "f": "geojson", "outSR": "4326"}).json().get("features", []) for r in rings(feat["geometry"])]
    region_rings  = [r for feat in requests.get(rgn_url,  params={"where": "1=1",              "outFields": "RGN22NM",   "f": "geojson", "outSR": "4326"}).json().get("features", []) for r in rings(feat["geometry"])]
    return geojson, england_rings, region_rings


CITY_COORDS = {
    "Birmingham": (52.4862, -1.8904), "Brighton": (50.8225, -0.1372),
    "Bristol": (51.4545, -2.5879), "Canterbury": (51.2802, 1.0789),
    "Exeter": (50.7184, -3.5339), "Leeds": (53.8008, -1.5491),
    "London": (51.5074, -0.1278), "Manchester": (53.4808, -2.2426),
    "Middlesbrough": (54.5742, -1.2350), "Newcastle upon Tyne": (54.9783, -1.6178),
    "Nottingham": (52.9548, -1.1581), "Peterborough": (52.5695, -0.2405),
    "Plymouth": (50.3755, -4.1427), "Sunderland": (54.9061, -1.3838),
    "York": (53.9590, -1.0815),
}

YEARS = [2021, 2022, 2023, 2024, 2025]


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def fmt_m(n):
    return f"{n/1_000_000:.2f}M" if n >= 1_000_000 else f"{n/1_000:.0f}K"

def growth_badge(curr, prev):
    if prev is None or prev == 0:
        return ""  # no previous year (2021) — show nothing
    pct = (curr - prev) / prev * 100
    cls = "up" if pct > 0 else "down"
    return f"<span class='kpi-growth {cls}'>{'▲' if pct>0 else '▼'} {abs(pct):.1f}%</span>"

def kpi(label, val, sub, badge, color):
    # Keep everything on one line — multiline HTML breaks Streamlit's markdown parser
    return (
        f"<div class='kpi-box'>"
        f"<div class='kpi-label'>{label}</div>"
        f"<div class='kpi-value {color}'>{val}</div>"
        f"<div class='kpi-sub'>{sub}</div>"
        + (badge if badge else "")
        + "</div>"
    )

def annual(df, country, group, year, col):
    s = df[(df["country"] == country) & (df["group"] == group) & (df["year"] == year)]
    return s[col].sum() if col == "items" else s[col].mean()


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 0 — TITLE
# ══════════════════════════════════════════════════════════════════════════════

def slide_title():
    st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Barlow+Condensed:ital,wght@0,800;1,400;1,600&family=Open+Sans:wght@300;400&family=Raleway:wght@200;300;700;900&display=swap" rel="stylesheet">
    <style>
    [data-testid="stAppViewBlockContainer"],
    [data-testid="stVerticalBlock"],
    [data-testid="stMarkdownContainer"] { padding-top: 0 !important; padding-bottom: 0 !important; }
    .title-hero {
        margin: -8rem -8rem 2rem -8rem;
        padding: 0 8rem;
        min-height: 100vh;
        background: linear-gradient(to bottom, #7A9BBF 0%, #4D6A96 40%, #2E4A72 100%);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    .title-rule {
        width: 50px;
        height: 3px;
        background: #ffffff;
        border-radius: 2px;
        margin: 0 auto 2rem auto;
    }
    .title-h1 {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 3.8rem;
        font-weight: 400;
        color: #ffffff;
        max-width: 1700px;
        line-height: 1.4;
        margin: 0 0 2rem 0;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        text-align: center;
    }
    .title-countries {
        display: flex;
        align-items: center;
        gap: 3rem;
        margin-bottom: 0.6rem;
    }
    .title-country {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 10px;
    }
    .title-country-name {
        font-family: 'Raleway', sans-serif !important;
        font-size: 1.7rem;
        font-weight: 200;
        font-style: normal;
        color: #ffffff;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }
    .title-flag img {
        width: 120px;
        height: auto;
        border-radius: 6px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.35);
        display: block;
    }
    .title-vs {
        font-family: 'Raleway', sans-serif !important;
        font-size: 1.7rem;
        font-weight: 200;
        color: #ffffff;
        letter-spacing: 0.12em;
    }
    .title-years {
        font-family: 'Open Sans', sans-serif !important;
        font-size: clamp(1rem, 2vw, 2rem) !important;
        font-weight: 300 !important;
        color: #ffffff !important;
        letter-spacing: 0.15em !important;
        text-transform: uppercase !important;
        margin-top: 1.2rem !important;
    }
    .title-corner {
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        text-align: right;
        color: #ffffff;
        font-family: 'Open Sans', sans-serif;
        font-size: 14px;
        font-weight: 300;
        letter-spacing: 0.06em;
        line-height: 1.7;
        text-transform: uppercase;
    }
    .title-corner strong {
        display: block;
        color: rgba(255,255,255,0.7);
        font-weight: 500;
        font-size: 15px;
    }
    .title-scroll-hint {
        position: absolute;
        bottom: 1.8rem;
        left: 50%;
        transform: translateX(-50%);
        color: #ffffff;
        font-family: 'Open Sans', sans-serif;
        font-size: 0.9rem;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
    }
    .title-scroll-hint span {
        font-size: 0.95rem;
        animation: bob 1.8s ease-in-out infinite;
        display: block;
    }
    @keyframes bob {
        0%,100% { transform: translateY(0); }
        50%      { transform: translateY(7px); }
    }
    @keyframes fall {
        0%   { transform: translateY(-70px) rotate(0deg);   opacity: 0; }
        8%   { opacity: 1; }
        92%  { opacity: 1; }
        100% { transform: translateY(92vh) rotate(360deg); opacity: 0; }
    }
    .pill {
        position: absolute;
        border-radius: 50px;
        animation: fall linear infinite;
        pointer-events: none;
        z-index: 0;
    }
    .title-rule, .title-h1, .title-countries, .title-years {
        position: relative;
        z-index: 1;
    }
    .title-corner {
        position: absolute;
        z-index: 1;
        bottom: 1.8rem;
        right: 2.2rem;
    }
    .title-scroll-hint {
        position: absolute;
        z-index: 1;
        bottom: 1.8rem;
        left: 50%;
        transform: translateX(-50%);
    }
    </style>

    <div class='title-hero'>
        <!-- falling pills -->
        <div class='pill' style='left:4%;  width:12px;height:28px;background:linear-gradient(to bottom,rgba(255,255,255,0.525) 50%,rgba(220,30,30,0.453) 50%);animation-duration:9s; animation-delay:0s;  top:-70px;'></div>
        <div class='pill' style='left:12%; width:9px; height:22px;background:linear-gradient(to bottom,rgba(220,30,30,0.453) 50%,rgba(255,255,255,0.52) 50%);animation-duration:7s; animation-delay:1.5s;top:-70px;'></div>
        <div class='pill' style='left:19%; width:14px;height:34px;background:linear-gradient(to bottom,rgba(255,255,255,0.52) 50%,rgba(180,10,10,0.4525) 50%);animation-duration:11s;animation-delay:3s;  top:-70px;'></div>
        <div class='pill' style='left:27%; width:10px;height:24px;background:linear-gradient(to bottom,rgba(180,10,10,0.453) 50%,rgba(255,255,255,0.52) 50%);animation-duration:8s; animation-delay:0.8s;top:-70px;'></div>
        <div class='pill' style='left:35%; width:13px;height:30px;background:linear-gradient(to bottom,rgba(255,255,255,0.522) 50%,rgba(220,30,30,0.4528) 50%);animation-duration:12s;animation-delay:5s;  top:-70px;'></div>
        <div class='pill' style='left:42%; width:8px; height:20px;background:linear-gradient(to bottom,rgba(220,30,30,0.4525) 50%,rgba(255,255,255,0.518) 50%);animation-duration:7.5s;animation-delay:2s;  top:-70px;'></div>
        <div class='pill' style='left:50%; width:15px;height:36px;background:linear-gradient(to bottom,rgba(255,255,255,0.518) 50%,rgba(180,10,10,0.4522) 50%);animation-duration:10s;animation-delay:4.5s;top:-70px;'></div>
        <div class='pill' style='left:57%; width:11px;height:26px;background:linear-gradient(to bottom,rgba(180,10,10,0.4528) 50%,rgba(255,255,255,0.52) 50%);animation-duration:9s; animation-delay:1s;  top:-70px;'></div>
        <div class='pill' style='left:64%; width:10px;height:24px;background:linear-gradient(to bottom,rgba(255,255,255,0.52) 50%,rgba(220,30,30,0.453) 50%);animation-duration:13s;animation-delay:6s;  top:-70px;'></div>
        <div class='pill' style='left:71%; width:13px;height:32px;background:linear-gradient(to bottom,rgba(220,30,30,0.4522) 50%,rgba(255,255,255,0.518) 50%);animation-duration:8s; animation-delay:2.5s;top:-70px;'></div>
        <div class='pill' style='left:78%; width:9px; height:22px;background:linear-gradient(to bottom,rgba(255,255,255,0.525) 50%,rgba(180,10,10,0.453) 50%);animation-duration:10s;animation-delay:0.3s;top:-70px;'></div>
        <div class='pill' style='left:85%; width:14px;height:34px;background:linear-gradient(to bottom,rgba(180,10,10,0.452) 50%,rgba(255,255,255,0.522) 50%);animation-duration:7s; animation-delay:3.8s;top:-70px;'></div>
        <div class='pill' style='left:92%; width:11px;height:26px;background:linear-gradient(to bottom,rgba(255,255,255,0.518) 50%,rgba(220,30,30,0.4525) 50%);animation-duration:11s;animation-delay:1.8s;top:-70px;'></div>
        <div class='pill' style='left:8%;  width:8px; height:20px;background:linear-gradient(to bottom,rgba(220,30,30,0.453) 50%,rgba(255,255,255,0.52) 50%);animation-duration:14s;animation-delay:7s;  top:-70px;'></div>
        <div class='pill' style='left:23%; width:12px;height:28px;background:linear-gradient(to bottom,rgba(255,255,255,0.522) 50%,rgba(180,10,10,0.4525) 50%);animation-duration:9.5s;animation-delay:4s;  top:-70px;'></div>
        <div class='pill' style='left:46%; width:9px; height:22px;background:linear-gradient(to bottom,rgba(180,10,10,0.4528) 50%,rgba(255,255,255,0.52) 50%);animation-duration:8.5s;animation-delay:5.5s;top:-70px;'></div>
        <div class='pill' style='left:60%; width:14px;height:32px;background:linear-gradient(to bottom,rgba(255,255,255,0.52) 50%,rgba(220,30,30,0.4528) 50%);animation-duration:12s;animation-delay:2.2s;top:-70px;'></div>
        <div class='pill' style='left:75%; width:10px;height:24px;background:linear-gradient(to bottom,rgba(220,30,30,0.4525) 50%,rgba(255,255,255,0.518) 50%);animation-duration:7.5s;animation-delay:8s;  top:-70px;'></div>
        <div class='pill' style='left:88%; width:12px;height:30px;background:linear-gradient(to bottom,rgba(255,255,255,0.52) 50%,rgba(180,10,10,0.453) 50%);animation-duration:10s;animation-delay:3.2s;top:-70px;'></div>
        <div class='pill' style='left:31%; width:8px; height:20px;background:linear-gradient(to bottom,rgba(180,10,10,0.4522) 50%,rgba(255,255,255,0.522) 50%);animation-duration:13s;animation-delay:9s;  top:-70px;'></div>
        <div class='title-rule'></div>
        <div class='title-h1'>
            Weather &amp; Socioeconomic Factors<br>
            Associated with Antidepressant Prescribing
        </div>
        <div class='title-countries'>
            <div class='title-country'>
                <span class='title-country-name'>England</span>
                <span class='title-flag'><img src='https://flagcdn.com/gb-eng.svg' alt='England flag'></span>
            </div>
            <span class='title-vs'>vs</span>
            <div class='title-country'>
                <span class='title-country-name'>Spain</span>
                <span class='title-flag'><img src='https://flagcdn.com/es.svg' alt='Spain flag'></span>
            </div>
        </div>
        <div class='title-years' style='font-size:16px;'>2021 – 2025</div>
        <div class='title-corner' style='position:fixed;bottom:1.5rem;right:1.5rem;text-align:right;color:#fff;font-size:13px;line-height:1.6;font-family:Open Sans,sans-serif;letter-spacing:0.05em;'>
            Capstone Project · 2026<br>
            <strong style='font-size:14px;font-weight:600;opacity:0.8;'>Daria Drozhdina</strong>
        </div>
        <div class='title-scroll-hint'>scroll to explore <span>↓</span></div>
    </div>
    """, unsafe_allow_html=True)
    slide_introduction()


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 1 — INTRODUCTION
# ══════════════════════════════════════════════════════════════════════════════

def slide_introduction():
    st.markdown("""
    <style>
    .intro-card{background:#fff;border-radius:10px;border-left:5px solid #012169;
        padding:24px 28px;margin-bottom:20px;box-shadow:0 2px 8px rgba(0,0,0,.07);}
    .intro-card h3{font-family:Trebuchet MS,sans-serif;font-size:1.6rem;font-weight:900;
        color:#012169;margin:0 0 14px 0;text-transform:uppercase;letter-spacing:.06em;}
    .intro-card.red{border-left-color:#c0392b;}
    .intro-card.red h3{color:#c0392b;}
    .intro-card.gray{border-left-color:#555;}
    .intro-card.gray h3{color:#444;}
    .why-item{display:flex;align-items:flex-start;gap:10px;margin-bottom:10px;font-size:.93rem;color:#333;}
    .why-num{background:#012169;color:#fff;border-radius:50%;width:22px;height:22px;
        display:flex;align-items:center;justify-content:center;font-size:.72rem;
        font-weight:700;flex-shrink:0;margin-top:2px;}
    .hyp-item{display:flex;align-items:flex-start;gap:10px;margin-bottom:10px;font-size:1.08rem;color:#333;}
    .hyp-num{color:#555;font-weight:700;min-width:20px;}
    .pipeline-wrap{display:flex;align-items:flex-start;gap:0;padding:8px 0;flex-wrap:wrap;}
    .pipe-step{display:flex;flex-direction:column;align-items:center;min-width:145px;max-width:190px;}
    .pipe-box{background:#f4f6fb;border:1.5px solid #d0d8ea;border-radius:8px;
        padding:12px 10px;text-align:center;width:100%;}
    .pipe-title{font-size:.75rem;font-weight:700;color:#c0392b;text-transform:uppercase;
        letter-spacing:.05em;margin-bottom:8px;}
    .pipe-arrow{display:flex;align-items:center;font-size:1.5rem;color:#c0392b;
        padding:0 6px;margin-top:26px;}
    .src-item{display:flex;align-items:center;gap:6px;margin-bottom:5px;font-size:.78rem;}
    .src-item img{width:18px;height:18px;object-fit:contain;border-radius:3px;}
    .src-item a{color:#012169;text-decoration:none;font-weight:500;}
    .src-item a:hover{text-decoration:underline;}
    .tool-badge{background:#e8ecf5;border-radius:4px;padding:3px 8px;font-size:.76rem;
        color:#012169;font-weight:600;margin:3px 2px;display:inline-block;}
    .why-subcards{display:flex;gap:14px;flex-wrap:wrap;margin-top:4px;}
    .why-sub{flex:1;min-width:180px;min-height:160px;background:#f4f6fb;border-radius:8px;padding:18px 18px;border-top:3px solid #012169;}
    .why-sub-title{font-size:1.35rem;font-weight:700;color:#012169;text-transform:uppercase;letter-spacing:.04em;margin-bottom:10px;}
    .why-sub-body{font-size:1.08rem;color:#444;line-height:1.6;}
    .pipe2-wrap{display:flex;gap:0;align-items:flex-start;width:100%;}
    .pipe2-card{flex:1;background:#f4f6fb;border-radius:8px;padding:16px 14px;border-top:3px solid #c0392b;min-height:220px;}
    .pipe2-title{font-size:.8rem;font-weight:700;color:#c0392b;text-transform:uppercase;letter-spacing:.06em;margin-bottom:12px;}
    .pipe2-arrow{display:flex;align-items:center;justify-content:center;font-size:1.4rem;color:#c0392b;padding:0 8px;margin-top:40px;flex-shrink:0;}
    .pipe2-sub{background:#fff;border-radius:6px;padding:8px 10px;margin-bottom:8px;border-left:3px solid #c0392b;}
    .pipe2-sub-title{font-size:.72rem;font-weight:700;color:#c0392b;text-transform:uppercase;letter-spacing:.04em;margin-bottom:5px;}
    .pipe2-src{font-size:.78rem;color:#333;display:flex;align-items:center;gap:5px;margin-bottom:3px;}
    .pipe2-src a{color:#012169;text-decoration:none;font-weight:500;}
    .nhs-badge{background:#005EB8;color:white;font-weight:900;font-size:.6rem;padding:2px 5px;border-radius:2px;flex-shrink:0;letter-spacing:.02em;}
    .src-dot{color:white;font-weight:700;font-size:.55rem;padding:2px 4px;border-radius:2px;flex-shrink:0;letter-spacing:.02em;}
    .pipe2-src a:hover{text-decoration:underline;}
    .pipe2-method{display:flex;flex-direction:column;gap:8px;margin-bottom:8px;}
    .pipe2-method-box{background:#fff;border-radius:6px;padding:8px 12px;border-left:3px solid #c0392b;}
    .pipe2-method-label{font-size:.72rem;font-weight:700;color:#c0392b;text-transform:uppercase;letter-spacing:.04em;margin-bottom:4px;}
    .pipe2-method-items{font-size:.72rem;color:#555;line-height:1.7;}
    .tool-logo{display:flex;align-items:center;gap:8px;margin-bottom:6px;}
    .tool-logo-badge{border-radius:5px;padding:3px 8px;font-size:.72rem;font-weight:700;color:#fff;}
    .tool-logo-name{font-size:.78rem;color:#333;}
    </style>
    """, unsafe_allow_html=True)

    # ── Card 1: Why these countries? ─────────────────────────────────────────
    st.markdown("""
    <div class='intro-card'>
      <h3>Why these countries?</h3>
      <div class='why-subcards'>
        <div class='why-sub'>
          <div class='why-sub-title'>1 · Data is Available</div>
          <div class='why-sub-body'><span style='color:#012169;font-weight:600;'>England</span>: granular per practitioner &amp; month<br><span style='color:#D95427;font-weight:600;'>Spain</span>: national totals per month</div>
        </div>
        <div class='why-sub'>
          <div class='why-sub-title'>2 · Healthcare Systems</div>
          <div class='why-sub-body'>Both universal &amp; public:<br><span style='color:#012169;font-weight:600;'>England</span>: NHS (National Health Service)<br><span style='color:#D95427;font-weight:600;'>Spain</span>: SNS (Sistema Nacional de Salud)</div>
        </div>
        <div class='why-sub'>
          <div class='why-sub-title'>3 · Economic Weight</div>
          <div class='why-sub-body'><span style='color:#012169;font-weight:600;'>England</span>: 7th globally <span style='font-size:1.2rem;font-weight:700;color:#012169;'>€2.9T</span><br><span style='color:#D95427;font-weight:600;'>Spain</span>: 14th globally <span style='font-size:1.2rem;font-weight:700;color:#D95427;'>€1.6T</span><br><span style='color:#999;font-size:.88rem;'>GDP, 2025</span></div>
        </div>
        <div class='why-sub'>
          <div class='why-sub-title'>4 · Climate</div>
          <div class='why-sub-body'><span style='color:#012169;font-weight:600;'>England</span>: ~1,500 sun hrs/yr<br><span style='color:#D95427;font-weight:600;'>Spain</span>: ~2,700 sun hrs/yr</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Card 2: Data sources pipeline — horizontal flow ──────────────────────
    components.html("""
<style>
* { box-sizing:border-box; margin:0; padding:0; }
body { font-family:'Trebuchet MS',sans-serif; background:transparent; }
.pc { background:#fff; border-radius:10px; border-left:5px solid #c0392b; padding:24px 28px; box-shadow:0 2px 8px rgba(0,0,0,.07); }
.pc h3 { font-size:1.6rem; font-weight:900; color:#c0392b; margin:0 0 52px 0; text-transform:uppercase; letter-spacing:.06em; }
/* Staggered entrance animation */
@keyframes fadeUp { from { opacity:0; transform:translateY(16px); } to { opacity:1; transform:translateY(0); } }
.col, .gap-lines, .gap-arr { opacity:0; }
.col.show { animation: fadeUp 0.55s ease forwards; }
.gap-arr.show { animation: fadeUp 0.4s ease forwards; }
/* Horizontal flow row */
.flow { display:flex; align-items:flex-start; position:relative; }
/* Each column */
.col { display:flex; flex-direction:column; }
.col-lbl { font-size:1.15rem; font-weight:900; color:#c0392b; text-transform:uppercase; letter-spacing:.07em; margin-bottom:12px; }
/* Source column */
.col-src { flex:1.2; }
.grp-lbl { font-size:.78rem; font-weight:700; color:#aaa; text-transform:uppercase; letter-spacing:.05em; margin:10px 0 5px 0; }
.grp-lbl:first-of-type { margin-top:0; }
.src-card { background:#f4f6fb; border-radius:5px; padding:9px 12px; margin-bottom:5px; font-size:1.05rem; font-weight:700; }
.src-card.api { border-left:3px solid #c0392b; }
.src-card.man { border-left:3px solid #9ab; }
.src-card a { text-decoration:none; font-weight:700; color:#012169; }
.src-card a:hover { text-decoration:underline; }
/* Gap for lines */
.gap-lines { width:56px; flex-shrink:0; }
/* Extraction column */
.col-ext { flex:1; }
.ext-card { background:#f4f6fb; border-radius:6px; padding:13px 15px; margin-bottom:12px; }
.ext-card.api { border-left:3px solid #c0392b; }
.ext-card.man { border-left:3px solid #9ab; }
.ext-lbl { font-size:1.05rem; font-weight:700; text-transform:uppercase; letter-spacing:.05em; margin-bottom:0; }
.ext-lbl.api { color:#c0392b; }
.ext-lbl.man { color:#778; }
.ext-item { font-size:.87rem; color:#555; padding:1px 0; }
/* Arrow gap */
.gap-arr { width:40px; flex-shrink:0; display:flex; align-items:center; justify-content:center; font-size:1.2rem; color:#c0392b; }
/* Tool columns */
.col-tool { flex:1; }
.tool-card { background:#f4f6fb; border-radius:6px; padding:14px 16px; border-left:3px solid #c0392b; }
.t-row { display:flex; align-items:center; gap:10px; margin-bottom:10px; }
.t-row:last-child { margin-bottom:0; }
.tbadge { border-radius:4px; padding:4px 8px; font-size:.85rem; font-weight:700; color:#fff; }
.tname { font-size:1.05rem; font-weight:700; color:#333; }
/* SVG overlay */
#ov { position:absolute; top:0; left:0; pointer-events:none; overflow:visible; opacity:0; transition: opacity 0.4s; }
</style>

<div class="pc">
<h3>Data Sources &amp; Pipeline</h3>
<div class="flow" id="flow">

<div class="col col-src" style="opacity:0">
<div class="col-lbl">1. Sources</div>
<div class="grp-lbl">Pharmaceutical</div>
<div class="src-card api" id="s-nhs"><a href="https://opendata.nhsbsa.net/dataset/english-prescribing-dataset-epd-with-snomed-code" target="_blank">NHS BSA Open Data</a></div>
<div class="src-card man" id="s-san"><a href="https://www.sanidad.gob.es/areas/farmacia/consumoMedicamentos/ATC/home.htm" target="_blank">Ministerio de Sanidad</a></div>
<div class="grp-lbl">Weather</div>
<div class="src-card api" id="s-met"><a href="https://meteostat.net/en/" target="_blank">Meteostat</a></div>
<div class="src-card man" id="s-mo"><a href="https://www.metoffice.gov.uk/research/climate/maps-and-data/historic-station-data" target="_blank">Met Office</a></div>
<div class="grp-lbl">Socioeconomic</div>
<div class="src-card man" id="s-ons"><a href="https://www.ons.gov.uk/" target="_blank">ONS England</a></div>
<div class="src-card man" id="s-ine"><a href="https://www.ine.es/" target="_blank">INE Spain</a></div>
</div>

<div class="gap-lines" style="opacity:0"></div>

<div class="col col-ext" style="opacity:0">
<div class="col-lbl">2. Extraction</div>
<div class="ext-card api" id="m-api-nhs">
<div class="ext-lbl api">API</div>
</div>
<div class="ext-card man" id="m-man-san">
<div class="ext-lbl man">Manual</div>
</div>
</div>

<div class="gap-arr" style="opacity:0">→</div>

<div class="col col-tool" id="col-clean" style="opacity:0">
<div class="col-lbl" style="display:flex;"><span style="flex-shrink:0;">3.&nbsp;</span><span>Cleaning &amp; Transforming</span></div>
<div class="tool-card" id="m-clean">
<div class="t-row"><img src="https://cdn.simpleicons.org/python/3776AB" width="22" height="22"><span class="tname">Python</span></div>
<div class="t-row"><img src="https://cdn.simpleicons.org/postgresql/336791" width="22" height="22"><span class="tname">PostgreSQL</span></div>
</div>
</div>

<div class="gap-arr" id="arr2" style="opacity:0">→</div>

<div class="col col-tool" id="col-vis" style="opacity:0">
<div class="col-lbl">4. Visualisation</div>
<div class="tool-card">
<div class="t-row"><img src="https://cdn.simpleicons.org/plotly/3F4F75" width="22" height="22"><span class="tname">Plotly</span></div>
<div class="t-row"><img src="https://cdn.simpleicons.org/streamlit/FF4B4B" width="22" height="22"><span class="tname">Streamlit</span></div>
</div>
</div>

<svg id="ov"></svg>
</div>
</div>

<script>
function draw() {
  var flow = document.getElementById('flow');
  var svg  = document.getElementById('ov');
  var fr   = flow.getBoundingClientRect();
  svg.setAttribute('width',  fr.width);
  svg.setAttribute('height', fr.height);
  svg.innerHTML = '';
  function curve(sid, tid, col, w) {
    var se = document.getElementById(sid), te = document.getElementById(tid);
    if (!se || !te) return;
    var sr = se.getBoundingClientRect(), tr = te.getBoundingClientRect();
    var x1 = sr.right - fr.left, y1 = sr.top + sr.height/2 - fr.top;
    var x2 = tr.left  - fr.left, y2 = tr.top + tr.height/2 - fr.top;
    var mx = (x1+x2)/2;
    var p = document.createElementNS('http://www.w3.org/2000/svg','path');
    p.setAttribute('d','M'+x1+' '+y1+' C'+mx+' '+y1+' '+mx+' '+y2+' '+x2+' '+y2);
    p.setAttribute('fill','none'); p.setAttribute('stroke',col);
    p.setAttribute('stroke-width',w); p.setAttribute('opacity','0.75');
    svg.appendChild(p);
  }
  curve('s-nhs','m-api-nhs','#c0392b',1.8);
  curve('s-met','m-api-nhs','#c0392b',1.8);
  curve('s-san','m-man-san','#9ab',1.4);
  curve('s-mo', 'm-man-san','#9ab',1.4);
  curve('s-ons','m-man-san','#9ab',1.4);
  curve('s-ine','m-man-san','#9ab',1.4);
}
function centerAll() {
  var flow    = document.getElementById('flow');
  var fr      = flow.getBoundingClientRect();
  var srcCol  = document.querySelector('.col-src');
  var srcRect = srcCol.getBoundingClientRect();
  var srcMid  = srcRect.top + srcRect.height / 2 - fr.top;

  // Center extraction cards (first card gets the margin-top)
  var extCol   = document.querySelector('.col-ext');
  var extLblH  = extCol.querySelector('.col-lbl').offsetHeight + 10;
  var extCards = extCol.querySelectorAll('.ext-card');
  var extH = 0;
  extCards.forEach(function(c){ extH += c.offsetHeight + 10; });
  extH -= 10;
  var extMt = Math.max(0, srcMid - extLblH - extH / 2);
  extCards[0].style.marginTop = extMt + 'px';

  // Center tool cards
  ['col-clean','col-vis'].forEach(function(id) {
    var col   = document.getElementById(id);
    var lbl   = col.querySelector('.col-lbl').offsetHeight + 10;
    var card  = col.querySelector('.tool-card');
    var mt    = Math.max(0, srcMid - lbl - card.offsetHeight / 2);
    card.style.marginTop = mt + 'px';
  });

  // Center arrows
  document.querySelectorAll('.gap-arr').forEach(function(el) {
    el.style.paddingTop = Math.max(0, srcMid - 12) + 'px';
  });
}
// Staggered animation order: src, gap-lines, ext, arr1, clean, arr2, vis
var animEls = [
  document.querySelector('.col-src'),
  document.querySelector('.gap-lines'),
  document.querySelector('.col-ext'),
  document.querySelectorAll('.gap-arr')[0],
  document.getElementById('col-clean'),
  document.querySelectorAll('.gap-arr')[1],
  document.getElementById('col-vis'),
];

function triggerAnimation() {
  // Center and draw lines BEFORE animation starts (elements are hidden but laid out correctly)
  centerAll();
  draw();
  var total = animEls.length;
  animEls.forEach(function(el, i) {
    if (!el) return;
    setTimeout(function() { el.classList.add('show'); }, i * 220);
  });
  // Show SVG lines as Sources finishes its fade-in
  setTimeout(function(){
    document.getElementById('ov').style.opacity = '1';
  }, 600);
}

var observer = new IntersectionObserver(function(entries) {
  entries.forEach(function(e) {
    if (e.isIntersecting) {
      triggerAnimation();
      observer.disconnect();
    }
  });
}, { threshold: 0.85 });

observer.observe(document.querySelector('.flow'));
window.addEventListener('resize', function(){ centerAll(); draw(); });
</script>
""", height=510)

    # ── Card 3: Hypotheses ────────────────────────────────────────────────────
    st.markdown("""
    <div class='intro-card gray'>
      <h3>My Hypotheses</h3>
      <div class='hyp-item'><span class='hyp-num'>1.</span>
        <span>England has a higher level of antidepressant prescriptions than Spain.</span>
      </div>
      <div class='hyp-item'><span class='hyp-num'>2.</span>
        <span>The amount of sun hours affects prescription rates in both countries.</span>
      </div>
      <div class='hyp-item'><span class='hyp-num'>3.</span>
        <span>Bigger cities have higher rates of antidepressant prescriptions.</span>
      </div>
      <div class='hyp-item'><span class='hyp-num'>4.</span>
        <span>Economic wellbeing of citizens strongly correlates with depression levels.</span>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 2 — OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════

def slide_overview():
    master = load_master()

    # ── Controls row (defined before columns so both are available everywhere) ──
    ctrl_l, ctrl_r = st.columns([0.74, 1], gap="large")
    with ctrl_l:
        st.markdown("<p style='font-size:0.85rem;font-weight:700;color:#555;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:0px;'>Year</p>", unsafe_allow_html=True)
        year = st.select_slider(
            "Year", options=YEARS, value=2021, key="ov_year", label_visibility="collapsed",
        )
    with ctrl_r:
        st.markdown("<p style='font-size:0.85rem;font-weight:700;color:#555;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:4px;'>Packs Issued</p>", unsafe_allow_html=True)
        metric = st.selectbox(
            "Packs Issued",
            ["Total", "Per 1,000 population"],
            key="ov_metric",
            label_visibility="collapsed",
        )
    # initialise drug_group key so col_left can read it before the widget renders
    if "ov_drug_group" not in st.session_state:
        st.session_state["ov_drug_group"] = "Antidepressants"
    drug_group_pre = st.session_state["ov_drug_group"]

    # ── Two-column layout ─────────────────────────────────────────────────────
    col_left, col_right = st.columns([0.74, 1], gap="large")

    # ════ LEFT: Map ═══════════════════════════════════════════════════════════
    with col_left:

        st.markdown("<p style='font-size:0.85rem;font-weight:700;color:#555;text-transform:uppercase;letter-spacing:0.07em;margin:10px 0 4px;'>Annual Sunshine Hours</p>", unsafe_allow_html=True)
        with st.spinner("Loading map…"):
            eng_geo = load_england_country_geojson()

        # ── Sunshine hours for map ────────────────────────────────────────────
        m_yr = master[master["year"] == year]
        m_prev_map = master[master["year"] == year - 1] if year > 2021 else None

        def sun_vals(country):
            cur = m_yr[(m_yr["country"]==country) & (m_yr["group"]=="Antidepressants")]
            sun_annual = cur["tsun_mean"].sum() / 60          # annual hours (for color)
            sun_daily  = cur["tsun_mean"].mean() / 60 / 30.44 # daily hours (for label)
            pop = cur["population"].mean()
            if m_prev_map is not None:
                prev = m_prev_map[(m_prev_map["country"]==country) & (m_prev_map["group"]=="Antidepressants")]
                prev_annual = prev["tsun_mean"].sum() / 60
                pct = (sun_annual - prev_annual) / prev_annual * 100 if prev_annual else 0
                growth_str = f"{'▲' if pct>=0 else '▼'} {abs(pct):.1f}% vs {year-1}"
            else:
                growth_str = "—"
            return round(sun_annual), round(sun_daily, 1), pop, growth_str

        sun_eng, sun_eng_day, pop_eng, gr_eng = sun_vals("England")
        sun_esp, sun_esp_day, pop_esp, gr_esp = sun_vals("Spain")

        # Fixed range across all years (daily hrs) so colorbar is stable when sliding
        all_sun = [
            master[(master["country"]==c) & (master["group"]=="Antidepressants") & (master["year"]==y)]["tsun_mean"].sum() / 60 / 365
            for c in ["England", "Spain"] for y in YEARS
        ]
        zmin = min(all_sun) * 0.95
        zmax = max(all_sun) * 1.02
        sun_scale = [[0, "#3A6A9A"], [0.5, "#A0603A"], [1, "#E8703A"]]

        fig_map = go.Figure()
        # Spain
        fig_map.add_trace(go.Choropleth(
            locations=["ESP"], z=[sun_esp/365], locationmode="ISO-3",
            customdata=[[f"{pop_esp/1e6:.2f}M", gr_esp, int(sun_esp)]],
            colorscale=sun_scale, zmin=zmin, zmax=zmax, showscale=False,
            marker=dict(line=dict(color="rgba(0,0,0,0)", width=0)),
            hovertemplate=(
                "<b>Spain</b><br>"
                "☀️ %{customdata[2]:,} hrs/yr<extra></extra>"
            ),
        ))
        # England
        fig_map.add_trace(go.Choropleth(
            geojson=eng_geo, locations=["England"], z=[sun_eng/365],
            customdata=[[f"{pop_eng/1e6:.2f}M", gr_eng, int(sun_eng)]],
            colorscale=sun_scale, zmin=zmin, zmax=zmax,
            colorbar=dict(
                title=dict(text="Sun hrs/day", font=dict(size=15, color="#CCC")),
                tickfont=dict(color="#CCC", size=14),
                thickness=14, len=0.5, x=0.97,
                bgcolor="rgba(0,0,0,0)",
                borderwidth=0,
            ),
            marker=dict(line=dict(color="rgba(0,0,0,0)", width=0)),
            hovertemplate=(
                "<b>England</b><br>"
                "☀️ %{customdata[2]:,} hrs/yr<extra></extra>"
            ),
        ))
        # Country names — large
        # Country names — larger
        fig_map.add_trace(go.Scattergeo(
            lat=[40.4, 52.5], lon=[-3.7, -1.8],
            text=["Spain", "England"], mode="markers+text",
            textposition="middle center",
            marker=dict(size=0, color="rgba(0,0,0,0)"),
            textfont=dict(size=24, color="white", family="Trebuchet MS, sans-serif"),
            hoverinfo="skip", showlegend=False,
        ))
        # Daily sun hours
        fig_map.add_trace(go.Scattergeo(
            lat=[38.6, 51.1], lon=[-3.7, -1.8],
            text=[f"~{sun_esp_day} hrs/day", f"~{sun_eng_day} hrs/day"],
            mode="markers+text",
            textposition="middle center",
            marker=dict(size=0, color="rgba(0,0,0,0)"),
            textfont=dict(size=14, color="rgba(255,255,255,0.5)", family="Trebuchet MS, sans-serif"),
            hoverinfo="skip", showlegend=False,
        ))
        fig_map.update_layout(
            geo=dict(
                scope="europe", resolution=50,
                projection=dict(type="mercator"),
                lonaxis=dict(range=[-11, 5]),
                lataxis=dict(range=[35, 58]),
                showland=True,    landcolor="#1E2235",
                showocean=True,   oceancolor="#0D1520",
                showcountries=True, countrycolor="#3A405C",
                showcoastlines=False,
                showlakes=True,   lakecolor="#0D1520",
                bgcolor="#0D1520",
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=0, b=0, l=0, r=0),
            height=546,
            dragmode=False,
        )
        st.markdown("""
        <style>
        [data-testid="stPlotlyChart"] {
            padding: 0 !important;
            margin: 0 !important;
            background: #0D1520 !important;
            border-radius: 8px;
            overflow: hidden;
        }
        [data-testid="stPlotlyChart"] > div { padding: 0 !important; background: #0D1520 !important; }
        </style>""", unsafe_allow_html=True)
        st.plotly_chart(fig_map, use_container_width=True, config={"scrollZoom": False, "displayModeBar": False, "doubleClick": False})

        if year == 2025 and metric == "Per 1,000 population":
            dg = st.session_state.get("ov_drug_group", "Antidepressants")
            cards_html = """
<div style='display:flex;flex-direction:column;gap:10px;margin-top:10px;'>
  <div style='background:#eef3ff;border-left:4px solid #012169;border-radius:8px;padding:12px 16px;'>
    <div style='font-size:0.9rem;font-weight:700;text-transform:uppercase;letter-spacing:0.07em;color:#012169;margin-bottom:6px;'>Hypothesis 1 — Confirmed</div>
    <div style='font-size:1.1rem;color:#222;line-height:1.5;'>England consistently prescribes more antidepressants per 1,000 population than Spain across all years studied (2021–2025).</div>
  </div>"""
            if dg == "Antidepressants + Anxiolytics":
                cards_html += """
  <div style='background:#fff8f0;border-left:4px solid #D95427;border-radius:8px;padding:12px 16px;'>
    <div style='font-size:0.9rem;font-weight:700;text-transform:uppercase;letter-spacing:0.07em;color:#D95427;margin-bottom:6px;'>Unexpected Insight</div>
    <div style='font-size:1.1rem;color:#222;line-height:1.5;'>Anxiolytic prescribing in Spain is <strong>falling</strong> — overall antidepressant growth tempo is <strong>accelerating faster</strong>, narrowing the gap.</div>
  </div>"""
            cards_html += "\n</div>"
            st.markdown(cards_html, unsafe_allow_html=True)

    # ════ RIGHT: KPIs + Line chart ════════════════════════════════════════════
    with col_right:

        m_prev = master[master["year"] == year - 1] if year > 2021 else None

        def get(country, group):
            sub  = master[(master["country"]==country) & (master["group"]==group) & (master["year"]==year)]
            if metric == "Total":
                cur = sub["items"].sum()
            elif metric == "Per 1,000 population":
                cur = sub["items_per_1k"].sum()
            else:  # per whole population
                pop = sub["population"].mean()
                cur = sub["items"].sum() / pop if pop > 0 else 0
            if m_prev is not None:
                sp = m_prev[(m_prev["country"]==country) & (m_prev["group"]==group)]
                if metric == "Total":
                    prev = sp["items"].sum()
                elif metric == "Per 1,000 population":
                    prev = sp["items_per_1k"].sum()
                else:
                    pop = sp["population"].mean()
                    prev = sp["items"].sum() / pop if pop > 0 else 0
            else:
                prev = None
            return cur, prev

        eng_ad, p_eng_ad = get("England", "Antidepressants")
        esp_ad, p_esp_ad = get("Spain",   "Antidepressants")
        eng_ax, p_eng_ax = get("England", "Anxiolytics")
        esp_ax, p_esp_ax = get("Spain",   "Anxiolytics")

        if metric == "Total":
            fmt = fmt_m
        elif metric == "Per 1,000 population":
            fmt = lambda x: f"{x:.0f}"
        else:  # per whole population
            fmt = lambda x: f"{x:.3f}"
        sub_label = "packs"

        # Two columns: one per country, both drug groups stacked inside
        kc1, kc2 = st.columns(2)

        def small_badge(curr, prev):
            if prev is None or prev == 0:
                return ""
            pct = (curr - prev) / prev * 100
            color = "#CC0000" if pct > 0 else "#1a7a1a"
            arrow = "▲" if pct > 0 else "▼"
            return f"<span style='font-size:1.3rem;position:absolute;bottom:0;right:2px;color:{color};font-weight:700;'>{arrow} {abs(pct):.1f}%</span>"

        def vs_badge(eng_val, esp_val):
            """Small bottom-right badge: how much more/less England is vs Spain."""
            if esp_val == 0:
                return ""
            pct = (eng_val - esp_val) / esp_val * 100
            arrow = "▲" if pct > 0 else "▼"
            higher_lower = "higher" if pct > 0 else "lower"
            tip_text = f"England&#39;s prescribing rate is {abs(pct):.1f}% {higher_lower} than Spain&#39;s in {year}"
            return (
                f"<span style='position:absolute;top:50%;right:8px;transform:translateY(-50%);"
                f"display:inline-flex;align-items:center;gap:4px;'>"
                f"<span style='font-size:1.1rem;font-weight:700;color:#012169;"
                f"background:#f0f3ff;border-radius:4px;padding:2px 8px;'>"
                f"{arrow} {abs(pct):.1f}%</span>"
                f"<span style='position:relative;display:inline-block;'>"
                f"<span style='font-size:0.95rem;color:#888;cursor:pointer;font-weight:700;"
                f"border:1.5px solid #bbb;border-radius:50%;width:18px;height:18px;"
                f"display:inline-flex;align-items:center;justify-content:center;line-height:1;"
                f"' class='tip-trigger'>ⓘ"
                f"<span style='display:none;position:absolute;bottom:130%;right:0;"
                f"background:#333;color:#fff;font-size:0.82rem;font-weight:400;"
                f"border-radius:6px;padding:6px 10px;white-space:nowrap;"
                f"box-shadow:0 2px 8px rgba(0,0,0,0.2);z-index:99;pointer-events:none;'"
                f" class='tip-box'>{tip_text}</span>"
                f"</span></span></span>"
                f"<style>"
                f".tip-trigger:hover .tip-box {{display:block !important;}}"
                f"</style>"
            )

        def country_card(flag, country_name, ad_val, p_ad, ax_val, p_ax, color,
                         ad_badge="", ax_badge=""):
            return (
                f"<div class='kpi-box' style='padding:2px 16px 4px;position:relative;'>"
                f"<div class='kpi-label' style='font-size:1.25rem;font-weight:700;color:#333;margin-bottom:4px;'>{flag} {country_name}</div>"
                f"<div style='margin-bottom:4px;position:relative;'>"
                f"{ad_badge}"
                f"<div class='kpi-label' style='font-size:1.0rem;'>Antidepressants</div>"
                f"<div class='kpi-value {color}' style='font-size:2.4rem;'>{fmt(ad_val)}</div>"
                f"<div class='kpi-sub' style='font-size:1.0rem;'>{sub_label}</div>"
                + f"</div>"
                + f"<hr style='border:none;border-top:1px solid #f0f0f0;margin:2px 0;'/>"
                + f"<div style='position:relative;'>"
                + f"{ax_badge}"
                + f"<div class='kpi-label' style='font-size:1.0rem;'>Anxiolytics</div>"
                + f"<div class='kpi-value {color}' style='font-size:1.5rem;font-weight:600;'>{fmt(ax_val)}</div>"
                + f"<div class='kpi-sub' style='font-size:1.0rem;'>{sub_label}</div>"
                + f"</div>"
                f"</div>"
            )

        kc1, kc2 = st.columns(2)
        with kc1:
            st.markdown(country_card(
                "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "England", eng_ad, p_eng_ad, eng_ax, p_eng_ax, "eng",
                ad_badge=vs_badge(eng_ad, esp_ad),
                ax_badge=vs_badge(eng_ax, esp_ax),
            ), unsafe_allow_html=True)
        with kc2:
            st.markdown(country_card("🇪🇸", "Spain", esp_ad, p_esp_ad, esp_ax, p_esp_ax, "esp"), unsafe_allow_html=True)

        # ── Line chart ────────────────────────────────────────────────────────
        st.markdown("<p style='font-size:0.85rem;font-weight:700;color:#555;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:4px;'>Group of drug</p>", unsafe_allow_html=True)
        drug_group = st.selectbox(
            "Group of drug",
            ["Antidepressants", "Anxiolytics", "Antidepressants + Anxiolytics"],
            key="ov_drug_group",
            label_visibility="collapsed",
        )

        all_series = [
            ("England", "Antidepressants", "#012169", "solid", "England — Antidepressants"),
            ("England", "Anxiolytics",     "#4A6FBF", "dot",   "England — Anxiolytics"),
            ("Spain",   "Antidepressants", "#D95427", "solid", "Spain — Antidepressants"),
            ("Spain",   "Anxiolytics",     "#F0966A", "dot",   "Spain — Anxiolytics"),
        ]
        if drug_group == "Antidepressants":
            series = [s for s in all_series if s[1] == "Antidepressants"]
        elif drug_group == "Anxiolytics":
            series = [s for s in all_series if s[1] == "Anxiolytics"]
        else:
            series = all_series

        fig_line = go.Figure()

        for i, (country, group, color, dash, label) in enumerate(series):
            vals = np.array([
                master[(master["country"]==country) & (master["group"]==group) & (master["year"]==y)]["items_per_1k"].sum()
                for y in YEARS
            ])
            growth_labels = [""]
            for j in range(1, len(vals)):
                if vals[j-1] != 0:
                    pct = (vals[j] - vals[j-1]) / vals[j-1] * 100
                    growth_labels.append(f"{'▲' if pct>=0 else '▼'}{abs(pct):.1f}%")
                else:
                    growth_labels.append("")

            show_text = drug_group != "Antidepressants + Anxiolytics"
            fig_line.add_trace(go.Scatter(
                x=YEARS, y=vals,
                mode="lines+markers+text" if show_text else "lines+markers",
                name=label,
                text=growth_labels if show_text else None,
                textposition="top center",
                textfont=dict(size=17, color=color, family="Trebuchet MS, sans-serif"),
                line=dict(color=color, dash=dash, width=2.2),
                marker=dict(size=7, color=color),
                customdata=growth_labels,
                hovertemplate=f"<b>{label}</b><br>%{{x}}: %{{y:.0f}} Prescriptions/1k<br>%{{customdata}}<extra></extra>",
            ))

        fig_line.update_layout(
            xaxis=dict(
                tickvals=YEARS, ticktext=[str(y) for y in YEARS],
                title=dict(text="Year", font=dict(size=14, color="#333")),
                tickfont=dict(color="#333", size=16),
                gridcolor="#E8E8E8",
            ),
            yaxis=dict(
                title=dict(text="Prescriptions per 1k pop. (annual)", font=dict(size=15, color="#333")),
                tickfont=dict(color="#333", size=16),
                gridcolor="#E8E8E8",
                range=[None, 1850],
            ),
            legend=dict(
                orientation="h", y=-0.18, x=0,
                font=dict(size=16, color="#555"), bgcolor="rgba(0,0,0,0)",
            ),
            paper_bgcolor="white",
            plot_bgcolor="white",
            margin=dict(t=40, b=50, l=10, r=60),
            height=500,
            hovermode="x unified",
        )
        st.plotly_chart(fig_line, use_container_width=True)




# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 2 — ENGLAND BY CITY
# ══════════════════════════════════════════════════════════════════════════════

def slide_england_cities():
    MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

    # ── City size tiers ───────────────────────────────────────────────────────
    TIER_LARGE  = 500_000
    TIER_MEDIUM = 200_000
    TIER_COLOR  = {"Large": "#C0392B", "Medium": "#D4880A", "Small": "#1A5EA8"}
    TIER_LABEL  = {"Large": "Large  >500k", "Medium": "Medium  200k–500k", "Small": "Small  <200k"}

    def get_tier(pop):
        if pop >= TIER_LARGE:
            return "Large"
        elif pop >= TIER_MEDIUM:
            return "Medium"
        else:
            return "Small"

    city_df = load_england_cities()

    st.markdown("<h2 style='text-align:center;color:#222;'>England — Antidepressant Prescribing by City</h2>",
                unsafe_allow_html=True)

    # ── SECTION 1: City Ranking Table ────────────────────────────────────────
    st.markdown("<hr style='margin:10px 0 6px;border-color:#DDD;'>", unsafe_allow_html=True)

    rank_year = st.select_slider("Year", options=YEARS, value=2023, key="rank_year")

    st.markdown("<p style='font-weight:700;color:#222;font-size:1.8rem;margin:10px 0 10px;'>City Rankings — Antidepressant Prescription Rate</p>", unsafe_allow_html=True)

    _df_r = city_df[(city_df["group"] == "antidepressant") & (city_df["year"] == rank_year)]
    df_rank = (
        _df_r.groupby("city")
        .agg(total_items=("items", "sum"), population=("population", "first"))
        .reset_index()
        .dropna(subset=["total_items"])
    )
    df_rank["norm_rate"] = df_rank["total_items"] / (df_rank["population"] / 1000)
    df_rank = df_rank.sort_values("norm_rate", ascending=False).reset_index(drop=True)

    if not df_rank.empty:
        df_rank["tier"] = df_rank["population"].apply(get_tier)
        df_rank["color"] = df_rank["tier"].map(TIER_COLOR)
        df_rank["pop_label"] = df_rank["population"].apply(
            lambda p: f"{p/1_000_000:.1f}M" if p >= 1_000_000 else f"{p/1_000:.0f}K"
        )

        # Build HTML table (no size tier column)
        rows_html = ""
        for i, row in df_rank.iterrows():
            rank_num = i + 1
            color = row["color"]
            bg = "#fff" if rank_num % 2 == 1 else "#F8F8F8"
            rows_html += (
                f"<tr style='background:{bg};'>"
                f"<td style='padding:9px 12px;font-weight:700;color:#555;text-align:center;'>{rank_num}</td>"
                f"<td style='padding:9px 12px;font-weight:600;color:{color};font-size:1.02rem;'>{row['city']}</td>"
                f"<td style='padding:9px 12px;text-align:right;font-weight:700;color:#222;font-size:1.05rem;'>{row['norm_rate']:.0f}</td>"
                f"<td style='padding:9px 12px;text-align:right;color:#555;'>{row['pop_label']}</td>"
                f"</tr>"
            )

        table_html = f"""
        <table style='width:100%;border-collapse:collapse;font-family:sans-serif;'>
          <thead>
            <tr style='background:#012169;color:#fff;'>
              <th style='padding:10px 12px;text-align:center;font-weight:600;font-size:0.9rem;'>#</th>
              <th style='padding:10px 12px;text-align:left;font-weight:600;font-size:0.9rem;'>City</th>
              <th style='padding:10px 12px;text-align:right;font-weight:600;font-size:0.9rem;'>Packs / 1k pop</th>
              <th style='padding:10px 12px;text-align:right;font-weight:600;font-size:0.9rem;'>Population</th>
            </tr>
          </thead>
          <tbody>{rows_html}</tbody>
        </table>
        """

        # ── Table left, map right ─────────────────────────────────────────────
        _df_m = city_df[(city_df["group"] == "antidepressant") & (city_df["year"] == rank_year)]
        df_map = (
            _df_m.groupby("city")
            .agg(total_items=("items", "sum"), population=("population", "first"))
            .reset_index()
            .dropna(subset=["total_items"])
        )
        df_map["norm_rate"] = df_map["total_items"] / (df_map["population"] / 1000)
        df_map["tier"] = df_map["population"].apply(get_tier)
        df_map["pop_label"] = df_map["population"].apply(
            lambda p: f"{p/1_000_000:.1f}M" if p >= 1_000_000 else f"{p/1_000:.0f}K"
        )
        coords_df = pd.DataFrame(
            [(c, lat, lon) for c, (lat, lon) in CITY_COORDS.items()],
            columns=["city", "lat", "lon"],
        )
        df_plot = df_map.merge(coords_df, on="city").dropna(subset=["norm_rate"])
        max_pop = df_plot["population"].max()
        df_plot["bubble_size"] = (df_plot["population"] / max_pop * 50 + 8).round(1)

        with st.spinner("Loading boundaries…"):
            _, england_rings, region_rings = load_city_boundaries()

        tbl_col, map_col = st.columns([2, 3], gap="large")
        with tbl_col:
            st.markdown(table_html, unsafe_allow_html=True)

        with map_col:
            fig_map = go.Figure()
            for lats, lons in england_rings:
                fig_map.add_trace(go.Scattergeo(lat=lats, lon=lons, mode="lines",
                    line=dict(color="#AAAAAA", width=1.5), hoverinfo="skip", showlegend=False))
            for lats, lons in region_rings:
                fig_map.add_trace(go.Scattergeo(lat=lats, lon=lons, mode="lines",
                    line=dict(color="#CCCCCC", width=0.5), hoverinfo="skip", showlegend=False))
            for tier in ["Large", "Medium", "Small"]:
                dt = df_plot[df_plot["tier"] == tier]
                if dt.empty:
                    continue
                fig_map.add_trace(go.Scattergeo(
                    lat=dt["lat"], lon=dt["lon"],
                    mode="markers+text",
                    name={"Large": "Large  >500k", "Medium": "Medium  200k–500k", "Small": "Small  <200k"}[tier],
                    text=dt["city"],
                    textposition="top center",
                    textfont=dict(size=14, color="#222"),
                    marker=dict(
                        size=dt["bubble_size"],
                        color=TIER_COLOR[tier],
                        opacity=0.82,
                        line=dict(color="white", width=1),
                        sizemode="diameter",
                    ),
                    customdata=np.stack([dt["norm_rate"], dt["population"]], axis=1),
                    hovertemplate="<b>%{text}</b><br>Packs/1k pop: %{customdata[0]:.0f}<br>Pop: %{customdata[1]:,.0f}<extra></extra>",
                ))
            _map_h = 750
            fig_map.update_layout(
                geo=dict(
                    scope="europe", resolution=50,
                    lonaxis=dict(range=[-5.8, 2.1]), lataxis=dict(range=[49.8, 55.9]),
                    showland=True, landcolor="#F2EFE9",
                    showocean=True, oceancolor="#A8D8EA",
                    showcountries=False, showcoastlines=False,
                    showlakes=True, lakecolor="#A8D8EA",
                    bgcolor="white",
                ),
                paper_bgcolor="white",
                margin=dict(t=10, b=10, l=5, r=5),
                height=_map_h,
                legend=dict(font=dict(size=20, color="#333"), bgcolor="rgba(255,255,255,0.85)", x=0.01, y=0.99),
            )
            st.plotly_chart(fig_map, use_container_width=True)

    # ── SECTION 4: Socioeconomic Correlation (antidepressants only) ───────────
    st.markdown("<hr style='margin:10px 0 6px;border-color:#DDD;'>", unsafe_allow_html=True)
    st.markdown("<p style='font-weight:700;color:#222;font-size:1.8rem;margin:10px 0 10px;'>Antidepressants vs Socioeconomic Factors</p>", unsafe_allow_html=True)

    sc_col1, sc_col2 = st.columns([2, 1])
    with sc_col1:
        sc_param = st.selectbox("Socioeconomic parameter", list(SOCIO_FILES.keys()), key="sc_param")
    with sc_col2:
        sc_year = st.select_slider("Year ", options=["All"] + YEARS, value="All", key="sc_year")

    df_socio = load_socio(sc_param)
    avail_sc_years = sorted(df_socio["year"].unique())

    if sc_year == "All":
        # One dot per city per year
        _df_sc_raw_all = city_df[city_df["group"] == "antidepressant"]
        df_rx_sc_all = (
            _df_sc_raw_all.groupby(["city", "year"])
            .agg(total_items=("items", "sum"), population=("population", "first"))
            .reset_index().dropna()
        )
        df_rx_sc_all["rx_rate"] = df_rx_sc_all["total_items"] / (df_rx_sc_all["population"] / 1000)
        df_rx_sc_all["tier"] = df_rx_sc_all["population"].apply(get_tier)
        df_sv_all = df_socio[["city", "year", "value"]].rename(columns={"value": "socio_val"})
        df_sc = df_rx_sc_all.merge(df_sv_all, on=["city", "year"]).dropna()
        df_sc["label"] = df_sc["city"] + " " + df_sc["year"].astype(str)
        sc_yr_use = "All"
    else:
        _df_sc_raw = city_df[(city_df["group"] == "antidepressant") & (city_df["year"] == sc_year)]
        df_rx_sc = (
            _df_sc_raw.groupby("city")
            .agg(total_items=("items", "sum"), population=("population", "first"))
            .reset_index().dropna()
        )
        df_rx_sc["rx_rate"] = df_rx_sc["total_items"] / (df_rx_sc["population"] / 1000)
        df_rx_sc["tier"] = df_rx_sc["population"].apply(get_tier)
        sc_yr_use = sc_year if sc_year in avail_sc_years else min(avail_sc_years, key=lambda y: abs(y - sc_year))
        df_sv = df_socio[df_socio["year"] == sc_yr_use][["city", "value"]].rename(columns={"value": "socio_val"})
        df_sc = df_rx_sc.merge(df_sv, on="city").dropna()
        df_sc["label"] = df_sc["city"]

    if len(df_sc) >= 4:
        r_sc, p_sc = pearson_r(df_sc["socio_val"], df_sc["rx_rate"])
        p_sc_str = "p < 0.0001" if p_sc < 0.0001 else f"p = {p_sc:.4f}"
        z_sc = np.polyfit(df_sc["socio_val"], df_sc["rx_rate"], 1)
        x_sc_line = np.linspace(df_sc["socio_val"].min(), df_sc["socio_val"].max(), 100)

        # Group by prescription rate tertiles
        terciles = df_sc["rx_rate"].quantile([1/3, 2/3])
        def rx_group(v):
            if v <= terciles[1/3]: return "Low prescribing"
            elif v <= terciles[2/3]: return "Mid prescribing"
            else: return "High prescribing"
        df_sc["rx_group"] = df_sc["rx_rate"].apply(rx_group)
        RX_GROUP_COLOR = {"High prescribing": "#C0392B", "Mid prescribing": "#E09C2A", "Low prescribing": "#2E86C1"}

        fig_sc = go.Figure()
        for grp in ["High prescribing", "Mid prescribing", "Low prescribing"]:
            dt = df_sc[df_sc["rx_group"] == grp]
            if dt.empty:
                continue
            fig_sc.add_trace(go.Scatter(
                x=dt["socio_val"], y=dt["rx_rate"],
                mode="markers+text" if sc_year != "All" else "markers",
                name=grp,
                text=dt["label"],
                textposition="top center",
                textfont=dict(size=12, color=RX_GROUP_COLOR[grp]),
                marker=dict(color=RX_GROUP_COLOR[grp], size=11, opacity=0.9),
                hovertemplate="<b>%{text}</b><br>" + sc_param + ": %{x:.2f}<br>Packs/1k pop: %{y:.0f}<extra></extra>",
            ))
        fig_sc.add_trace(go.Scatter(
            x=x_sc_line, y=np.poly1d(z_sc)(x_sc_line), mode="lines",
            line=dict(color="#444", width=2, dash="dash"),
            showlegend=False, hoverinfo="skip",
        ))
        year_note_sc = f" (socio: {sc_yr_use})" if sc_yr_use != sc_year else ""
        fig_sc.update_layout(
            title=dict(
                text=f"Antidepressants vs {sc_param}{year_note_sc}   r = {r_sc:.3f}   {p_sc_str}",
                font=dict(size=14, color="#012169"),
            ),
            xaxis=dict(title=dict(text=sc_param, font=dict(size=14, color="#333")),
                       tickfont=dict(size=13, color="#333"), gridcolor="#EEE"),
            yaxis=dict(title=dict(text="Packs / 1k pop (annual)", font=dict(size=14, color="#333")),
                       tickfont=dict(size=13, color="#333"), gridcolor="#EEE"),
            legend=dict(font=dict(size=13, color="#333")),
            paper_bgcolor="white", plot_bgcolor="white",
            margin=dict(t=50, b=40, l=10, r=10), height=420,
        )

        sc_left, sc_right = st.columns([3, 1])
        with sc_left:
            st.plotly_chart(fig_sc, use_container_width=True)
        with sc_right:
            # Note: Housing Affordability Ratio = house price / income, so higher = LESS affordable
            _is_affordability = "affordability" in sc_param.lower() or "housing" in sc_param.lower()
            if abs(r_sc) > 0.5 and p_sc < 0.05:
                direction = "positively" if r_sc > 0 else "negatively"
                if _is_affordability:
                    interp = f"<b>Strong {direction} correlated</b>"
                else:
                    interp = (f"<b>Strong {direction} correlated</b> — cities with higher {sc_param} tend to have "
                              f"{'more' if r_sc > 0 else 'fewer'} antidepressant prescriptions.")
                card_color = "#2E7D32"
                card_bg    = "#F1F8F1"
            elif p_sc < 0.05:
                direction = "positively" if r_sc > 0 else "negatively"
                interp = f"<b>Moderate {direction} correlation</b> — statistically significant but modest link."
                card_color = "#2E7D32"
                card_bg    = "#F1F8F1"
            else:
                interp = "<b>No significant correlation</b> detected (p ≥ 0.05)."
                card_color = "#888"
                card_bg    = "#F5F5F5"
            st.markdown(
                f"<div style='background:{card_bg};border-left:5px solid {card_color};"
                f"border-radius:8px;padding:16px 14px;margin-top:64px;'>"
                f"<p style='color:{card_color};font-size:1.0rem;margin:0;line-height:1.6;'>{interp}</p>"
                f"<p style='color:#888;font-size:0.85rem;margin:10px 0 0;'>"
                f"r = {r_sc:.3f} &nbsp; {p_sc_str} &nbsp; n = {len(df_sc)} cities</p>"
                f"</div>",
                unsafe_allow_html=True,
            )
    else:
        st.info(f"Not enough cities with data for {sc_param} in {sc_yr_use}.")

    # ── PROJECT CONCLUSIONS ───────────────────────────────────────────────────
    st.markdown("<hr style='margin:30px 0 10px;border-color:#DDD;'>", unsafe_allow_html=True)
    st.markdown("<p style='font-weight:700;color:#222;font-size:1.8rem;margin:10px 0 18px;'>Project Conclusions</p>", unsafe_allow_html=True)

    st.markdown("""
    <style>
    .concl-grid { display:flex; gap:16px; flex-wrap:wrap; margin-bottom:16px; }
    .concl-card {
        flex:1; min-width:260px;
        background:#fff;
        border-radius:10px;
        border-left:5px solid #012169;
        padding:18px 20px;
        box-shadow:0 2px 8px rgba(0,0,0,.07);
    }
    .concl-card.red  { border-left-color:#C0392B; }
    .concl-card.gold { border-left-color:#D4880A; }
    .concl-card.gray { border-left-color:#555; }
    .concl-label {
        font-size:0.72rem; font-weight:700; text-transform:uppercase;
        letter-spacing:0.08em; color:#888; margin-bottom:6px;
    }
    .concl-headline {
        font-size:1.05rem; font-weight:700; color:#222;
        margin-bottom:8px; line-height:1.4;
    }
    .concl-body {
        font-size:0.9rem; color:#444; line-height:1.6;
    }
    .concl-stat {
        display:inline-block; background:#F0F4FF;
        border-radius:4px; padding:2px 7px;
        font-size:0.85rem; font-weight:700; color:#012169; margin:0 2px;
    }
    .concl-stat.red { background:#FFF0EE; color:#C0392B; }
    .concl-stat.gold { background:#FFF8E8; color:#D4880A; }
    </style>

    <div class='concl-grid'>

      <div class='concl-card'>
        <div class='concl-label'>Prescription Volume</div>
        <div class='concl-headline'>England prescribes antidepressants at a significantly higher rate than Spain</div>
        <div class='concl-body'>
          Despite comparable universal healthcare systems, England's antidepressant rate is
          substantially higher across all years studied. This is not explained by economic disadvantage —
          Spain carries persistently higher unemployment yet prescribes less.
          The gap likely reflects differences in GP referral culture, mental health stigma, and
          system incentives rather than underlying disease burden.
        </div>
      </div>

      <div class='concl-card red'>
        <div class='concl-label'>Seasonality</div>
        <div class='concl-headline'>Winter peaks are real and statistically confirmed in both countries</div>
        <div class='concl-body'>
          STL decomposition confirms a significant seasonal component
          (<span class='concl-stat'>Kruskal-Wallis p &lt; 0.0001</span>) in antidepressant prescriptions
          for both England and Spain. Prescriptions peak in January–February and trough in June–July,
          mirroring the inverse of sunshine hours. At a
          <span class='concl-stat red'>2-month lag</span>, sunshine
          shows its strongest negative correlation with prescriptions — consistent with a delay
          between reduced light exposure and the point at which patients seek and receive treatment.
        </div>
      </div>

      <div class='concl-card gold'>
        <div class='concl-label'>City-Level Variation — England</div>
        <div class='concl-headline'>Northern, deprived cities consistently rank highest for antidepressant prescribing</div>
        <div class='concl-body'>
          There is a roughly <span class='concl-stat gold'>3× spread</span> in prescription rate across English cities.
          Northern cities (Nottingham, Manchester, Middlesbrough) dominate the top of the ranking,
          while London, Canterbury and Brighton sit at the bottom.
          City size alone does not explain this — deprivation and income matter more.
          Cities with lower Gross Disposable Income prescribe significantly more
          (<span class='concl-stat gold'>r = −0.64, p = 0.003</span>).
        </div>
      </div>

    </div>

    <div class='concl-grid'>

      <div class='concl-card gray'>
        <div class='concl-label'>Sunshine & Mental Health</div>
        <div class='concl-headline'>Sunlight is a consistent predictor, but not the only one</div>
        <div class='concl-body'>
          Across both countries and most cities, more sunshine correlates with fewer prescriptions.
          However, effect size varies widely by city, and in many cases the relationship is not
          statistically significant at city level — suggesting that sunlight is one factor in a
          larger picture that includes socioeconomic deprivation, GP access, and local demographics.
          Spain's climate advantage (~2,700 vs ~1,500 hrs/yr) may partially explain its lower prescribing,
          but the socioeconomic gap is the stronger explanatory variable.
        </div>
      </div>

      <div class='concl-card'>
        <div class='concl-label'>Anxiolytics vs Antidepressants</div>
        <div class='concl-headline'>Spain prescribes more anxiolytics; England prescribes more antidepressants</div>
        <div class='concl-body'>
          The two countries show a clear drug-class divergence. Spain's anxiolytic rate is proportionally
          higher relative to antidepressants, while England shows the opposite pattern.
          This may reflect different clinical guidelines, prescribing traditions, or how mental
          health conditions are classified and treated within each national system.
        </div>
      </div>

      <div class='concl-card red'>
        <div class='concl-label'>Key Limitation</div>
        <div class='concl-headline'>Prescriptions measure treatment, not illness</div>
        <div class='concl-body'>
          All findings are based on prescription volumes, not diagnosis rates or actual mental health
          outcomes. A city or country with more prescriptions may have better access to care,
          not necessarily higher illness rates. Caution is required when interpreting
          cross-country comparisons — structural differences in healthcare systems can produce
          divergent prescription patterns even with identical underlying populations.
        </div>
      </div>

    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE — COUNTRY COMPARISON
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data
def load_vitd():
    df = pd.read_csv("../Extacted data/Pharm stats /epd_colecalciferol_cities_clean_2021_2025.csv")
    df['date'] = pd.to_datetime(df['date'].astype(str), format='%Y%m')
    return df

@st.cache_data
def load_city_weather():
    df = pd.read_csv("../EDA/data/England_city_weather_population.csv")
    df['date'] = pd.to_datetime(df['date'], format='%Y-%m')
    df['tsun_hours'] = df['tsun'] / 60
    return df

@st.cache_data
def load_unemployment():
    df = pd.read_csv("../Extacted data/Other /Unemployment_Spain_UK.csv")
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)
    df["Unemployment Rate"] = df["Unemployment Rate"].str.rstrip("%").astype(float)
    df["Male unemployment"] = df["Male unemployment"].str.rstrip("%").astype(float)
    df["Female unemployment"] = df["Female unemployment"].str.rstrip("%").astype(float)
    df["Country"] = df["Country"].replace("England", "England (GB)")
    return df.sort_values("Date")

@st.cache_data
def load_health_exp():
    df = pd.read_csv("../Extacted data/Other /Government_Health_Expenditure_Spain_UK.csv")
    df["Gov. Health Exp. %GDP"] = df["Gov. Health Exp. %GDP"].str.rstrip("%").astype(float)
    df["Country"] = df["Country"].replace("United Kingdom", "England (GB)")
    return df.sort_values("Date")

def slide_country_comparison():
    st.markdown("<h2 style='text-align:center;color:#222;'>England vs Spain — Socioeconomic Context</h2>",
                unsafe_allow_html=True)

    df_unemp = load_unemployment()
    df_health = load_health_exp()

    COLOR_ENG = "#012169"
    COLOR_ESP = "#c0392b"

    col_l, col_r = st.columns(2, gap="large")

    # ── LEFT: Unemployment rate ───────────────────────────────────────────────
    with col_l:
        st.markdown("<p style='font-weight:700;color:#222;font-size:0.95rem;margin-bottom:4px;'>Unemployment Rate (%)</p>", unsafe_allow_html=True)

        fig_u = go.Figure()

        for country, color in [("England (GB)", COLOR_ENG), ("Spain", COLOR_ESP)]:
            df_c = df_unemp[df_unemp["Country"] == country].copy().reset_index(drop=True)
            label_mask = [i % 6 == 0 for i in range(len(df_c))]
            labels = [f"{v:.1f}%" if m else "" for v, m in zip(df_c["Unemployment Rate"], label_mask)]
            fig_u.add_trace(go.Scatter(
                x=df_c["Date"], y=df_c["Unemployment Rate"],
                mode="lines+text", name=country,
                line=dict(color=color, width=2.5),
                text=labels, textposition="top center",
                textfont=dict(size=15, color=color),
                hovertemplate=f"<b>{country}</b><br>%{{x|%b %Y}}: %{{y:.1f}}%<extra></extra>",
            ))
        fig_u.update_layout(
            xaxis=dict(title=dict(text="Month", font=dict(size=14, color="#333")),
                       tickfont=dict(size=15, color="#333"), gridcolor="#EEE"),
            yaxis=dict(title=dict(text="Unemployment (%)", font=dict(size=14, color="#333")),
                       tickfont=dict(size=15, color="#333"), gridcolor="#EEE"),
            legend=dict(font=dict(size=15, color="#333"), bgcolor="rgba(255,255,255,0.8)"),
            paper_bgcolor="white", plot_bgcolor="white",
            margin=dict(t=20, b=40, l=10, r=10), height=380,
        )
        st.plotly_chart(fig_u, use_container_width=True)

    # ── RIGHT: Healthcare % of GDP ────────────────────────────────────────────
    with col_r:
        st.markdown("<p style='font-weight:700;color:#222;font-size:0.95rem;margin-bottom:4px;'>Government Health Expenditure (% of GDP)</p>", unsafe_allow_html=True)


        fig_h = go.Figure()

        for country, color in [("England (GB)", COLOR_ENG), ("Spain", COLOR_ESP)]:
            df_c = df_health[df_health["Country"] == country].dropna(subset=["Gov. Health Exp. %GDP"])
            fig_h.add_trace(go.Scatter(
                x=df_c["Date"], y=df_c["Gov. Health Exp. %GDP"],
                mode="lines+markers+text", name=country,
                line=dict(color=color, width=2.5),
                marker=dict(size=7, color=color),
                text=[f"{v:.1f}%" for v in df_c["Gov. Health Exp. %GDP"]],
                textposition="top center",
                textfont=dict(size=15, color=color),
                hovertemplate=f"<b>{country}</b><br>%{{x}}: %{{y:.2f}}% GDP<extra></extra>",
            ))

        fig_h.update_layout(
            xaxis=dict(title=dict(text="Year", font=dict(size=14, color="#333")),
                       tickfont=dict(size=15, color="#333"), gridcolor="#EEE",
                       tickmode="array",
                       tickvals=df_health["Date"].unique(),
                       ticktext=[str(y) for y in sorted(df_health["Date"].unique())]),
            yaxis=dict(title=dict(text="% of GDP", font=dict(size=14, color="#333")),
                       tickfont=dict(size=15, color="#333"), gridcolor="#EEE"),
            legend=dict(font=dict(size=15, color="#333"), bgcolor="rgba(255,255,255,0.8)"),
            paper_bgcolor="white", plot_bgcolor="white",
            margin=dict(t=20, b=40, l=10, r=10), height=380,
        )
        st.plotly_chart(fig_h, use_container_width=True)

    # ── Correlation controls ───────────────────────────────────────────────────
    st.markdown("<hr style='margin:16px 0;border-color:#DDD;'>", unsafe_allow_html=True)
    cc_param = "Unemployment Rate"
    cc_drug = st.selectbox("Drug group", ["Anxiolytics", "Antidepressants"],
        key="cc_drug", label_visibility="visible")
    cc_lag = 0

    master = load_master()
    df_rx = master[master["group"].str.lower() == cc_drug.lower()][
        ["date", "country", "items_per_1k_per_day"]].copy()
    df_rx["date"] = pd.to_datetime(df_rx["date"])

    is_monthly = (cc_param == "Unemployment Rate")
    lag_unit = "month" if is_monthly else "year"

    st.markdown(
        f"<p style='font-weight:700;color:#222;font-size:0.95rem;margin-bottom:6px;'>"
        f"Correlation — {cc_param} vs {cc_drug} Prescriptions"
        f"</p>", unsafe_allow_html=True)

    if is_monthly:
        # Monthly unemployment — shift socio date forward by lag so it pairs with later rx
        df_u2 = load_unemployment().copy()
        df_u2["country"] = df_u2["Country"].replace({"England (GB)": "England"})
        df_u2 = df_u2[["Date", "country", "Unemployment Rate"]].rename(
            columns={"Date": "date", "Unemployment Rate": "socio_val"})
        if cc_lag > 0:
            df_u2["date"] = df_u2["date"] + pd.DateOffset(months=cc_lag)
        df_merged = df_rx.merge(df_u2, on=["date", "country"]).dropna()
        x_label = "Unemployment (%)"
        hover_x = "Unemployment: %{x:.1f}%"
    else:
        # Annual health expenditure — aggregate prescriptions by year
        df_rx["year"] = df_rx["date"].dt.year
        df_rx_yr = df_rx.groupby(["year", "country"])["items_per_1k_per_day"].mean().reset_index()
        df_h2 = load_health_exp().copy()
        df_h2["country"] = df_h2["Country"].replace({"England (GB)": "England"})
        df_h2 = df_h2[["Date", "country", "Gov. Health Exp. %GDP"]].rename(
            columns={"Date": "year", "Gov. Health Exp. %GDP": "socio_val"})
        if cc_lag > 0:
            df_h2["year"] = df_h2["year"] + cc_lag
        df_merged = df_rx_yr.merge(df_h2, on=["year", "country"]).dropna()
        x_label = "Gov. Health Exp. (% of GDP)"
        hover_x = "Health Exp: %{x:.2f}% GDP"

    corr_results_cc = {}
    if len(df_merged) >= 4:
        cc_l, cc_r = st.columns(2, gap="large")
        for (country, color), col in zip(
            [("England", COLOR_ENG), ("Spain", COLOR_ESP)], [cc_l, cc_r]
        ):
            dc = df_merged[df_merged["country"] == country].dropna()
            with col:
                if len(dc) < 3:
                    st.info(f"Not enough data for {country}.")
                    continue
                rv, pv = pearson_r(dc["socio_val"], dc["items_per_1k_per_day"])
                corr_results_cc[country] = (rv, pv)
                p_str = "p < 0.0001" if pv < 0.0001 else f"p = {pv:.4f}"
                sig = "✓ significant" if pv < 0.05 else "✗ not significant"
                z = np.polyfit(dc["socio_val"], dc["items_per_1k_per_day"], 1)
                x_line = np.linspace(dc["socio_val"].min(), dc["socio_val"].max(), 100)
                fig_c = go.Figure()
                fig_c.add_trace(go.Scatter(
                    x=dc["socio_val"], y=dc["items_per_1k_per_day"],
                    mode="markers", showlegend=False,
                    marker=dict(color=color, size=6, opacity=0.65),
                    hovertemplate=f"{hover_x}<br>Items/1k/day: %{{y:.3f}}<extra></extra>",
                ))
                fig_c.add_trace(go.Scatter(
                    x=x_line, y=np.poly1d(z)(x_line), mode="lines",
                    showlegend=False, line=dict(color=color, width=2, dash="dash"),
                    hoverinfo="skip",
                ))
                fig_c.update_layout(
                    title=dict(text=f"{country}   r = {rv:.3f}   {p_str}   {sig}",
                               font=dict(size=14, color=color)),
                    xaxis=dict(title=dict(text=x_label, font=dict(size=14, color="#333")),
                               tickfont=dict(size=15, color="#333"), gridcolor="#EEE"),
                    yaxis=dict(title=dict(text=f"{cc_drug} items/1k/day", font=dict(size=14, color="#333")),
                               tickfont=dict(size=15, color="#333"), gridcolor="#EEE"),
                    paper_bgcolor="white", plot_bgcolor="white",
                    margin=dict(t=45, b=40, l=10, r=10), height=340,
                )
                st.plotly_chart(fig_c, use_container_width=True)

        # ── Interpretation ────────────────────────────────────────────────────
        interp_html = "<div style='margin-top:8px;'>"
        for country, (rv, pv) in corr_results_cc.items():
            sig = pv < 0.05
            color = "#012169" if country == "England" else "#D95427"
            bg = "#eef3ff" if country == "England" else "#fff4f0"
            strength = "weak" if abs(rv) < 0.2 else ("moderate" if abs(rv) < 0.4 else "strong")
            direction = "positive" if rv > 0 else "negative"
            lag_txt = f" {cc_lag} {lag_unit}{'s' if cc_lag > 1 else ''} later" if cc_lag > 0 else ""
            p_str = "p < 0.0001" if pv < 0.0001 else f"p = {pv:.4f}"
            if sig:
                if cc_param == "Unemployment Rate":
                    if rv > 0:
                        body = (f"Higher unemployment is associated with <b>more</b> {cc_drug.lower()} prescriptions{lag_txt}. "
                                f"Economic hardship likely drives psychological distress, increasing demand for medication.")
                    else:
                        body = (f"Higher unemployment is associated with <b>fewer</b> {cc_drug.lower()} prescriptions{lag_txt}. "
                                f"This may reflect reduced healthcare access during economic downturns, or different coping patterns.")
                else:
                    if rv > 0:
                        body = (f"Higher health expenditure is associated with <b>more</b> {cc_drug.lower()} prescriptions{lag_txt}. "
                                f"Greater investment in healthcare may increase access to mental health services and prescription rates.")
                    else:
                        body = (f"Higher health expenditure is associated with <b>fewer</b> {cc_drug.lower()} prescriptions{lag_txt}. "
                                f"This could reflect that better-funded preventive care reduces the need for medication.")
                headline = f"{country} — {strength} {direction} link (r = {rv:.2f}, {p_str})"
            else:
                headline = f"{country} — No significant link (r = {rv:.2f}, {p_str})"
                body = (f"No statistically significant correlation between {cc_param.lower()} and "
                        f"{cc_drug.lower()} prescriptions at this lag. "
                        f"Try a different lag or drug group to explore the relationship further.")
            interp_html += (
                f"<div style='background:{bg};border-left:4px solid {color};border-radius:6px;"
                f"padding:10px 14px;margin:5px 0;'>"
                f"<div style='font-size:0.92rem;font-weight:700;color:{color};margin-bottom:3px;'>{headline}</div>"
                f"<div style='font-size:0.88rem;color:#444;line-height:1.5;'>{body}</div>"
                f"</div>")
        interp_html += "</div>"
        st.markdown(interp_html, unsafe_allow_html=True)
    else:
        st.info("Not enough overlapping data to compute correlation.")


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 3 — SEASONALITY
# ══════════════════════════════════════════════════════════════════════════════

def pearson_r(x, y):
    """Pearson r and two-tailed p-value using numpy + t-distribution approximation."""
    x, y = np.array(x), np.array(y)
    n = len(x)
    r = np.corrcoef(x, y)[0, 1]
    t_stat = r * np.sqrt(n - 2) / np.sqrt(1 - r**2 + 1e-15)
    # two-tailed p-value using normal approximation (good for n>30)
    from math import erfc, sqrt
    p = erfc(abs(t_stat) / sqrt(2))
    return r, p

def slide_seasonality():
    import calendar
    try:
        import holidays as hol_lib
        HAS_HOLIDAYS = True
    except ImportError:
        HAS_HOLIDAYS = False
    try:
        from statsmodels.tsa.seasonal import seasonal_decompose
        from scipy.stats import kruskal, mannwhitneyu
        HAS_STATSMODELS = True
    except ImportError:
        HAS_STATSMODELS = False

    master = load_master()
    master["days_in_month"] = master["date"].dt.days_in_month
    master["month"] = master["date"].dt.month
    master["tsun_hours"] = master["tsun_mean"] / 60

    # Working days adjustment
    if HAS_HOLIDAYS:
        def count_working_days(year, month, country):
            h = hol_lib.country_holidays('GB', subdiv='ENG', years=year) if country == 'England' \
                else hol_lib.country_holidays('ES', years=year)
            _, days = calendar.monthrange(year, month)
            return sum(1 for d in range(1, days+1)
                       if pd.Timestamp(year=year, month=month, day=d).weekday() < 5
                       and pd.Timestamp(year=year, month=month, day=d) not in h)
        master["working_days"] = master.apply(
            lambda r: count_working_days(r["date"].year, r["date"].month, r["country"]), axis=1)
        avg_wd = master["working_days"].mean().round(0)
        master["items_per_workday_1k"] = (
            master["items_per_1k"] / master["working_days"] * avg_wd).round(2)
    else:
        master["items_per_workday_1k"] = master["items_per_1k"] / master["days_in_month"]

    RX_COL = "items_per_workday_1k"
    colors = {"England": "#012169", "Spain": "#D95427"}

    st.markdown("""
        <div style='margin-bottom:8px;'></div>
    """, unsafe_allow_html=True)

    drug_group = st.selectbox("Drug group", ["Antidepressants", "Anxiolytics"],
                              key="seas_drug", label_visibility="visible")

    MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    country_list = ["England", "Spain"]  # always both for the time-series chart

    def _seas_decomp(df_c, color, RX_COL, MONTH_NAMES, HAS_STATSMODELS, kruskal, lag=0):
        """Returns (fig_seas, fig_sc) for one country dataframe."""
        # Seasonal bar
        if HAS_STATSMODELS and len(df_c) >= 24:
            decomp = seasonal_decompose(df_c.set_index("date")[RX_COL], model="additive", period=12)
            df_c = df_c.copy()
            df_c["seasonal"] = decomp.seasonal.values
            groups = [df_c[df_c["month"]==m]["seasonal"].dropna() for m in range(1,13)]
            groups = [g for g in groups if len(g) > 0]
            stat, p_kw = kruskal(*groups)
            p_label = "p < 0.0001" if p_kw < 0.0001 else f"p = {p_kw:.4f}"
            sig_label = "✅ Seasonal pattern confirmed" if p_kw < 0.05 else "❌ No significant seasonality"
            fig_seas = go.Figure()
            fig_seas.add_trace(go.Bar(
                x=MONTH_NAMES, y=df_c.groupby("month")["seasonal"].mean().values,
                marker_color=color, marker_opacity=0.75,
                hovertemplate="<b>%{x}</b>: %{y:.3f}<extra></extra>", showlegend=False))
            fig_seas.add_hline(y=0, line_color="#999", line_width=1)
        else:
            monthly_avg = df_c.groupby("month")[RX_COL].mean()
            overall_avg = df_c[RX_COL].mean()
            p_label, sig_label = "statsmodels not available", ""
            fig_seas = go.Figure()
            fig_seas.add_trace(go.Bar(
                x=MONTH_NAMES, y=(monthly_avg - overall_avg).values,
                marker_color=color, marker_opacity=0.75, showlegend=False))
            fig_seas.add_hline(y=0, line_color="#999", line_width=1)
        # Add average sunshine hours line on secondary y-axis
        sun_by_month = df_c.groupby("month")["tsun_mean"].mean() / 60  # minutes → hours
        fig_seas.add_trace(go.Scatter(
            x=MONTH_NAMES, y=sun_by_month.values,
            mode="lines+markers", name="Avg sun hrs",
            yaxis="y2",
            line=dict(color="#E03030", width=2, dash="dot"),
            marker=dict(size=6, color="#E03030"),
            hovertemplate="<b>%{x}</b>: %{y:.0f} sun hrs<extra></extra>",
            showlegend=True))
        fig_seas.update_layout(
            title=dict(text=f"Seasonal component   Kruskal-Wallis {p_label}   {sig_label}",
                       font=dict(size=14, color=color)),
            xaxis=dict(tickfont=dict(size=14, color="#333")),
            yaxis=dict(title=dict(text="Seasonal component", font=dict(size=15, color="#333")), tickfont=dict(size=15, color="#333"), gridcolor="#EEE"),
            yaxis2=dict(title=dict(text="Avg sun hrs", font=dict(size=14, color="#E03030")),
                        tickfont=dict(size=15, color="#E03030"),
                        overlaying="y", side="right", showgrid=False),
            legend=dict(orientation="h", y=-0.15, font=dict(size=14, color="#555")),
            paper_bgcolor="white", plot_bgcolor="white",
            margin=dict(t=45, b=40, l=10, r=10), height=320)
        # Detrended scatter
        df_sc = df_c.dropna(subset=["tsun_hours", RX_COL]).reset_index(drop=True)
        df_sc = df_sc.copy()
        # Apply lag: sunshine at t predicts prescriptions at t+lag
        if lag > 0:
            df_sc["rx_lagged"] = df_sc[RX_COL].shift(-lag)
            df_sc = df_sc.dropna(subset=["rx_lagged"]).reset_index(drop=True)
            rx_col_use = "rx_lagged"
        else:
            rx_col_use = RX_COL
        t = np.arange(len(df_sc))
        df_sc["rx_detrended"] = df_sc[rx_col_use] - np.poly1d(np.polyfit(t, df_sc[rx_col_use], 1))(t)
        r, p_r = pearson_r(df_sc["tsun_hours"], df_sc["rx_detrended"])
        p_label_r = "p < 0.0001" if p_r < 0.0001 else f"p = {p_r:.4f}"
        sig = "✓ significant" if p_r < 0.05 else "✗ not significant"
        z = np.polyfit(df_sc["tsun_hours"], df_sc["rx_detrended"], 1)
        x_range = np.linspace(df_sc["tsun_hours"].min(), df_sc["tsun_hours"].max(), 100)
        fig_sc = go.Figure()
        fig_sc.add_trace(go.Scatter(
            x=df_sc["tsun_hours"], y=df_sc["rx_detrended"], mode="markers",
            marker=dict(color=color, size=7, opacity=0.7),
            text=df_sc["date"].dt.strftime("%b %Y"),
            hovertemplate="<b>%{text}</b><br>Sun: %{x:.0f} hrs<br>Residual: %{y:.3f}<extra></extra>",
            showlegend=False))
        fig_sc.add_trace(go.Scatter(
            x=x_range, y=np.poly1d(z)(x_range), mode="lines",
            line=dict(color=color, width=2, dash="dash"),
            showlegend=False, hoverinfo="skip"))
        lag_label = f"   lag {lag}m" if lag > 0 else ""
        fig_sc.update_layout(
            title=dict(text=f"Sunshine vs Prescriptions (detrended{lag_label})   r = {r:.3f}   {p_label_r}   {sig}",
                       font=dict(size=14, color=color)),
            xaxis=dict(title=dict(text="Sunshine (hrs/month)", font=dict(size=15, color="#333")), tickfont=dict(size=15, color="#333"), gridcolor="#EEE"),
            yaxis=dict(title=dict(text="Residual", font=dict(size=15, color="#333")), tickfont=dict(size=15, color="#333"), gridcolor="#EEE"),
            paper_bgcolor="white", plot_bgcolor="white",
            margin=dict(t=40, b=40, l=10, r=10), height=320)
        return fig_seas, fig_sc, r, p_r

    # ── Chart 1: Time series with year bands ──────────────────────────────────
    year_band_colors = ["#E8EEF8", "#FFF3E8", "#E8F4EC", "#F0E8F8", "#FFF8E8"]
    fig_ts = go.Figure()
    for i, yr in enumerate(YEARS):
        x0 = f"{yr}-01-01"
        x1 = f"{yr}-12-31"
        fig_ts.add_vrect(x0=x0, x1=x1,
            fillcolor=year_band_colors[i % len(year_band_colors)], opacity=0.45, line_width=0,
            layer="below",
            annotation_text=str(yr),
            annotation_position="top left",
            annotation_font=dict(size=14, color="#999"))
    for c in country_list:
        df_c = master[(master["country"]==c) & (master["group"]==drug_group)].sort_values("date")
        fig_ts.add_trace(go.Scatter(
            x=df_c["date"], y=df_c[RX_COL], mode="lines", name=c,
            line=dict(color=colors[c], width=2.2),
            hovertemplate=f"<b>{c}</b><br>%{{x|%b %Y}}: %{{y:.2f}}<extra></extra>"))
        # Trendline
        t = np.arange(len(df_c))
        trend = np.poly1d(np.polyfit(t, df_c[RX_COL], 1))(t)
        fig_ts.add_trace(go.Scatter(
            x=df_c["date"], y=trend, mode="lines", name=f"{c} trend",
            line=dict(color=colors[c], width=1.5, dash="dash"),
            opacity=0.5, hoverinfo="skip", showlegend=False))
        # Peak & trough markers per year
        for yr in YEARS:
            df_yr = df_c[df_c["year"] == yr]
            if df_yr.empty:
                continue
            idx_max = df_yr[RX_COL].idxmax()
            idx_min = df_yr[RX_COL].idxmin()
            for idx, symbol, label in [(idx_max, "triangle-up", "▲"), (idx_min, "triangle-down", "▼")]:
                row = df_yr.loc[idx]
                fig_ts.add_trace(go.Scatter(
                    x=[row["date"]], y=[row[RX_COL]],
                    mode="markers+text",
                    marker=dict(symbol=symbol, size=10, color=colors[c]),
                    text=[f"{label}{row[RX_COL]:.0f} {row['date'].strftime('%b')}"],
                    textposition="top center" if label == "▲" else "bottom center",
                    textfont=dict(size=15, color=colors[c]),
                    hovertemplate=f"<b>{c} {'Peak' if label=='▲' else 'Trough'}</b><br>"
                                  f"%{{x|%b %Y}}: %{{y:.1f}}<extra></extra>",
                    showlegend=False,
                ))
    fig_ts.update_layout(
        title=dict(text=f"{drug_group} — Prescriptions per 1k (working-days adjusted)", font=dict(size=15, color="#333")),
        xaxis=dict(tickformat="%b %Y", tickangle=-45, tickfont=dict(size=14, color="#333"), gridcolor="#EEE"),
        yaxis=dict(title=dict(text="Items / 1k", font=dict(size=15, color="#333")), tickfont=dict(size=14, color="#333"), gridcolor="#EEE"),
        legend=dict(orientation="h", y=-0.25, font=dict(size=15, color="#555")),
        paper_bgcolor="white", plot_bgcolor="white",
        margin=dict(t=40, b=60, l=10, r=10), height=380, hovermode="x unified")
    st.plotly_chart(fig_ts, use_container_width=True)

    # ── Country selector (below time-series, above seasonal detail) ───────────
    sel_col, lag_col = st.columns([1, 1])
    with sel_col:
        country_sel = st.selectbox("Country", ["Both", "England", "Spain"],
                                   key="seas_country", label_visibility="visible")
    with lag_col:
        lag = st.select_slider("Prescription lag (months)", options=[0, 1, 2, 3],
                               value=0, key="seas_lag", label_visibility="visible")

    # ── Row 2: Seasonal bars + detrended scatter ──────────────────────────────
    corr_results = {}  # store {country: (r, p)} for explanation block

    if country_sel == "Both":
        # Side by side for both countries
        col_pairs = st.columns(2)
        for col, c in zip(col_pairs, ["England", "Spain"]):
            df_c = master[(master["country"]==c) & (master["group"]==drug_group)].sort_values("date").copy().reset_index(drop=True)
            df_c = df_c.dropna(subset=[RX_COL])
            fig_seas, _, r_c, p_c = _seas_decomp(df_c, colors[c], RX_COL, MONTH_NAMES, HAS_STATSMODELS, kruskal, lag)
            corr_results[c] = (r_c, p_c)
            fig_seas.update_layout(title_text=f"{c}   " + fig_seas.layout.title.text)
            with col:
                st.plotly_chart(fig_seas, use_container_width=True)
        col_pairs2 = st.columns(2)
        for col, c in zip(col_pairs2, ["England", "Spain"]):
            df_c = master[(master["country"]==c) & (master["group"]==drug_group)].sort_values("date").copy().reset_index(drop=True)
            df_c = df_c.dropna(subset=[RX_COL])
            _, fig_sc, r_c, p_c = _seas_decomp(df_c, colors[c], RX_COL, MONTH_NAMES, HAS_STATSMODELS, kruskal, lag)
            fig_sc.update_layout(title_text=f"{c}   " + fig_sc.layout.title.text)
            with col:
                st.plotly_chart(fig_sc, use_container_width=True)
    else:
        # Single country: seasonal bar left, scatter right
        c = country_sel
        df_c = master[(master["country"]==c) & (master["group"]==drug_group)].sort_values("date").copy().reset_index(drop=True)
        df_c = df_c.dropna(subset=[RX_COL])
        fig_seas, fig_sc, r_c, p_c = _seas_decomp(df_c, colors[c], RX_COL, MONTH_NAMES, HAS_STATSMODELS, kruskal, lag)
        corr_results[c] = (r_c, p_c)
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig_seas, use_container_width=True)
        with col2:
            st.plotly_chart(fig_sc, use_container_width=True)

    # ── Interpretation block ───────────────────────────────────────────────────
    def _interp(country, r, p, lag, drug_group):
        sig = p < 0.05
        direction = "negative" if r < 0 else "positive"
        strength = "weak" if abs(r) < 0.2 else ("moderate" if abs(r) < 0.4 else "strong")
        color = "#012169" if country == "England" else "#D95427"
        if lag == 0:
            lag_text = "in the same month"
        else:
            lag_text = f"{lag} month{'s' if lag > 1 else ''} after"
        if sig:
            headline = f"Sunshine predicts {drug_group.lower()} prescribing {lag_text} — {strength} {direction} link (r = {r:.2f}, p = {p:.4f})"
            if r < 0:
                body = (f"More sun is associated with <b>fewer</b> prescriptions {lag_text}. "
                        f"This fits the SAD hypothesis: sunshine improves mood, reducing the need for medication. "
                        f"A {lag}-month delay suggests patients experience low mood during dark months "
                        f"but only seek help — and get prescribed — weeks later." if lag > 0 else
                        f"More sun is associated with <b>fewer</b> prescriptions. "
                        f"This supports the idea that sunlight directly influences mood and reduces prescribing demand.")
            else:
                body = (f"Unexpectedly, more sun correlates with <b>more</b> prescriptions {lag_text}. "
                        f"This could reflect confounding: summer months may have higher GP attendance, "
                        f"or prescriptions may be initiated in spring before summer sun arrives.")
        else:
            headline = f"No significant link between sunshine and prescriptions at lag {lag}m (r = {r:.2f}, p = {p:.4f})"
            body = ("The scatter shows no clear pattern. Sunshine alone does not predict prescribing at this lag — "
                    "other factors (GP availability, seasonal mood cycles, holiday periods) likely dominate. "
                    "Try a different lag to see if the relationship emerges later.")
        border = color
        bg = "#eef3ff" if country == "England" else "#fff4f0"
        return f"""
<div style='background:{bg};border-left:4px solid {border};border-radius:6px;
            padding:12px 16px;margin:6px 0;'>
  <div style='font-size:0.95rem;font-weight:700;color:{color};margin-bottom:4px;'>{country} — {headline}</div>
  <div style='font-size:0.9rem;color:#444;line-height:1.5;'>{body}</div>
</div>"""

    interp_html = "<div style='margin-top:10px;'>"
    for country, (r, p) in corr_results.items():
        interp_html += _interp(country, r, p, lag, drug_group)
    interp_html += "</div>"
    st.markdown(interp_html, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE — CAUSAL IMPACT
# ══════════════════════════════════════════════════════════════════════════════

def slide_causal_impact():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    try:
        # pandas 2.x removed is_datetime_or_timedelta_dtype — patch before import
        import pandas.core.dtypes.common as _pdtypes
        if not hasattr(_pdtypes, "is_datetime_or_timedelta_dtype"):
            _pdtypes.is_datetime_or_timedelta_dtype = (
                lambda arr_or_dtype: pd.api.types.is_datetime64_any_dtype(arr_or_dtype)
                or pd.api.types.is_timedelta64_dtype(arr_or_dtype)
            )
        from causalimpact import CausalImpact
        HAS_CI = True
    except ImportError:
        HAS_CI = False

    st.markdown("<h2 style='text-align:center;color:#222;'>Causal Impact Analysis</h2>",
                unsafe_allow_html=True)
    st.markdown("""
    <p style='text-align:center;color:#555;font-size:0.95rem;max-width:700px;margin:0 auto 20px;'>
    Pick an intervention date and the model estimates what prescriptions <em>would have been</em>
    without it — using a Bayesian structural time-series fitted on the pre-period.
    The gap between actual and counterfactual is the causal effect.
    </p>""", unsafe_allow_html=True)

    master = load_master()
    master["date"] = pd.to_datetime(master["date"])

    # ── Controls ──────────────────────────────────────────────────────────────
    ctrl1, ctrl2, ctrl3 = st.columns(3)
    with ctrl1:
        ci_country = st.selectbox("Country", ["England", "Spain"], key="ci_country")
    with ctrl2:
        ci_drug = st.selectbox("Drug group", ["Antidepressants", "Anxiolytics"], key="ci_drug")
    with ctrl3:
        ci_covariate = st.selectbox("Control variable", ["Sunshine hours", "Other drug group"],
                                    key="ci_covariate")

    # Date slider — only mid-range dates
    all_dates = sorted(master["date"].unique())
    date_options = [d for d in all_dates if pd.Timestamp("2022-03-01") <= pd.Timestamp(d) <= pd.Timestamp("2024-09-01")]
    intervention_date = st.select_slider(
        "Intervention date",
        options=date_options,
        value=pd.Timestamp("2023-01-01") if pd.Timestamp("2023-01-01") in [pd.Timestamp(d) for d in date_options] else date_options[len(date_options)//2],
        format_func=lambda d: pd.Timestamp(d).strftime("%b %Y"),
        key="ci_intervention",
    )

    color = "#012169" if ci_country == "England" else "#D95427"

    # ── Build time series ─────────────────────────────────────────────────────
    df_main = (
        master[(master["country"] == ci_country) & (master["group"] == ci_drug)]
        .sort_values("date")
        .set_index("date")[["items_per_1k", "tsun_mean"]]
        .dropna(subset=["items_per_1k"])
    )
    df_main["tsun_hours"] = df_main["tsun_mean"] / 60

    # Build covariate column — keep DatetimeIndex throughout (package needs it)
    if ci_covariate == "Other drug group":
        other_drug = "Anxiolytics" if ci_drug == "Antidepressants" else "Antidepressants"
        df_other = (
            master[(master["country"] == ci_country) & (master["group"] == other_drug)]
            .sort_values("date").set_index("date")[["items_per_1k"]]
            .rename(columns={"items_per_1k": "x1"})
        )
        df_ci = df_main[["items_per_1k"]].rename(columns={"items_per_1k": "y"}).join(df_other)
    else:  # Sunshine hours
        df_ci = df_main[["items_per_1k", "tsun_hours"]].rename(
            columns={"items_per_1k": "y", "tsun_hours": "x1"}
        )

    df_ci = df_ci.dropna()

    # causalimpact internals do data[0] — must use plain integer RangeIndex
    interv_ts = pd.Timestamp(intervention_date)
    date_index = pd.DatetimeIndex(df_ci.index)
    interv_i = next((i for i, d in enumerate(date_index) if d >= interv_ts), None)
    df_ci = df_ci.reset_index(drop=True)
    # causalimpact misc.py does data_mu[0], data_mu[1]... — needs integer column labels
    df_ci.columns = range(len(df_ci.columns))

    if interv_i is None or interv_i < 6 or interv_i >= len(df_ci) - 3:
        st.warning("Choose an intervention date with at least 6 months before and 3 months after.")
        return

    pre_period  = [0, interv_i - 1]
    post_period = [interv_i, len(df_ci) - 1]

    # ── Run CausalImpact ──────────────────────────────────────────────────────
    if not HAS_CI:
        st.error("Install causalimpact: `pip install causalimpact`")
        return

    with st.spinner("Running Bayesian structural time-series model…"):
        try:
            ci_model = CausalImpact(df_ci, pre_period, post_period)
            ci_model.run()
        except Exception as e:
            import traceback
            st.error(f"Model error: {e}")
            st.code(traceback.format_exc())
            return

    # ── Plot ──────────────────────────────────────────────────────────────────
    plt.close("all")
    ci_model.plot(figsize=(12, 8))
    fig = plt.gcf()
    fig.patch.set_facecolor("white")
    for ax in fig.axes:
        ax.set_facecolor("white")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.tick_params(labelsize=12)
        for line in ax.get_lines():
            if line.get_color() in ["blue", "steelblue", "#1f77b4"]:
                line.set_color(color)
    st.pyplot(fig)
    plt.close("all")

    # ── Summary cards ─────────────────────────────────────────────────────────
    summary_text = ci_model.summary()
    report_text  = ci_model.summary(output="report")

    st.markdown("<hr style='margin:16px 0;border-color:#DDD;'>", unsafe_allow_html=True)
    s_col, r_col = st.columns([1, 1])
    with s_col:
        st.markdown("<p style='font-weight:700;color:#222;font-size:1.1rem;margin-bottom:6px;'>Summary</p>",
                    unsafe_allow_html=True)
        st.code(summary_text, language=None)
    with r_col:
        st.markdown("<p style='font-weight:700;color:#222;font-size:1.1rem;margin-bottom:6px;'>Report</p>",
                    unsafe_allow_html=True)
        st.markdown(
            f"<div style='background:#F7F8FC;border-radius:8px;padding:16px;font-size:0.88rem;"
            f"color:#333;line-height:1.7;white-space:pre-wrap;font-family:monospace;'>{report_text}</div>",
            unsafe_allow_html=True,
        )


# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
# MAIN — single scrollable page
# ══════════════════════════════════════════════════════════════════════════════

slide_title()

st.markdown("<div style='height:60px'></div>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["Prescription Rate", "Seasonality", "Economic Factors", "England by City"])
with tab1:
    slide_overview()
with tab2:
    slide_seasonality()
with tab3:
    slide_country_comparison()
with tab4:
    slide_england_cities()
