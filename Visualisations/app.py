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
    page_title="Rx England vs Spain",
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
  .kpi-label { font-size: 0.68rem; color: #999; text-transform: uppercase; letter-spacing: 0.05em; }
  .kpi-value { font-size: 1.9rem; font-weight: 700; line-height: 1.15; margin: 3px 0 1px; }
  .kpi-sub   { font-size: 0.72rem; color: #bbb; }
  .kpi-growth { font-size: 0.68rem; position: absolute; bottom: 7px; right: 9px; }
  .up   { color: #CC0000; }
  .down { color: #1a7a1a; }
  .eng  { color: #CC0000; }
  .esp  { color: #D4881A; }
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
# SLIDE 1 — OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════

def slide_overview():
    master = load_master()

    # ── Title ─────────────────────────────────────────────────────────────────
    st.markdown("""
        <h2 style='text-align:center;color:#222;font-family:Trebuchet MS,sans-serif;
                   font-size:1.55rem;margin-bottom:18px;'>
            Weather &amp; Socioeconomic Factors Associated with Antidepressant Prescribing
            <span style='display:block;font-size:0.95rem;font-weight:400;color:#888;margin-top:3px;'>
                England vs Spain · 2021–2025
            </span>
        </h2>
    """, unsafe_allow_html=True)

    # ── Two-column layout ─────────────────────────────────────────────────────
    col_left, col_right = st.columns([1.15, 1], gap="large")

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

        with st.spinner("Loading map…"):
            eng_geo = load_england_country_geojson()

        # Values for map colouring (per 1,000 population, annual)
        m_yr   = master[master["year"] == year]
        map_eng = m_yr[(m_yr["country"]=="England") & (m_yr["group"]=="Antidepressants")]["items_per_1k"].sum()
        map_esp = m_yr[(m_yr["country"]=="Spain")   & (m_yr["group"]=="Antidepressants")]["items_per_1k"].sum()
        zmin = min(map_eng, map_esp) * 0.85
        zmax = max(map_eng, map_esp) * 1.05
        red  = [[0, "#FFBBBB"], [0.4, "#E83A3A"], [1, "#6C0000"]]

        fig_map = go.Figure()
        # Spain
        fig_map.add_trace(go.Choropleth(
            locations=["ESP"], z=[round(map_esp, 1)], locationmode="ISO-3",
            colorscale=red, zmin=zmin, zmax=zmax, showscale=False,
            marker=dict(line=dict(color="#AAAAAA", width=0.8)),
            hovertemplate="<b>Spain</b><br>%{z:.0f} Rx/1k<extra></extra>",
        ))
        # England
        fig_map.add_trace(go.Choropleth(
            geojson=eng_geo, locations=["England"], z=[round(map_eng, 1)],
            colorscale=red, zmin=zmin, zmax=zmax,
            colorbar=dict(
                title=dict(text="Rx/1k pop.", font=dict(size=10, color="#555")),
                tickfont=dict(color="#555", size=10),
                thickness=12, len=0.5, x=1.0,
            ),
            marker=dict(line=dict(color="#888888", width=1.0)),
            hovertemplate="<b>England</b><br>%{z:.0f} Rx/1k<extra></extra>",
        ))
        # Labels — white so they're readable on both red-shaded countries
        fig_map.add_trace(go.Scattergeo(
            lat=[40.4, 52.8], lon=[-3.7, -1.8],
            text=["Spain", "England"], mode="markers+text",
            textposition="middle center",
            marker=dict(size=0, color="rgba(0,0,0,0)"),
            textfont=dict(size=14, color="white", family="Trebuchet MS, sans-serif"),
            hoverinfo="skip", showlegend=False,
        ))
        fig_map.update_layout(
            geo=dict(
                scope="europe", resolution=50,
                lonaxis=dict(range=[-11, 5]), lataxis=dict(range=[35, 61]),
                showland=True, landcolor="#F2EFE9",
                showocean=True, oceancolor="#A8D8EA",
                showcountries=True, countrycolor="#CCCCCC",
                showcoastlines=False, showlakes=True, lakecolor="#A8D8EA",
                bgcolor="white",
            ),
            paper_bgcolor="white",
            margin=dict(t=0, b=0, l=0, r=40),
            height=430,
        )
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
        use_total = metric == "Total Prescription"

        m_prev = master[master["year"] == year - 1] if year > 2021 else None

        def get(country, group):
            sub = master[(master["country"]==country) & (master["group"]==group) & (master["year"]==year)]
            cur = sub["items"].sum() if use_total else sub["items_per_1k"].sum()
            if m_prev is not None:
                sp = m_prev[(m_prev["country"]==country) & (m_prev["group"]==group)]
                prev = sp["items"].sum() if use_total else sp["items_per_1k"].sum()
            else:
                prev = None  # 2021 — no previous year
            return cur, prev

        eng_ad, p_eng_ad = get("England", "Antidepressants")
        esp_ad, p_esp_ad = get("Spain",   "Antidepressants")
        eng_ax, p_eng_ax = get("England", "Anxiolytics")
        esp_ax, p_esp_ax = get("Spain",   "Anxiolytics")

        fmt = fmt_m if use_total else (lambda x: f"{x:.0f}")
        sub_label = "packs" if use_total else "Rx per 1,000 pop."

        # Row 1: Antidepressants
        r1a, r1b = st.columns(2)
        with r1a:
            st.markdown(kpi("🇬🇧 Antidepressants", fmt(eng_ad), f"England · {sub_label}",
                            growth_badge(eng_ad, p_eng_ad), "eng"), unsafe_allow_html=True)
        with r1b:
            st.markdown(kpi("🇪🇸 Antidepressants", fmt(esp_ad), f"Spain · {sub_label}",
                            growth_badge(esp_ad, p_esp_ad), "esp"), unsafe_allow_html=True)

        # Row 2: Anxiolytics
        r2a, r2b = st.columns(2)
        with r2a:
            st.markdown(kpi("🇬🇧 Anxiolytics", fmt(eng_ax), f"England · {sub_label}",
                            growth_badge(eng_ax, p_eng_ax), "eng"), unsafe_allow_html=True)
        with r2b:
            st.markdown(kpi("🇪🇸 Anxiolytics", fmt(esp_ax), f"Spain · {sub_label}",
                            growth_badge(esp_ax, p_esp_ax), "esp"), unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        # ── Line chart ────────────────────────────────────────────────────────
        series = [
            ("England", "Antidepressants", "#CC0000",  "solid",  "🇬🇧 England — Antidepressants"),
            ("England", "Anxiolytics",     "#FF7777",  "dot",    "🇬🇧 England — Anxiolytics"),
            ("Spain",   "Antidepressants", "#D4881A",  "solid",  "🇪🇸 Spain — Antidepressants"),
            ("Spain",   "Anxiolytics",     "#F5C064",  "dot",    "🇪🇸 Spain — Anxiolytics"),
        ]

        fig_line = go.Figure()
        yrs = np.array(YEARS)

        for country, group, color, dash, label in series:
            vals = np.array([
                master[(master["country"]==country) & (master["group"]==group) & (master["year"]==y)]["items_per_1k"].sum()
                for y in YEARS
            ])
            # Actual line
            fig_line.add_trace(go.Scatter(
                x=YEARS, y=vals,
                mode="lines+markers",
                name=label,
                line=dict(color=color, dash=dash, width=2.2),
                marker=dict(size=7, color=color),
                hovertemplate=f"<b>{label}</b><br>%{{x}}: %{{y:.0f}} Rx/1k<extra></extra>",
            ))
            # Trend line (linear regression)
            m_coef, b_coef = np.polyfit(yrs, vals, 1)
            trend = m_coef * yrs + b_coef
            fig_line.add_trace(go.Scatter(
                x=YEARS, y=trend,
                mode="lines",
                name=f"{label} (trend)",
                line=dict(color=color, dash="longdash", width=1.2),
                opacity=0.55,
                showlegend=False,
                hoverinfo="skip",
            ))

        fig_line.add_vline(
            x=year, line=dict(color="#888", width=1, dash="dot"),
            annotation_text=str(year), annotation_position="top right",
            annotation_font=dict(size=10, color="#888"),
        )

        fig_line.update_layout(
            xaxis=dict(
                tickvals=YEARS, ticktext=[str(y) for y in YEARS],
                title=dict(text="Year", font=dict(size=11, color="#666")),
                gridcolor="#F0F0F0",
            ),
            yaxis=dict(
                title=dict(text="Rx per 1,000 population (annual)", font=dict(size=10, color="#666")),
                gridcolor="#F0F0F0",
            ),
            legend=dict(
                orientation="h", y=-0.28, x=0,
                font=dict(size=10), bgcolor="rgba(0,0,0,0)",
            ),
            paper_bgcolor="white",
            plot_bgcolor="white",
            margin=dict(t=10, b=60, l=10, r=10),
            height=310,
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
        colorbar=dict(title=dict(text="Rx/1k/day", font=dict(size=11)), thickness=12, len=0.55),
        marker=dict(line=dict(color="white", width=1.2)),
        hovertemplate="<b>%{location}</b><br>%{z:.1f} Rx/1k/day<extra></extra>",
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
# NAVIGATION
# ══════════════════════════════════════════════════════════════════════════════

SLIDES = {
    "01 · Overview": slide_overview,
    "02 · England by City": slide_england_cities,
}

with st.sidebar:
    st.markdown("### Navigation")
    page = st.radio("", list(SLIDES.keys()), label_visibility="collapsed")

SLIDES[page]()