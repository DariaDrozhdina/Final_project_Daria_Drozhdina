import pandas as pd
import plotly.graph_objects as go

# ── City coordinates (hardcoded — no geocoding needed to run) ─────────────────
data = [
    {"city": "Birmingham",          "lat": 52.4862, "lon": -1.8904},
    {"city": "Brighton",            "lat": 50.8225, "lon": -0.1372},
    {"city": "Bristol",             "lat": 51.4545, "lon": -2.5879},
    {"city": "Canterbury",          "lat": 51.2802, "lon":  1.0789},
    {"city": "Exeter",              "lat": 50.7184, "lon": -3.5339},
    {"city": "Leeds",               "lat": 53.8008, "lon": -1.5491},
    {"city": "London",              "lat": 51.5074, "lon": -0.1278},
    {"city": "Manchester",          "lat": 53.4808, "lon": -2.2426},
    {"city": "Middlesbrough",       "lat": 54.5742, "lon": -1.2350},
    {"city": "Newcastle upon Tyne", "lat": 54.9783, "lon": -1.6178},
    {"city": "Nottingham",          "lat": 52.9548, "lon": -1.1581},
    {"city": "Peterborough",        "lat": 52.5695, "lon": -0.2405},
    {"city": "Plymouth",            "lat": 50.3755, "lon": -4.1427},
    {"city": "Sunderland",          "lat": 54.9061, "lon": -1.3838},
    {"city": "York",                "lat": 53.9590, "lon": -1.0815},
]

df = pd.DataFrame(data)
print(df)

# ── Plot ──────────────────────────────────────────────────────────────────────
fig = go.Figure()

fig.add_trace(go.Scattergeo(
    lat=df["lat"],
    lon=df["lon"],
    text=df["city"],
    mode="markers+text",
    textposition="top center",
    marker=dict(
        size=14,
        color="#2670A6",
        symbol="circle",
        line=dict(color="white", width=1),
    ),
    hovertemplate="<b>%{text}</b><extra></extra>",
))

fig.update_layout(
    title=dict(text="England Cities — Prescription Study", x=0.5, font=dict(size=16)),
    geo=dict(
        scope="europe",
        resolution=50,
        lonaxis=dict(range=[-6.5, 2.5]),
        lataxis=dict(range=[49.5, 56.5]),
        showland=True,
        landcolor="#1e2130",
        showocean=True,
        oceancolor="#0f1117",
        showcountries=True,
        countrycolor="#444",
        showcoastlines=True,
        coastlinecolor="#555",
        showlakes=False,
        bgcolor="#0f1117",
    ),
    paper_bgcolor="#0f1117",
    font=dict(color="#e0e0e0"),
    margin=dict(t=50, b=10, l=10, r=10),
    height=650,
)

fig.show()