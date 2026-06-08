"""
Weather and Socioeconomic Factors Associated with Antidepressant Prescribing
England vs Spain (2021–2025)  ·  Streamlit Presentation
"""

import numpy as np
import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go

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
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# DATA
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data
def load_master():
    df = pd.read_csv("EDA/Master_table_Spain_England.csv")
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
        st.markdown("<p style='font-size:0.85rem;font-weight:700;color:#555;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:4px;'>Prescription in packs</p>", unsafe_allow_html=True)
        metric = st.selectbox(
            "Prescription in packs",
            ["Total Prescription", "Prescription per 1k population"],
            key="ov_metric",
            label_visibility="collapsed",
        )

        m_prev = master[master["year"] == year - 1] if year > 2021 else None

        def get(country, group):
            sub  = master[(master["country"]==country) & (master["group"]==group) & (master["year"]==year)]
            if metric == "Total Prescription":
                cur = sub["items"].sum()
            elif metric == "Prescription per 1k population":
                cur = sub["items_per_1k"].sum()
            else:  # per person
                cur = sub["items"].sum() / sub["population"].mean() if sub["population"].mean() > 0 else 0
            if m_prev is not None:
                sp = m_prev[(m_prev["country"]==country) & (m_prev["group"]==group)]
                if metric == "Total Prescription":
                    prev = sp["items"].sum()
                elif metric == "Prescription per 1k population":
                    prev = sp["items_per_1k"].sum()
                else:
                    prev = sp["items"].sum() / sp["population"].mean() if sp["population"].mean() > 0 else 0
            else:
                prev = None
            return cur, prev

        eng_ad, p_eng_ad = get("England", "Antidepressants")
        esp_ad, p_esp_ad = get("Spain",   "Antidepressants")
        eng_ax, p_eng_ax = get("England", "Anxiolytics")
        esp_ax, p_esp_ax = get("Spain",   "Anxiolytics")

        if metric == "Total Prescription":
            fmt = fmt_m
        elif metric == "Prescription per 1k population":
            fmt = lambda x: f"{x:.0f}"
        else:
            fmt = lambda x: f"{x:.2f}"
        sub_label = "pack"

        # Two columns: one per country, both drug groups stacked inside
        kc1, kc2 = st.columns(2)

        def small_badge(curr, prev):
            if prev is None or prev == 0:
                return ""
            pct = (curr - prev) / prev * 100
            color = "#CC0000" if pct > 0 else "#1a7a1a"
            arrow = "▲" if pct > 0 else "▼"
            return f"<span style='font-size:0.75rem;position:absolute;bottom:0;right:2px;color:{color};'>{arrow} {abs(pct):.1f}%</span>"

        def country_card(flag, country_name, ad_val, p_ad, ax_val, p_ax, color):
            return (
                f"<div class='kpi-box' style='padding:2px 16px 4px;'>"
                f"<div class='kpi-label' style='font-size:1.05rem;font-weight:700;color:#333;margin-bottom:2px;'>{flag} {country_name}</div>"
                f"<div style='margin-bottom:2px;position:relative;'>"
                f"<div class='kpi-label'>Antidepressants</div>"
                f"<div class='kpi-value {color}' style='font-size:2.0rem;'>{fmt(ad_val)}</div>"
                f"<div class='kpi-sub'>{sub_label}</div>"
                + growth_badge(ad_val, p_ad)
                + f"</div>"
                f"<hr style='border:none;border-top:1px solid #f0f0f0;margin:2px 0;'/>"
                f"<div style='position:relative;'>"
                f"<div class='kpi-label' style='font-size:0.78rem;'>Anxiolytics</div>"
                f"<div class='kpi-value {color}' style='font-size:1.1rem;font-weight:600;'>{fmt(ax_val)}</div>"
                f"<div class='kpi-sub' style='font-size:0.78rem;'>{sub_label}</div>"
                + small_badge(ax_val, p_ax)
                + f"</div>"
                f"</div>"
            )

        kc1, kc2 = st.columns(2)
        with kc1:
            st.markdown(country_card("🏴󠁧󠁢󠁥󠁮󠁧󠁿", "England", eng_ad, p_eng_ad, eng_ax, p_eng_ax, "eng"), unsafe_allow_html=True)
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

    c1, c2 = st.columns(2)
    with c1:
        year  = st.select_slider("Year", options=YEARS, value=2023, key="city_year")
    with c2:
        group = st.radio("Drug group", ["antidepressant", "anxiolytic"], horizontal=True, key="city_group")

    with st.spinner("Loading boundaries…"):
        geojson, england_rings, region_rings = load_city_boundaries()

    df_rx = (
        city_df[city_df["group"] == group]
        .groupby(["year", "city"])["items_per_1k_per_day"]
        .sum().reset_index()
    )
    rx_year = df_rx[df_rx["year"] == year].set_index("city")["items_per_1k_per_day"]
    cities  = [f["id"] for f in geojson["features"]]
    z_vals  = [round(rx_year.get(c, 0), 1) for c in cities]

    label_df = (
        pd.DataFrame([(c,) + CITY_COORDS[c] for c in cities if c in CITY_COORDS],
                     columns=["city", "lat", "lon"])
        .merge(pd.DataFrame({"city": cities, "rx": z_vals}), on="city")
    )

    fig = go.Figure()
    fig.add_trace(go.Choropleth(
        geojson=geojson, locations=cities, z=z_vals,
        colorscale=[[0, "#FFBBBB"], [0.5, "#E83A3A"], [1, "#6C0000"]],
        zmin=min(z_vals), zmax=max(z_vals),
        colorbar=dict(title=dict(text="Prescriptions/1k/day", font=dict(size=11)), thickness=12, len=0.55),
        marker=dict(line=dict(color="white", width=1.2)),
        hovertemplate="<b>%{location}</b><br>%{z:.1f} Prescriptions/1k/day<extra></extra>",
    ))
    for lats, lons in england_rings:
        fig.add_trace(go.Scattergeo(lat=lats, lon=lons, mode="lines",
            line=dict(color="#AFAFAF", width=1.5), hoverinfo="skip", showlegend=False))
    for lats, lons in region_rings:
        fig.add_trace(go.Scattergeo(lat=lats, lon=lons, mode="lines",
            line=dict(color="#CCCCCC", width=0.5), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scattergeo(
        lat=label_df["lat"], lon=label_df["lon"],
        text=label_df["city"], mode="markers+text", textposition="top center",
        marker=dict(size=4, color="#333"),
        textfont=dict(size=11, color="#333", family="Trebuchet MS, sans-serif"),
        hoverinfo="skip", showlegend=False,
    ))
    fig.update_layout(
        geo=dict(scope="europe", resolution=50,
                 lonaxis=dict(range=[-6.5, 2.5]), lataxis=dict(range=[49.5, 56.5]),
                 showland=True, landcolor="#F2EFE9", showocean=True, oceancolor="#A8D8EA",
                 showcountries=False, showcoastlines=False,
                 showlakes=True, lakecolor="#A8D8EA", bgcolor="white"),
        paper_bgcolor="white", margin=dict(t=10, b=10, l=5, r=5), height=600,
    )
    st.plotly_chart(fig, use_container_width=True)


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

    drug_group = st.selectbox("Drug group", ["Antidepressants", "Anxiolytics"],
                              key="seas_drug", label_visibility="visible")

    # ── Chart 1: Time series with summer shading ──────────────────────────────
    fig_ts = go.Figure()
    for yr in YEARS:
        fig_ts.add_vrect(x0=f"{yr}-06-01", x1=f"{yr}-08-31",
            fillcolor="gold", opacity=0.08, line_width=0,
            annotation_text="Summer" if yr == YEARS[0] else "",
            annotation_position="top left",
            annotation_font=dict(size=9, color="#999"))

    for country in ["England", "Spain"]:
        df_c = master[(master["country"]==country) & (master["group"]==drug_group)].sort_values("date")
        fig_ts.add_trace(go.Scatter(
            x=df_c["date"], y=df_c[RX_COL], mode="lines", name=country,
            line=dict(color=colors[country], width=2.2),
            hovertemplate=f"<b>{country}</b><br>%{{x|%b %Y}}: %{{y:.2f}}<extra></extra>"))

    fig_ts.update_layout(
        title=dict(text=f"{drug_group} — Prescriptions per 1k (working-days adjusted)", font=dict(size=13, color="#333")),
        xaxis=dict(tickformat="%b %Y", tickangle=-45, tickfont=dict(size=11, color="#333"), gridcolor="#EEE"),
        yaxis=dict(title="Rx / 1k", tickfont=dict(size=11, color="#333"), gridcolor="#EEE"),
        legend=dict(orientation="h", y=-0.25, font=dict(size=12, color="#555")),
        paper_bgcolor="white", plot_bgcolor="white",
        margin=dict(t=40, b=60, l=10, r=10), height=300, hovermode="x unified")
    st.plotly_chart(fig_ts, use_container_width=True)

    # ── Row 2: Seasonal component + monthly average ───────────────────────────
    col1, col2 = st.columns(2)
    MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

    for col, country, color in [(col1, "England", "#012169"), (col2, "Spain", "#D95427")]:
        df_c = master[(master["country"]==country) & (master["group"]==drug_group)].sort_values("date").copy().reset_index(drop=True)
        df_c = df_c.dropna(subset=[RX_COL])

        # Seasonal decomposition
        if HAS_STATSMODELS and len(df_c) >= 24:
            decomp = seasonal_decompose(df_c.set_index("date")[RX_COL], model="additive", period=12)
            seasonal = decomp.seasonal.values
            df_c["seasonal"] = seasonal
            # Kruskal-Wallis
            groups = [df_c[df_c["month"]==m]["seasonal"].dropna() for m in range(1,13)]
            groups = [g for g in groups if len(g) > 0]
            stat, p_kw = kruskal(*groups)
            p_label = f"p < 0.0001" if p_kw < 0.0001 else f"p = {p_kw:.4f}"
            sig_label = "✅ Seasonal pattern confirmed" if p_kw < 0.05 else "❌ No significant seasonality"

            # Plot seasonal component
            fig_seas = go.Figure()
            fig_seas.add_trace(go.Bar(
                x=MONTH_NAMES,
                y=df_c.groupby("month")["seasonal"].mean().values,
                marker_color=[color if v < 0 else color for v in df_c.groupby("month")["seasonal"].mean().values],
                marker_opacity=0.75,
                hovertemplate="<b>%{x}</b>: %{y:.3f}<extra></extra>",
                showlegend=False,
            ))
            fig_seas.add_hline(y=0, line_color="#999", line_width=1)
        else:
            # Fallback: simple monthly average deviation
            monthly_avg = df_c.groupby("month")[RX_COL].mean()
            overall_avg = df_c[RX_COL].mean()
            p_label, sig_label = "statsmodels not available", ""
            fig_seas = go.Figure()
            fig_seas.add_trace(go.Bar(
                x=MONTH_NAMES, y=(monthly_avg - overall_avg).values,
                marker_color=color, marker_opacity=0.75, showlegend=False))
            fig_seas.add_hline(y=0, line_color="#999", line_width=1)

        fig_seas.update_layout(
            title=dict(text=f"{country}   Kruskal-Wallis {p_label}   {sig_label}",
                       font=dict(size=11, color=color)),
            xaxis=dict(tickfont=dict(size=11, color="#333")),
            yaxis=dict(title="Seasonal component", tickfont=dict(size=10, color="#333"), gridcolor="#EEE"),
            paper_bgcolor="white", plot_bgcolor="white",
            margin=dict(t=45, b=30, l=10, r=10), height=280)
        with col:
            st.plotly_chart(fig_seas, use_container_width=True)

    # ── Row 3: Detrended sunshine correlation ─────────────────────────────────
    st.markdown("<p style='font-size:0.85rem;font-weight:700;color:#555;text-transform:uppercase;letter-spacing:0.07em;margin:8px 0 4px;'>Sunshine vs Prescriptions (detrended)</p>", unsafe_allow_html=True)
    col3, col4 = st.columns(2)
    for col, country, color in [(col3, "England", "#012169"), (col4, "Spain", "#D95427")]:
        df_c = master[(master["country"]==country) & (master["group"]==drug_group)].sort_values("date").copy()
        df_c = df_c.dropna(subset=["tsun_hours", RX_COL]).reset_index(drop=True)
        t = np.arange(len(df_c))
        df_c["rx_detrended"] = df_c[RX_COL] - np.poly1d(np.polyfit(t, df_c[RX_COL], 1))(t)
        r, p_r = pearson_r(df_c["tsun_hours"], df_c["rx_detrended"])
        p_label = "p < 0.0001" if p_r < 0.0001 else f"p = {p_r:.4f}"
        sig = "✓ significant" if p_r < 0.05 else "✗ not significant"
        z = np.polyfit(df_c["tsun_hours"], df_c["rx_detrended"], 1)
        x_range = np.linspace(df_c["tsun_hours"].min(), df_c["tsun_hours"].max(), 100)
        fig_sc = go.Figure()
        fig_sc.add_trace(go.Scatter(
            x=df_c["tsun_hours"], y=df_c["rx_detrended"], mode="markers",
            marker=dict(color=color, size=7, opacity=0.7),
            text=df_c["date"].dt.strftime("%b %Y"),
            hovertemplate="<b>%{text}</b><br>Sun: %{x:.0f} hrs<br>Residual: %{y:.3f}<extra></extra>",
            showlegend=False))
        fig_sc.add_trace(go.Scatter(
            x=x_range, y=np.poly1d(z)(x_range), mode="lines",
            line=dict(color=color, width=2, dash="dash"),
            showlegend=False, hoverinfo="skip"))
        fig_sc.update_layout(
            title=dict(text=f"{country}   r = {r:.3f}   {p_label}   {sig}", font=dict(size=11, color=color)),
            xaxis=dict(title="Sunshine (hrs/month)", tickfont=dict(size=10, color="#333"), gridcolor="#EEE"),
            yaxis=dict(title="Rx residual", tickfont=dict(size=10, color="#333"), gridcolor="#EEE"),
            paper_bgcolor="white", plot_bgcolor="white",
            margin=dict(t=40, b=40, l=10, r=10), height=280)
        with col:
            st.plotly_chart(fig_sc, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# NAVIGATION
# ══════════════════════════════════════════════════════════════════════════════

SLIDES = {
    "00 · Title": slide_title,
    "01 · Overview": slide_overview,
    "02 · England by City": slide_england_cities,
    "03 · Seasonality": slide_seasonality,
}

with st.sidebar:
    st.markdown("### Navigation")
    page = st.radio("", list(SLIDES.keys()), label_visibility="collapsed")

SLIDES[page]()
