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
px_colors = px.colors.qualitative.Safe

st.set_page_config(
    page_title="Prescriptions England vs Spain",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  [data-testid="stAppViewContainer"] { background: #FAFAFA; }
  .kpi-box {
      background: white;
      border-radius: 10px;
      padding: 14px 16px 10px;
      box-shadow: 0 2px 6px rgba(0,0,0,0.08);
      text-align: center;
      position: relative;
      margin-bottom: 8px;
  }
  .kpi-label { font-size: 0.82rem; color: #999; text-transform: uppercase; letter-spacing: 0.05em; }
  .kpi-value { font-size: 2.2rem; font-weight: 700; line-height: 1.15; margin: 3px 0 1px; }
  .kpi-sub   { font-size: 0.88rem; color: #bbb; }
  .kpi-growth { font-size: 0.82rem; position: absolute; bottom: 7px; right: 9px; }
  .up   { color: #CC0000; }
  .down { color: #1a7a1a; }
  .eng  { color: #012169; }
  .esp  { color: #D95427; }
  .sec-title {
      font-size: 0.8rem; font-weight: 700; letter-spacing: 0.1em;
      text-transform: uppercase; color: #555; margin: 0 0 8px;
  }
  /* Tabs */
  [data-testid="stTabs"] button { font-size: 1rem; font-weight: 600; color: #333 !important; }
  [data-testid="stTabs"] button[aria-selected="true"] { color: #012169 !important; border-bottom: 3px solid #012169; }
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
  .stSlider label, .stRadio label { color: #222 !important; }
  /* Radio option text */
  [data-testid="stRadio"] div[role="radiogroup"] label span { color: #222 !important; }
  /* Select slider tick labels */
  [data-testid="stSlider"] [data-testid="stMarkdownContainer"] p { color: #222 !important; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# DATA
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data
def load_master():
    df = pd.read_csv("EDA/data/Master_table_Spain_England.csv")
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    return df

@st.cache_data
def load_england_cities():
    df = pd.read_csv("EDA/data/England_all_per_city.csv")
    df.columns = df.columns.str.strip()
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    return df

SOCIO_FILES = {
    "Median Age":                       ("EDA/data/socioeconomic/median_age.csv",                      "wide"),
    "Housing Affordability Ratio":      ("EDA/data/socioeconomic/housing_affordability_ratio.csv",     "wide"),
    "Gross Disposable Income (£/head)": ("EDA/data/socioeconomic/gross_disposable_household_income.csv","wide"),
    "Unemployment Rate (%)":            ("EDA/data/socioeconomic/unemployment_rate.csv",                "long"),
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
        <div style='display:flex;flex-direction:column;align-items:center;justify-content:center;
                    height:70vh;text-align:center;'>
            <h1 style='font-family:Trebuchet MS,sans-serif;font-size:2.4rem;font-weight:700;
                       color:#222;max-width:820px;line-height:1.25;margin-bottom:18px;'>
                Weather &amp; Socioeconomic Factors Associated with Antidepressant Prescribing
            </h1>
            <p style='font-size:1.15rem;color:#888;font-family:Trebuchet MS,sans-serif;'>
                England vs Spain &nbsp;·&nbsp; 2021–2025
            </p>
        </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 1 — OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════

def slide_overview():
    master = load_master()

    # ── Two-column layout ─────────────────────────────────────────────────────
    col_left, col_right = st.columns([0.74, 1], gap="large")

    # ════ LEFT: Year slider + Map ════════════════════════════════════════════
    with col_left:
        st.markdown("<p style='font-size:0.85rem;font-weight:700;color:#555;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:0px;'>Year</p>", unsafe_allow_html=True)
        year = st.select_slider(
            "Year",
            options=YEARS,
            value=2023,
            key="ov_year",
            label_visibility="collapsed",
        )

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

        # Fixed range across all years so colorbar is stable when sliding
        all_sun = [
            master[(master["country"]==c) & (master["group"]=="Antidepressants") & (master["year"]==y)]["tsun_mean"].sum() / 60
            for c in ["England", "Spain"] for y in YEARS
        ]
        zmin = min(all_sun) * 0.95
        zmax = max(all_sun) * 1.02
        sun_scale = [[0, "#3A6A9A"], [0.5, "#A0603A"], [1, "#E8703A"]]

        fig_map = go.Figure()
        # Spain
        fig_map.add_trace(go.Choropleth(
            locations=["ESP"], z=[sun_esp], locationmode="ISO-3",
            customdata=[[f"{pop_esp/1e6:.2f}M", gr_esp]],
            colorscale=sun_scale, zmin=zmin, zmax=zmax, showscale=False,
            marker=dict(line=dict(color="rgba(0,0,0,0)", width=0)),
            hovertemplate=(
                "<b>Spain</b><br>"
                "☀️ Sunshine: %{z:,} hrs/yr<br>"
                "%{customdata[1]}<extra></extra>"
            ),
        ))
        # England
        fig_map.add_trace(go.Choropleth(
            geojson=eng_geo, locations=["England"], z=[sun_eng],
            customdata=[[f"{pop_eng/1e6:.2f}M", gr_eng]],
            colorscale=sun_scale, zmin=zmin, zmax=zmax,
            colorbar=dict(
                title=dict(text="Sun hrs/yr", font=dict(size=13, color="#CCC")),
                tickfont=dict(color="#CCC", size=13),
                thickness=12, len=0.6, x=0.97,
            ),
            marker=dict(line=dict(color="rgba(0,0,0,0)", width=0)),
            hovertemplate=(
                "<b>England</b><br>"
                "☀️ Sunshine: %{z:,} hrs/yr<br>"
                "%{customdata[1]}<extra></extra>"
            ),
        ))
        # Country names — large
        fig_map.add_trace(go.Scattergeo(
            lat=[40.4, 52.5], lon=[-3.7, -1.8],
            text=["Spain", "England"], mode="markers+text",
            textposition="middle center",
            marker=dict(size=0, color="rgba(0,0,0,0)"),
            textfont=dict(size=18, color="white", family="Trebuchet MS, sans-serif"),
            hoverinfo="skip", showlegend=False,
        ))
        # Sun hours — smaller, below country name
        fig_map.add_trace(go.Scattergeo(
            lat=[38.8, 51.2], lon=[-3.7, -1.8],
            text=[f"~{sun_esp_day} hrs/day", f"~{sun_eng_day} hrs/day"],
            mode="markers+text",
            textposition="middle center",
            marker=dict(size=0, color="rgba(0,0,0,0)"),
            textfont=dict(size=11, color="rgba(255,255,255,0.75)", family="Trebuchet MS, sans-serif"),
            hoverinfo="skip", showlegend=False,
        ))
        fig_map.update_layout(
            geo=dict(
                scope="europe", resolution=50,
                projection=dict(type="mercator"),
                lonaxis=dict(range=[-13, 7]),
                lataxis=dict(range=[34, 60]),
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
        st.plotly_chart(fig_map, use_container_width=True)

    # ════ RIGHT: KPIs + Line chart ════════════════════════════════════════════
    with col_right:
        st.markdown("<p style='font-size:0.85rem;font-weight:700;color:#555;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:4px;'>Packs Issued</p>", unsafe_allow_html=True)
        metric = st.selectbox(
            "Packs Issued",
            ["Total", "Per 1,000 population"],
            key="ov_metric",
            label_visibility="collapsed",
        )

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
            return f"<span style='font-size:0.75rem;position:absolute;bottom:0;right:2px;color:{color};'>{arrow} {abs(pct):.1f}%</span>"

        def vs_badge(eng_val, esp_val):
            """Small bottom-right badge: how much more/less England is vs Spain."""
            if esp_val == 0:
                return ""
            pct = (eng_val - esp_val) / esp_val * 100
            arrow = "▲" if pct > 0 else "▼"
            return (
                f"<span style='position:absolute;bottom:4px;right:8px;"
                f"font-size:0.72rem;font-weight:700;color:#012169;"
                f"background:#f0f3ff;border-radius:4px;padding:1px 5px;'>"
                f"{arrow} {abs(pct):.1f}%</span>"
            )

        def country_card(flag, country_name, ad_val, p_ad, ax_val, p_ax, color,
                         ad_badge="", ax_badge=""):
            return (
                f"<div class='kpi-box' style='padding:2px 16px 4px;position:relative;'>"
                f"<div class='kpi-label' style='font-size:1.05rem;font-weight:700;color:#333;margin-bottom:2px;'>{flag} {country_name}</div>"
                f"<div style='margin-bottom:2px;position:relative;'>"
                f"{ad_badge}"
                f"<div class='kpi-label'>Antidepressants</div>"
                f"<div class='kpi-value {color}' style='font-size:2.0rem;'>{fmt(ad_val)}</div>"
                f"<div class='kpi-sub'>{sub_label}</div>"
                + f"</div>"
                + f"<hr style='border:none;border-top:1px solid #f0f0f0;margin:2px 0;'/>"
                + f"<div style='position:relative;'>"
                + f"{ax_badge}"
                + f"<div class='kpi-label' style='font-size:0.78rem;'>Anxiolytics</div>"
                + f"<div class='kpi-value {color}' style='font-size:1.1rem;font-weight:600;'>{fmt(ax_val)}</div>"
                + f"<div class='kpi-sub' style='font-size:0.78rem;'>{sub_label}</div>"
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

        text_positions = ["top center", "top center", "top center", "top center"]
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
                textposition=text_positions[i % len(text_positions)],
                textfont=dict(size=14, color=color, family="Trebuchet MS, sans-serif"),
                line=dict(color=color, dash=dash, width=2.2),
                marker=dict(size=7, color=color),
                customdata=growth_labels,
                hovertemplate=f"<b>{label}</b><br>%{{x}}: %{{y:.0f}} Prescriptions/1k<br>%{{customdata}}<extra></extra>",
            ))

        fig_line.update_layout(
            xaxis=dict(
                tickvals=YEARS, ticktext=[str(y) for y in YEARS],
                title=dict(text="Year", font=dict(size=11, color="#333")),
                tickfont=dict(color="#333", size=13),
                gridcolor="#E8E8E8",
            ),
            yaxis=dict(
                title=dict(text="Prescriptions per 1k pop. (annual)", font=dict(size=10, color="#333")),
                tickfont=dict(color="#333", size=13),
                gridcolor="#E8E8E8",
                range=[None, 1700],
            ),
            legend=dict(
                orientation="h", y=-0.28, x=0,
                font=dict(size=14, color="#555"), bgcolor="rgba(0,0,0,0)",
            ),
            paper_bgcolor="white",
            plot_bgcolor="white",
            margin=dict(t=24, b=50, l=10, r=10),
            height=300,
            hovermode="x unified",
        )
        st.plotly_chart(fig_line, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 2 — ENGLAND BY CITY
# ══════════════════════════════════════════════════════════════════════════════

def slide_england_cities():
    city_df = load_england_cities()

    st.markdown("<h2 style='text-align:center;color:#222;'>England — Prescription Rate by City</h2>",
                unsafe_allow_html=True)

    MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

    c1, c2 = st.columns([1, 1])
    with c1:
        year = st.select_slider("Year", options=YEARS, value=2023, key="city_year")
    with c2:
        group = st.radio("Drug group", ["antidepressant", "anxiolytic"], horizontal=True, key="city_group")

    # Filter to selected year (all months)
    df_filtered = city_df[
        (city_df["group"] == group) &
        (city_df["year"] == year)
    ]

    # Aggregate per city across full year
    df_agg = (
        df_filtered
        .groupby("city")
        .agg(
            total_items=("items", "sum"),
            norm_rate=("items_per_1k_per_day", "mean"),
            population=("population", "first"),
        )
        .reset_index()
    )

    # Keep only cities with known coords
    coords = pd.DataFrame(
        [(c, lat, lon) for c, (lat, lon) in CITY_COORDS.items()],
        columns=["city", "lat", "lon"]
    )
    df_plot = df_agg.merge(coords, on="city").dropna(subset=["total_items", "norm_rate"])

    # Bubble size: scale population to reasonable pixel range
    max_pop = df_plot["population"].max()
    df_plot["bubble_size"] = (df_plot["population"] / max_pop * 55 + 8).round(1)

    with st.spinner("Loading boundaries…"):
        _, england_rings, region_rings = load_city_boundaries()

    fig = go.Figure()

    # England outline
    for lats, lons in england_rings:
        fig.add_trace(go.Scattergeo(lat=lats, lon=lons, mode="lines",
            line=dict(color="#AAAAAA", width=1.5), hoverinfo="skip", showlegend=False))
    for lats, lons in region_rings:
        fig.add_trace(go.Scattergeo(lat=lats, lon=lons, mode="lines",
            line=dict(color="#CCCCCC", width=0.5), hoverinfo="skip", showlegend=False))

    # Bubbles
    fig.add_trace(go.Scattergeo(
        lat=df_plot["lat"],
        lon=df_plot["lon"],
        mode="markers+text",
        text=df_plot["city"],
        textposition="top center",
        textfont=dict(size=10, color="#222", family="Trebuchet MS, sans-serif"),
        marker=dict(
            size=df_plot["bubble_size"],
            color=df_plot["norm_rate"],
            colorscale=[[0, "#FFBBBB"], [0.5, "#E83A3A"], [1, "#6C0000"]],
            cmin=df_plot["norm_rate"].min(),
            cmax=df_plot["norm_rate"].max(),
            colorbar=dict(
                title=dict(text="Items/1k/day", font=dict(size=11, color="#333")),
                thickness=12, len=0.55,
                tickfont=dict(size=10, color="#333"),
            ),
            line=dict(color="white", width=0.8),
            opacity=0.85,
            sizemode="diameter",
        ),
        customdata=np.stack([df_plot["norm_rate"], df_plot["population"]], axis=1),
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Rate (items/1k/day): %{customdata[0]:.2f}<br>"
            "Population: %{customdata[1]:,.0f}"
            "<extra></extra>"
        ),
        showlegend=False,
    ))

    fig.update_layout(
        geo=dict(
            scope="europe", resolution=50,
            lonaxis=dict(range=[-6.5, 2.5]), lataxis=dict(range=[49.5, 56.5]),
            showland=True, landcolor="#F2EFE9",
            showocean=True, oceancolor="#A8D8EA",
            showcountries=False, showcoastlines=False,
            showlakes=True, lakecolor="#A8D8EA",
            bgcolor="white",
        ),
        paper_bgcolor="white",
        margin=dict(t=10, b=10, l=5, r=5),
        height=480,
    )

    map_col, corr_col = st.columns([1, 1], gap="large")

    with map_col:
        st.plotly_chart(fig, use_container_width=True)

    with corr_col:
        # ── Socioeconomic correlation ─────────────────────────────────────────
        st.markdown("<p style='font-weight:700;color:#222;font-size:0.95rem;margin:0 0 6px;'>Socioeconomic correlation</p>", unsafe_allow_html=True)

        corr_mode = st.radio(
            "View", ["Single parameter", "All parameters overview"],
            horizontal=True, key="corr_mode",
            label_visibility="collapsed",
        )

        # Annual avg prescription rate per city for selected year (shared by both modes)
        df_rx_yr = (
            city_df[(city_df["group"] == group) & (city_df["year"] == year)]
            .groupby("city")["items_per_1k_per_day"]
            .mean()
            .reset_index()
            .rename(columns={"items_per_1k_per_day": "rx_rate"})
        )

        if corr_mode == "Single parameter":
            socio_label = st.selectbox("Parameter", list(SOCIO_FILES.keys()), key="socio_param")
            all_years_toggle = st.checkbox("Show all years", key="corr_all_years")
            df_socio = load_socio(socio_label)
            avail_years = sorted(df_socio["year"].unique())

            YEAR_COLORS = {
                2021: "#1f77b4", 2022: "#ff7f0e", 2023: "#2ca02c",
                2024: "#9467bd", 2025: "#e377c2",
            }

            if all_years_toggle:
                # Build combined df across all available years
                all_rows = []
                rx_years_all = sorted(city_df[city_df["group"] == group]["year"].unique())
                for yr in rx_years_all:
                    if yr not in avail_years:
                        continue
                    df_rx_y = (
                        city_df[(city_df["group"] == group) & (city_df["year"] == yr)]
                        .groupby("city")["items_per_1k_per_day"].mean().reset_index()
                        .rename(columns={"items_per_1k_per_day": "rx_rate"})
                    )
                    df_sv_y = df_socio[df_socio["year"] == yr][["city", "value"]].rename(columns={"value": "socio_val"})
                    df_c = df_rx_y.merge(df_sv_y, on="city").dropna()
                    df_c["year"] = yr
                    all_rows.append(df_c)

                if not all_rows:
                    st.info("No overlapping years between prescription and socioeconomic data.")
                else:
                    df_all = pd.concat(all_rows, ignore_index=True)
                    fig_corr = go.Figure()

                    for yr in sorted(df_all["year"].unique()):
                        dc = df_all[df_all["year"] == yr]
                        col_yr = YEAR_COLORS.get(yr, "#888")
                        rv, pv = pearson_r(dc["socio_val"], dc["rx_rate"])
                        p_str = "p < 0.0001" if pv < 0.0001 else f"p = {pv:.4f}"
                        z = np.polyfit(dc["socio_val"], dc["rx_rate"], 1)
                        x_line = np.linspace(df_all["socio_val"].min(), df_all["socio_val"].max(), 100)

                        fig_corr.add_trace(go.Scatter(
                            x=dc["socio_val"], y=dc["rx_rate"],
                            mode="markers+text",
                            name=str(yr),
                            text=dc["city"],
                            textposition="top center",
                            textfont=dict(size=8, color=col_yr),
                            marker=dict(color=col_yr, size=8, opacity=0.8),
                            hovertemplate=f"<b>%{{text}}</b> ({yr})<br>{socio_label}: %{{x:.2f}}<br>Rx rate: %{{y:.3f}}<extra></extra>",
                        ))
                        fig_corr.add_trace(go.Scatter(
                            x=x_line, y=np.poly1d(z)(x_line), mode="lines",
                            showlegend=False,
                            line=dict(color=col_yr, width=1.5, dash="dash"),
                            hovertemplate=f"{yr}  r={rv:.3f}  {p_str}<extra></extra>",
                        ))

                    fig_corr.update_layout(
                        title=dict(
                            text=f"{group.capitalize()} vs {socio_label} — all years",
                            font=dict(size=11, color="#012169")
                        ),
                        xaxis=dict(title=dict(text=socio_label, font=dict(size=11, color="#333")),
                                   tickfont=dict(size=10, color="#333"), gridcolor="#EEE"),
                        yaxis=dict(title=dict(text="Avg items/1k/day", font=dict(size=11, color="#333")),
                                   tickfont=dict(size=10, color="#333"), gridcolor="#EEE"),
                        legend=dict(title=dict(text="Year"), font=dict(size=10, color="#333")),
                        paper_bgcolor="white", plot_bgcolor="white",
                        margin=dict(t=50, b=40, l=10, r=10), height=460,
                    )
                    st.plotly_chart(fig_corr, use_container_width=True)

            else:
                socio_year = year if year in avail_years else min(avail_years, key=lambda y: abs(y - year))
                df_sv = df_socio[df_socio["year"] == socio_year][["city", "value"]].rename(columns={"value": "socio_val"})
                df_corr = df_rx_yr.merge(df_sv, on="city").dropna()

                if len(df_corr) >= 4:
                    r, p = pearson_r(df_corr["socio_val"], df_corr["rx_rate"])
                    p_str = "p < 0.0001" if p < 0.0001 else f"p = {p:.4f}"
                    sig = "✓ significant" if p < 0.05 else "✗ not significant"
                    color = "#012169"
                    z = np.polyfit(df_corr["socio_val"], df_corr["rx_rate"], 1)
                    x_line = np.linspace(df_corr["socio_val"].min(), df_corr["socio_val"].max(), 100)

                    top5 = set(df_corr.nlargest(5, "rx_rate")["city"])
                    dot_colors = ["#c0392b" if c in top5 else color for c in df_corr["city"]]
                    text_colors = ["#c0392b" if c in top5 else "#333" for c in df_corr["city"]]

                    fig_corr = go.Figure()
                    fig_corr.add_trace(go.Scatter(
                        x=df_corr["socio_val"], y=df_corr["rx_rate"],
                        mode="markers+text",
                        text=df_corr["city"],
                        textposition="top center",
                        textfont=dict(size=9, color=text_colors),
                        marker=dict(color=dot_colors, size=9, opacity=0.9),
                        hovertemplate="<b>%{text}</b><br>" + socio_label + ": %{x:.2f}<br>Rx rate: %{y:.3f}<extra></extra>",
                        showlegend=False,
                    ))
                    fig_corr.add_trace(go.Scatter(
                        x=x_line, y=np.poly1d(z)(x_line), mode="lines",
                        line=dict(color=color, width=2, dash="dash"),
                        showlegend=False, hoverinfo="skip",
                    ))
                    year_note = f" (socio data: {socio_year})" if socio_year != year else ""
                    fig_corr.update_layout(
                        title=dict(
                            text=f"{group.capitalize()} vs {socio_label}{year_note}   r = {r:.3f}   {p_str}   {sig}",
                            font=dict(size=11, color=color)
                        ),
                        xaxis=dict(title=dict(text=socio_label, font=dict(size=11, color="#333")),
                                   tickfont=dict(size=10, color="#333"), gridcolor="#EEE"),
                        yaxis=dict(title=dict(text="Avg items/1k/day", font=dict(size=11, color="#333")),
                                   tickfont=dict(size=10, color="#333"), gridcolor="#EEE"),
                        paper_bgcolor="white", plot_bgcolor="white",
                        margin=dict(t=50, b=40, l=10, r=10), height=400,
                    )
                    st.plotly_chart(fig_corr, use_container_width=True)
                else:
                    st.info(f"Not enough cities with data for {socio_label} in {socio_year}.")

        else:
            # ── All parameters overview — all years heatmap ───────────────────
            rx_years = sorted(city_df[city_df["group"] == group]["year"].unique())

            heatmap_rows = []
            for rx_yr in rx_years:
                df_rx_y = (
                    city_df[(city_df["group"] == group) & (city_df["year"] == rx_yr)]
                    .groupby("city")["items_per_1k_per_day"]
                    .mean()
                    .reset_index()
                    .rename(columns={"items_per_1k_per_day": "rx_rate"})
                )
                for label in SOCIO_FILES.keys():
                    df_s = load_socio(label)
                    avail = sorted(df_s["year"].unique())
                    if rx_yr not in avail:
                        continue
                    df_sv2 = df_s[df_s["year"] == rx_yr][["city", "value"]].rename(columns={"value": "socio_val"})
                    df_c = df_rx_y.merge(df_sv2, on="city").dropna()
                    if len(df_c) >= 4:
                        rv, pv = pearson_r(df_c["socio_val"], df_c["rx_rate"])
                        heatmap_rows.append({
                            "label": label,
                            "rx_year": rx_yr,
                            "s_year": rx_yr,
                            "r": rv,
                            "p": pv,
                            "sig": pv < 0.05,
                            "n": len(df_c),
                        })

            if not heatmap_rows:
                st.info("No data available to compute correlations.")
            else:
                df_hm = pd.DataFrame(heatmap_rows)

                param_order = (
                    df_hm.groupby("label")["r"].mean()
                    .sort_values(ascending=False)
                    .index.tolist()
                )
                r_matrix = df_hm.pivot(index="label", columns="rx_year", values="r").reindex(param_order)
                p_matrix = df_hm.pivot(index="label", columns="rx_year", values="p").reindex(param_order)
                s_matrix = df_hm.pivot(index="label", columns="rx_year", values="s_year").reindex(param_order)
                n_matrix = df_hm.pivot(index="label", columns="rx_year", values="n").reindex(param_order)

                years_cols = r_matrix.columns.tolist()

                hover_matrix = []
                annot_matrix = []
                for param in param_order:
                    hover_row, annot_row = [], []
                    for yr in years_cols:
                        rv = r_matrix.loc[param, yr] if yr in r_matrix.columns and not pd.isna(r_matrix.loc[param, yr]) else None
                        pv = p_matrix.loc[param, yr] if yr in p_matrix.columns and not pd.isna(p_matrix.loc[param, yr]) else None
                        sy = s_matrix.loc[param, yr] if yr in s_matrix.columns and not pd.isna(s_matrix.loc[param, yr]) else None
                        nv = n_matrix.loc[param, yr] if yr in n_matrix.columns and not pd.isna(n_matrix.loc[param, yr]) else None
                        if rv is not None:
                            p_str = "p < 0.0001" if pv < 0.0001 else f"p = {pv:.4f}"
                            note = f" (socio: {int(sy)})" if sy != yr else ""
                            hover_row.append(f"r = {rv:.3f}<br>{p_str}<br>n = {int(nv)}{note}")
                            annot_row.append("*" if pv < 0.05 else "")
                        else:
                            hover_row.append("No data")
                            annot_row.append("n/a")
                    hover_matrix.append(hover_row)
                    annot_matrix.append(annot_row)

                MISSING = -2.0
                z_vals = [
                    [MISSING if (pd.isna(v) or v is None) else v for v in row]
                    for row in r_matrix.values.tolist()
                ]

                fig_hm = go.Figure(data=go.Heatmap(
                    z=z_vals,
                    x=[str(y) for y in years_cols],
                    y=param_order,
                    zmin=-2, zmax=1,
                    colorscale=[
                        [0.000, "#DDDDDD"],
                        [0.333, "#DDDDDD"],
                        [0.333, "#c0392b"],
                        [0.667, "#f5f5f5"],
                        [1.000, "#012169"],
                    ],
                    colorbar=dict(
                        title="r",
                        tickvals=[-1, -0.5, 0, 0.5, 1],
                        ticktext=["-1", "-0.5", "0", "0.5", "1"],
                        tickfont=dict(size=10, color="#333"),
                    ),
                    text=annot_matrix,
                    texttemplate="%{text}",
                    textfont=dict(size=14, color="#222"),
                    customdata=hover_matrix,
                    hovertemplate="<b>%{y}</b> · %{x}<br>%{customdata}<extra></extra>",
                ))
                fig_hm.update_layout(
                    title=dict(
                        text=f"Correlations by year — {group.capitalize()}<br>"
                             "<sup>* = significant (p < 0.05)  ·  blue = positive  ·  red = negative</sup>",
                        font=dict(size=11, color="#012169"),
                    ),
                    xaxis=dict(title=dict(text="Prescription year", font=dict(size=11, color="#333")),
                               tickfont=dict(size=11, color="#333")),
                    yaxis=dict(tickfont=dict(size=9, color="#333"), autorange="reversed"),
                    paper_bgcolor="white", plot_bgcolor="white",
                    margin=dict(t=70, b=50, l=10, r=10),
                    height=460,
                )
                st.plotly_chart(fig_hm, use_container_width=True)
                st.caption("* = p < 0.05  ·  Gray = no data for that year")

    # ── Vitamin D prescriptions vs Sunshine hours ─────────────────────────────
    st.markdown("<hr style='margin:20px 0 12px;border-color:#DDD;'>", unsafe_allow_html=True)
    st.markdown("<p style='font-weight:700;color:#222;font-size:0.95rem;margin-bottom:6px;'>Do sunnier cities prescribe less Vitamin D?</p>", unsafe_allow_html=True)

    df_vitd = load_vitd()
    df_wx   = load_city_weather()

    # Monthly totals per city
    df_vitd_agg = df_vitd.groupby(['date','city'])['items'].sum().reset_index()
    df_vitd_agg = df_vitd_agg.merge(
        df_wx[['date','city','tsun_hours','population']], on=['date','city']
    ).dropna(subset=['tsun_hours'])
    df_vitd_agg['items_per_1k'] = df_vitd_agg['items'] / (df_vitd_agg['population'] / 1000)

    # Average per city across all years
    df_city_avg = (
        df_vitd_agg.groupby('city')
        .agg(avg_sun=('tsun_hours','mean'), avg_vitd=('items_per_1k','mean'))
        .reset_index()
    )

    if len(df_city_avg) >= 4:
        r_city, p_city = pearson_r(df_city_avg['avg_sun'], df_city_avg['avg_vitd'])
        p_str_c = "p < 0.0001" if p_city < 0.0001 else f"p = {p_city:.4f}"
        sig_c = "✓ significant" if p_city < 0.05 else "✗ not significant"

        z = np.polyfit(df_city_avg['avg_sun'], df_city_avg['avg_vitd'], 1)
        x_line = np.linspace(df_city_avg['avg_sun'].min(), df_city_avg['avg_sun'].max(), 100)

        top5_vd = set(df_city_avg.nlargest(5, 'avg_vitd')['city'])
        dot_colors_vd = ['#c0392b' if c in top5_vd else '#012169' for c in df_city_avg['city']]
        text_colors_vd = ['#c0392b' if c in top5_vd else '#333' for c in df_city_avg['city']]

        fig_vd = go.Figure()
        fig_vd.add_trace(go.Scatter(
            x=df_city_avg['avg_sun'], y=df_city_avg['avg_vitd'],
            mode='markers+text',
            text=df_city_avg['city'],
            textposition='top center',
            textfont=dict(size=9, color=text_colors_vd),
            marker=dict(color=dot_colors_vd, size=10, opacity=0.9),
            hovertemplate='<b>%{text}</b><br>Avg sun: %{x:.0f} hrs/mo<br>VitD/1k: %{y:.1f}<extra></extra>',
            showlegend=False,
        ))
        fig_vd.add_trace(go.Scatter(
            x=x_line, y=np.poly1d(z)(x_line), mode='lines',
            line=dict(color='#012169', width=2, dash='dash'),
            showlegend=False, hoverinfo='skip',
        ))
        fig_vd.update_layout(
            title=dict(
                text=f"Avg sunshine vs Avg VitD prescriptions per city   r = {r_city:.3f}   {p_str_c}   {sig_c}",
                font=dict(size=11, color='#012169'),
            ),
            xaxis=dict(title=dict(text='Avg sunshine hours / month', font=dict(size=11, color='#333')),
                       tickfont=dict(size=10, color='#333'), gridcolor='#EEE'),
            yaxis=dict(title=dict(text='Avg VitD items / 1k pop.', font=dict(size=11, color='#333')),
                       tickfont=dict(size=10, color='#333'), gridcolor='#EEE'),
            paper_bgcolor='white', plot_bgcolor='white',
            margin=dict(t=50, b=40, l=10, r=10), height=400,
        )
        st.plotly_chart(fig_vd, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE — COUNTRY COMPARISON
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data
def load_vitd():
    df = pd.read_csv("Extacted data/Pharm stats /epd_colecalciferol_cities_clean_2021_2025.csv")
    df['date'] = pd.to_datetime(df['date'].astype(str), format='%Y%m')
    return df

@st.cache_data
def load_city_weather():
    df = pd.read_csv("EDA/data/England_city_weather_population.csv")
    df['date'] = pd.to_datetime(df['date'], format='%Y-%m')
    df['tsun_hours'] = df['tsun'] / 60
    return df

@st.cache_data
def load_unemployment():
    df = pd.read_csv("Extacted data/Other /Unemployment_Spain_UK.csv")
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)
    df["Unemployment Rate"] = df["Unemployment Rate"].str.rstrip("%").astype(float)
    df["Male unemployment"] = df["Male unemployment"].str.rstrip("%").astype(float)
    df["Female unemployment"] = df["Female unemployment"].str.rstrip("%").astype(float)
    df["Country"] = df["Country"].replace("England", "England (GB)")
    return df.sort_values("Date")

@st.cache_data
def load_health_exp():
    df = pd.read_csv("Extacted data/Other /Government_Health_Expenditure_Spain_UK.csv")
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

        breakdown = st.radio("Show", ["Total", "Male / Female"], horizontal=True, key="unemp_breakdown")

        fig_u = go.Figure()

        for country, color in [("England (GB)", COLOR_ENG), ("Spain", COLOR_ESP)]:
            df_c = df_unemp[df_unemp["Country"] == country]
            if breakdown == "Total":
                fig_u.add_trace(go.Scatter(
                    x=df_c["Date"], y=df_c["Unemployment Rate"],
                    mode="lines", name=country,
                    line=dict(color=color, width=2.5),
                    hovertemplate=f"<b>{country}</b><br>%{{x|%b %Y}}: %{{y:.1f}}%<extra></extra>",
                ))
            else:
                fig_u.add_trace(go.Scatter(
                    x=df_c["Date"], y=df_c["Male unemployment"],
                    mode="lines", name=f"{country} — Male",
                    line=dict(color=color, width=2, dash="solid"),
                    hovertemplate=f"<b>{country} Male</b><br>%{{x|%b %Y}}: %{{y:.1f}}%<extra></extra>",
                ))
                fig_u.add_trace(go.Scatter(
                    x=df_c["Date"], y=df_c["Female unemployment"],
                    mode="lines", name=f"{country} — Female",
                    line=dict(color=color, width=2, dash="dash"),
                    hovertemplate=f"<b>{country} Female</b><br>%{{x|%b %Y}}: %{{y:.1f}}%<extra></extra>",
                ))

        fig_u.update_layout(
            xaxis=dict(title=dict(text="Month", font=dict(size=11, color="#333")),
                       tickfont=dict(size=10, color="#333"), gridcolor="#EEE"),
            yaxis=dict(title=dict(text="Unemployment (%)", font=dict(size=11, color="#333")),
                       tickfont=dict(size=10, color="#333"), gridcolor="#EEE"),
            legend=dict(font=dict(size=10, color="#333"), bgcolor="rgba(255,255,255,0.8)"),
            paper_bgcolor="white", plot_bgcolor="white",
            margin=dict(t=20, b=40, l=10, r=10), height=380,
        )
        st.plotly_chart(fig_u, use_container_width=True)

    # ── RIGHT: Healthcare % of GDP ────────────────────────────────────────────
    with col_r:
        st.markdown("<p style='font-weight:700;color:#222;font-size:0.95rem;margin-bottom:4px;'>Government Health Expenditure (% of GDP)</p>", unsafe_allow_html=True)
        # padding to align with radio above
        st.markdown("<div style='height:38px'></div>", unsafe_allow_html=True)

        fig_h = go.Figure()

        for country, color in [("England (GB)", COLOR_ENG), ("Spain", COLOR_ESP)]:
            df_c = df_health[df_health["Country"] == country].dropna(subset=["Gov. Health Exp. %GDP"])
            fig_h.add_trace(go.Scatter(
                x=df_c["Date"], y=df_c["Gov. Health Exp. %GDP"],
                mode="lines+markers", name=country,
                line=dict(color=color, width=2.5),
                marker=dict(size=7, color=color),
                hovertemplate=f"<b>{country}</b><br>%{{x}}: %{{y:.2f}}% GDP<extra></extra>",
            ))

        fig_h.update_layout(
            xaxis=dict(title=dict(text="Year", font=dict(size=11, color="#333")),
                       tickfont=dict(size=10, color="#333"), gridcolor="#EEE",
                       tickmode="array",
                       tickvals=df_health["Date"].unique(),
                       ticktext=[str(y) for y in sorted(df_health["Date"].unique())]),
            yaxis=dict(title=dict(text="% of GDP", font=dict(size=11, color="#333")),
                       tickfont=dict(size=10, color="#333"), gridcolor="#EEE"),
            legend=dict(font=dict(size=10, color="#333"), bgcolor="rgba(255,255,255,0.8)"),
            paper_bgcolor="white", plot_bgcolor="white",
            margin=dict(t=20, b=40, l=10, r=10), height=380,
        )
        st.plotly_chart(fig_h, use_container_width=True)

    # ── Correlation: unemployment vs anxiolytic prescription rate ─────────────
    st.markdown("<hr style='margin:16px 0;border-color:#DDD;'>", unsafe_allow_html=True)
    st.markdown("<p style='font-weight:700;color:#222;font-size:0.95rem;margin-bottom:6px;'>Correlation — Unemployment Rate vs Anxiolytic Prescriptions</p>", unsafe_allow_html=True)

    master = load_master()
    df_anx = master[master["group"].str.lower() == "anxiolytics"][["date", "country", "items_per_1k_per_day"]].copy()
    df_anx["date"] = pd.to_datetime(df_anx["date"])

    # Monthly unemployment — map country names to match master table
    df_u2 = load_unemployment().copy()
    df_u2["country"] = df_u2["Country"].replace({"England (GB)": "England"})
    df_u2 = df_u2[["Date", "country", "Unemployment Rate"]].rename(columns={"Date": "date", "Unemployment Rate": "unemp"})

    df_merged = df_anx.merge(df_u2, on=["date", "country"]).dropna()

    if len(df_merged) >= 4:
        cc_l, cc_r = st.columns(2, gap="large")

        for (country, color), col in zip(
            [("England", COLOR_ENG), ("Spain", COLOR_ESP)],
            [cc_l, cc_r]
        ):
            dc = df_merged[df_merged["country"] == country]
            with col:
                if len(dc) < 3:
                    st.info(f"Not enough data for {country}.")
                    continue
                rv, pv = pearson_r(dc["unemp"], dc["items_per_1k_per_day"])
                p_str = "p < 0.0001" if pv < 0.0001 else f"p = {pv:.4f}"
                sig = "✓ significant" if pv < 0.05 else "✗ not significant"
                z = np.polyfit(dc["unemp"], dc["items_per_1k_per_day"], 1)
                x_line = np.linspace(dc["unemp"].min(), dc["unemp"].max(), 100)

                fig_c = go.Figure()
                fig_c.add_trace(go.Scatter(
                    x=dc["unemp"], y=dc["items_per_1k_per_day"],
                    mode="markers", showlegend=False,
                    marker=dict(color=color, size=6, opacity=0.65),
                    hovertemplate="Unemployment: %{x:.1f}%<br>Items/1k/day: %{y:.3f}<extra></extra>",
                ))
                fig_c.add_trace(go.Scatter(
                    x=x_line, y=np.poly1d(z)(x_line), mode="lines",
                    showlegend=False,
                    line=dict(color=color, width=2, dash="dash"),
                    hoverinfo="skip",
                ))
                fig_c.update_layout(
                    title=dict(
                        text=f"{country}   r = {rv:.3f}   {p_str}   {sig}",
                        font=dict(size=11, color=color),
                    ),
                    xaxis=dict(title=dict(text="Unemployment (%)", font=dict(size=11, color="#333")),
                               tickfont=dict(size=10, color="#333"), gridcolor="#EEE"),
                    yaxis=dict(title=dict(text="Anxiolytic items/1k/day", font=dict(size=11, color="#333")),
                               tickfont=dict(size=10, color="#333"), gridcolor="#EEE"),
                    paper_bgcolor="white", plot_bgcolor="white",
                    margin=dict(t=45, b=40, l=10, r=10), height=340,
                )
                st.plotly_chart(fig_c, use_container_width=True)
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
        <h2 style='text-align:center;color:#222;font-family:Trebuchet MS,sans-serif;
                   font-size:1.4rem;margin-bottom:16px;'>
            Seasonality in Prescriptions
            <span style='display:block;font-size:0.9rem;font-weight:400;color:#888;margin-top:3px;'>
                Working-days adjusted · Seasonal decomposition · Kruskal-Wallis test
            </span>
        </h2>
    """, unsafe_allow_html=True)

    ctrl1, ctrl2 = st.columns(2)
    with ctrl1:
        drug_group = st.selectbox("Drug group", ["Antidepressants", "Anxiolytics"],
                                  key="seas_drug", label_visibility="visible")
    with ctrl2:
        country_sel = st.selectbox("Country", ["Both", "England", "Spain"],
                                   key="seas_country", label_visibility="visible")

    MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    country_list = ["England", "Spain"] if country_sel == "Both" else [country_sel]

    def _seas_decomp(df_c, color, RX_COL, MONTH_NAMES, HAS_STATSMODELS, kruskal):
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
        fig_seas.update_layout(
            title=dict(text=f"Seasonal component   Kruskal-Wallis {p_label}   {sig_label}",
                       font=dict(size=11, color=color)),
            xaxis=dict(tickfont=dict(size=11, color="#333")),
            yaxis=dict(title=dict(text="Seasonal component", font=dict(size=12, color="#333")), tickfont=dict(size=10, color="#333"), gridcolor="#EEE"),
            paper_bgcolor="white", plot_bgcolor="white",
            margin=dict(t=45, b=30, l=10, r=10), height=320)
        # Detrended scatter
        df_sc = df_c.dropna(subset=["tsun_hours", RX_COL]).reset_index(drop=True)
        t = np.arange(len(df_sc))
        df_sc = df_sc.copy()
        df_sc["rx_detrended"] = df_sc[RX_COL] - np.poly1d(np.polyfit(t, df_sc[RX_COL], 1))(t)
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
        fig_sc.update_layout(
            title=dict(text=f"Sunshine vs Prescriptions (detrended)   r = {r:.3f}   {p_label_r}   {sig}",
                       font=dict(size=11, color=color)),
            xaxis=dict(title=dict(text="Sunshine (hrs/month)", font=dict(size=12, color="#333")), tickfont=dict(size=10, color="#333"), gridcolor="#EEE"),
            yaxis=dict(title=dict(text="Residual", font=dict(size=12, color="#333")), tickfont=dict(size=10, color="#333"), gridcolor="#EEE"),
            paper_bgcolor="white", plot_bgcolor="white",
            margin=dict(t=40, b=40, l=10, r=10), height=320)
        return fig_seas, fig_sc

    # ── Chart 1: Time series with summer shading ──────────────────────────────
    fig_ts = go.Figure()
    for yr in YEARS:
        fig_ts.add_vrect(x0=f"{yr}-06-01", x1=f"{yr}-08-31",
            fillcolor="gold", opacity=0.08, line_width=0,
            annotation_text="Summer" if yr == YEARS[0] else "",
            annotation_position="top left",
            annotation_font=dict(size=9, color="#999"))
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
    ts_title = f"{country_sel} — {drug_group} — Prescriptions per 1k (working-days adjusted)"
    fig_ts.update_layout(
        title=dict(text=ts_title, font=dict(size=13, color="#333")),
        xaxis=dict(tickformat="%b %Y", tickangle=-45, tickfont=dict(size=11, color="#333"), gridcolor="#EEE"),
        yaxis=dict(title=dict(text="Items / 1k", font=dict(size=12, color="#333")), tickfont=dict(size=11, color="#333"), gridcolor="#EEE"),
        legend=dict(orientation="h", y=-0.25, font=dict(size=12, color="#555")),
        paper_bgcolor="white", plot_bgcolor="white",
        margin=dict(t=40, b=60, l=10, r=10), height=300, hovermode="x unified")
    st.plotly_chart(fig_ts, use_container_width=True)

    # ── Row 2: Seasonal bars + detrended scatter ──────────────────────────────
    if country_sel == "Both":
        # Side by side for both countries
        col_pairs = st.columns(2)
        for col, c in zip(col_pairs, ["England", "Spain"]):
            df_c = master[(master["country"]==c) & (master["group"]==drug_group)].sort_values("date").copy().reset_index(drop=True)
            df_c = df_c.dropna(subset=[RX_COL])
            fig_seas, _ = _seas_decomp(df_c, colors[c], RX_COL, MONTH_NAMES, HAS_STATSMODELS, kruskal)
            fig_seas.update_layout(title_text=f"{c}   " + fig_seas.layout.title.text)
            with col:
                st.plotly_chart(fig_seas, use_container_width=True)
        col_pairs2 = st.columns(2)
        for col, c in zip(col_pairs2, ["England", "Spain"]):
            df_c = master[(master["country"]==c) & (master["group"]==drug_group)].sort_values("date").copy().reset_index(drop=True)
            df_c = df_c.dropna(subset=[RX_COL])
            _, fig_sc = _seas_decomp(df_c, colors[c], RX_COL, MONTH_NAMES, HAS_STATSMODELS, kruskal)
            fig_sc.update_layout(title_text=f"{c}   " + fig_sc.layout.title.text)
            with col:
                st.plotly_chart(fig_sc, use_container_width=True)
    else:
        # Single country: seasonal bar left, scatter right
        c = country_sel
        df_c = master[(master["country"]==c) & (master["group"]==drug_group)].sort_values("date").copy().reset_index(drop=True)
        df_c = df_c.dropna(subset=[RX_COL])
        fig_seas, fig_sc = _seas_decomp(df_c, colors[c], RX_COL, MONTH_NAMES, HAS_STATSMODELS, kruskal)
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig_seas, use_container_width=True)
        with col2:
            st.plotly_chart(fig_sc, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# NAVIGATION
# ══════════════════════════════════════════════════════════════════════════════

SLIDES = {
    "00 · Title": slide_title,
    "01 · Analysis": None,  # tabbed slide
}

with st.sidebar:
    st.markdown("### Navigation")
    page = st.radio("", list(SLIDES.keys()), label_visibility="collapsed")

if page == "00 · Title":
    slide_title()
else:
    tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Seasonality", "Country Comparison", "England by City"])
    with tab1:
        slide_overview()
    with tab2:
        slide_seasonality()
    with tab3:
        slide_country_comparison()
    with tab4:
        slide_england_cities()
