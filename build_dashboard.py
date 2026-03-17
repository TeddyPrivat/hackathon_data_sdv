"""
build_dashboard.py
Génère dashboard.html — rapport climatique interactif, self-contained.
"""
import ast
import json
import requests
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from pathlib import Path
from sklearn.linear_model import LinearRegression

DATA = Path("data")
OUT  = Path("dashboard.html")

# ── Palette ───────────────────────────────────────────────────────────────────
C = dict(
    bg      = "#0a0d14",
    s1      = "rgba(255,255,255,0.03)",
    s2      = "rgba(255,255,255,0.06)",
    border  = "rgba(255,255,255,0.08)",
    text    = "#e2e8f0",
    muted   = "#475569",
    dim     = "#1e2d42",
    blue    = "#60a5fa",
    amber   = "#fbbf24",
    red     = "#f87171",
    green   = "#34d399",
    purple  = "#a78bfa",
    cyan    = "#22d3ee",
)
SCENE = {
    "Optimiste (+1.4°C)":     C["blue"],
    "Intermédiaire (+2.7°C)": C["amber"],
    "Pessimiste (+4.4°C)":    C["red"],
}
PLOT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor ="rgba(0,0,0,0)",
    font=dict(family="'Inter',system-ui,sans-serif", color=C["muted"], size=11),
    xaxis=dict(gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.07)",
               tickfont=dict(color=C["muted"])),
    yaxis=dict(gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.07)",
               tickfont=dict(color=C["muted"])),
    margin=dict(t=24, b=40, l=52, r=16),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=C["muted"])),
    hoverlabel=dict(bgcolor="#1e293b", font_color=C["text"], bordercolor=C["border"]),
)

def apply(fig, h=340, **kw):
    layout = {**PLOT, "height": h, **kw}
    fig.update_layout(**layout)
    return fig

def fig_json(fig):
    d = json.loads(fig.to_json())
    return json.dumps({"data": d["data"], "layout": d["layout"]})

print("Loading data...")

# ── Temperatures ──────────────────────────────────────────────────────────────
def load_sh(p):
    df = pd.read_csv(p, low_memory=False)
    df = df[df["Q_HOM"] == 1].copy()
    df["year"]  = df["YYYYMM"] // 100
    df["month"] = df["YYYYMM"] %  100
    return df

tx = load_sh(DATA / "temperatures/SH_TX_metropole_concat.csv")
tn = load_sh(DATA / "temperatures/SH_TN_metropole_concat.csv")
monthly = pd.concat([
    tx.groupby(["year","month"])["VALEUR"].mean().rename("tx"),
    tn.groupby(["year","month"])["VALEUR"].mean().rename("tn"),
], axis=1).dropna().reset_index()
monthly["tmoy"] = (monthly["tx"] + monthly["tn"]) / 2
annual = monthly.groupby("year")[["tx","tn","tmoy"]].mean().reset_index()
REF = annual[(annual.year>=1961) & (annual.year<=1990)]["tmoy"].mean()
annual["anomalie"] = annual["tmoy"] - REF

# ── CO2 ───────────────────────────────────────────────────────────────────────
co2_raw = pd.read_csv(DATA / "emissions_gaz/co2_mm_mlo.csv", comment="#")
co2_raw.columns = [c.strip() for c in co2_raw.columns]
co2 = co2_raw[co2_raw["average"]>0].groupby("year")["average"].mean().reset_index().rename(columns={"average":"co2_ppm"})

# ── Model ─────────────────────────────────────────────────────────────────────
df_model = annual.merge(co2, on="year").dropna()
df_model["log_co2"] = np.log(df_model["co2_ppm"] / 280)
model = LinearRegression()
model.fit(df_model[["log_co2"]].values, df_model["anomalie"].values)
coef = model.coef_[0] * np.log(2)

ANCHORS = {
    "Optimiste (+1.4°C)":     {2024:422,2030:430,2040:438,2050:428,2075:400,2100:390},
    "Intermédiaire (+2.7°C)": {2024:422,2030:435,2040:455,2050:480,2075:530,2100:550},
    "Pessimiste (+4.4°C)":    {2024:422,2030:445,2040:490,2050:550,2075:750,2100:1100},
}

def project(anchors, yr_end=2100):
    yrs  = np.arange(2024, yr_end+1)
    pts  = sorted(anchors.items())
    co2v = np.interp(yrs, [p[0] for p in pts], [p[1] for p in pts])
    anom = model.predict(np.log(co2v/280).reshape(-1,1)).flatten()
    return yrs, anom

projs = {n: project(a) for n, a in ANCHORS.items()}

# ── Fires ─────────────────────────────────────────────────────────────────────
fires = pd.read_csv(DATA / "feux/incendies_2003_2024.csv", low_memory=False)
fires["mois"] = pd.to_datetime(fires["date_alerte"], errors="coerce").dt.month

# ── Emissions ─────────────────────────────────────────────────────────────────
emi = pd.read_csv(DATA / "emissions_gaz/emissions_france_1995_2024.csv")
emp = pd.read_csv(DATA / "emissions_gaz/empreinte_carbone_france_par_habitant_1990_2024.csv")

# ── Precipitation ─────────────────────────────────────────────────────────────
prec_df = pd.read_csv(DATA / "precipitations/SH_RR_metropole_concat.csv", low_memory=False)
prec_df = prec_df[prec_df["Q_HOM"]==1]
prec_df["year"] = prec_df["YYYYMM"] // 100
prec_a = prec_df.groupby("year")["VALEUR"].mean().reset_index().rename(columns={"VALEUR":"precip"})
REF_P = prec_a[(prec_a.year>=1961)&(prec_a.year<=1990)]["precip"].mean()
prec_a["anom"] = prec_a["precip"] - REF_P

# ── Sécheresse VigiEau ────────────────────────────────────────────────────────
print("  Loading sécheresse...")
seche = pd.read_csv(DATA / "secheresse/vigieau_arretes_2024.csv", low_memory=False)
seche["date_debut"] = pd.to_datetime(seche["date_debut"], errors="coerce")
seche = seche.dropna(subset=["date_debut"])
seche_rows = []
for _, r in seche.iterrows():
    try:
        gravs = ast.literal_eval(r["zones_alerte.niveau_gravite"])
    except Exception:
        gravs = []
    for g in set(gravs):
        seche_rows.append({"date": r["date_debut"], "dept": str(r["departement"]).zfill(2), "gravite": g})
seche_exp = pd.DataFrame(seche_rows)
seche_exp["month"] = seche_exp["date"].dt.to_period("M").astype(str)
GRAV_ORDER = ["vigilance", "alerte", "alerte_renforcee", "crise"]
GRAV_COLORS = {"vigilance": C["green"], "alerte": C["amber"], "alerte_renforcee": "#f97316", "crise": C["red"]}
GRAV_LABELS = {"vigilance": "Vigilance", "alerte": "Alerte", "alerte_renforcee": "Alerte renforcée", "crise": "Crise"}
seche_pivot = seche_exp.groupby(["month","gravite"])["dept"].nunique().unstack(fill_value=0).reindex(columns=GRAV_ORDER, fill_value=0)
months_sorted = sorted(seche_pivot.index.tolist())
seche_pivot = seche_pivot.loc[months_sorted]

# ── Glaciers ──────────────────────────────────────────────────────────────────
print("  Loading glaciers...")
glac = pd.read_excel(DATA / "glaciers/glaciers_france.xlsx")
glac = glac[glac["Annual Balance"].notna()]
glac_ann = glac.groupby(["Glacier Name","Year"])["Annual Balance"].mean().reset_index()
# Cumulative balance per glacier
glaciers_list = glac_ann["Glacier Name"].unique().tolist()
glac_cum = {}
for g in glaciers_list:
    sub = glac_ann[glac_ann["Glacier Name"]==g].sort_values("Year")
    sub = sub.copy()
    sub["cumul"] = sub["Annual Balance"].cumsum()
    glac_cum[g] = sub

# ── Feux heatmap (mois × année) ───────────────────────────────────────────────
fires["annee"] = fires["annee"].astype(int)
fires_hm = fires.dropna(subset=["mois"]).copy()
fires_hm["mois"] = fires_hm["mois"].astype(int)
hm_pivot = fires_hm.groupby(["annee","mois"])["surface_totale_ha"].sum().unstack(fill_value=0)
years_hm  = hm_pivot.index.tolist()
months_hm = hm_pivot.columns.tolist()
z_hm      = hm_pivot.values.tolist()
MONTH_NAMES = ["","Jan","Fév","Mar","Avr","Mai","Jun","Jul","Aoû","Sep","Oct","Nov","Déc"]

# ── GeoJSON ───────────────────────────────────────────────────────────────────
dept_geojson = None
try:
    r = requests.get("https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements-version-simplifiee.geojson", timeout=8)
    dept_geojson = r.json()
    print("  GeoJSON loaded")
except Exception:
    print("  GeoJSON unavailable")

print("Building charts...")

# ── Key numbers ───────────────────────────────────────────────────────────────
anom_2023 = float(annual[annual.year==2023]["anomalie"].values[0])
co2_last  = float(co2["co2_ppm"].iloc[-2])
fires_tot = int(fires["surface_totale_ha"].sum())
emp_last  = float(emp["empreinte_carbone_tCO2e_par_habitant"].iloc[-1])

proj_vals = {}
for name in SCENE:
    yrs, anom = projs[name]
    proj_vals[name] = {yr: round(float(anom[list(yrs).index(yr)]), 2) for yr in [2030, 2050, 2100]}

# Chatbot context summary for system prompt
glac_last_bal = {g: round(float(glac_cum[g]["Annual Balance"].iloc[-1]),3) for g in glaciers_list}
chatbot_context = f"""Tu es un assistant climatique expert qui répond aux questions sur ce tableau de bord.

Données disponibles :
- Anomalie température France 2023 : {anom_2023:+.2f}°C vs référence 1961-1990
- CO₂ atmosphérique actuel : {co2_last:.0f} ppm (préindustriel : 280 ppm)
- Surface brûlée incendies 2003-2024 : {fires_tot:,} ha au total
- Empreinte carbone 2024 : {emp_last} tCO₂e/habitant (objectif 2050 : 2 t)
- Modèle log-linéaire : anomalie = f(log CO₂/280), sensibilité = {coef:.2f}°C/doublement CO₂

Projections 2100 par scénario IPCC AR6 :
- Optimiste (SSP1-1.9) : {proj_vals["Optimiste (+1.4°C)"][2100]:+.1f}°C
- Intermédiaire (SSP2-4.5) : {proj_vals["Intermédiaire (+2.7°C)"][2100]:+.1f}°C
- Pessimiste (SSP5-8.5) : {proj_vals["Pessimiste (+4.4°C)"][2100]:+.1f}°C

Glaciers France : {len(glaciers_list)} glaciers suivis — bilan de masse annuel moyen tous glaciers : {sum(glac_last_bal.values())/len(glac_last_bal):.3f} m éq. eau/an

Réponds de manière concise, factuelle, en français. Si tu n'as pas l'information, dis-le clairement."""

# ═══════════════════════════════════════════════════════════════════════════════
# CHART 1 — Anomalie historique
# ═══════════════════════════════════════════════════════════════════════════════
fig_hist = go.Figure()
fig_hist.add_bar(
    x=annual["year"].tolist(), y=annual["anomalie"].round(3).tolist(),
    marker_color=[C["red"] if v>0 else C["blue"] for v in annual["anomalie"]],
    marker_opacity=0.55, name="Anomalie annuelle", hovertemplate="%{x} : %{y:+.2f}°C<extra></extra>",
)
roll = annual["anomalie"].rolling(10, center=True).mean()
fig_hist.add_scatter(
    x=annual["year"].tolist(), y=roll.round(3).tolist(), mode="lines",
    line=dict(color=C["text"], width=2.5), name="Moyenne 10 ans",
    hovertemplate="%{x} : %{y:+.2f}°C<extra></extra>",
)
fig_hist.add_hline(y=0, line_color=C["dim"], line_width=1)
apply(fig_hist, h=320,
      xaxis_title="", yaxis_title="Anomalie (°C)",
      legend=dict(orientation="h", y=1.1, bgcolor="rgba(0,0,0,0)"))
J_HIST = fig_json(fig_hist)

# ═══════════════════════════════════════════════════════════════════════════════
# CHART 2 — Projections 3 scénarios
# ═══════════════════════════════════════════════════════════════════════════════
fig_proj = go.Figure()
hist_roll = annual["anomalie"].rolling(5, center=True).mean()
fig_proj.add_scatter(
    x=annual["year"].tolist(), y=hist_roll.round(3).tolist(), mode="lines",
    line=dict(color="rgba(255,255,255,0.25)", width=1.5), name="Historique",
    hovertemplate="%{x} : %{y:+.2f}°C<extra></extra>",
)
for name, color in SCENE.items():
    yrs, anom = projs[name]
    fig_proj.add_scatter(
        x=yrs.tolist(), y=anom.round(3).tolist(), mode="lines",
        line=dict(color=color, width=2.5), name=name,
        hovertemplate=f"<b>{name}</b><br>%{{x}} : %{{y:+.2f}}°C<extra></extra>",
    )
    for yr in [2030, 2050, 2100]:
        idx = list(yrs).index(yr)
        fig_proj.add_scatter(
            x=[yr], y=[round(anom[idx],2)], mode="markers+text",
            marker=dict(size=8, color=color, symbol="circle"),
            text=[f"{anom[idx]:+.1f}°C"], textposition="top center",
            textfont=dict(size=10, color=color), showlegend=False,
            hovertemplate=f"{yr} : {anom[idx]:+.2f}°C<extra></extra>",
        )
fig_proj.add_vline(x=2024, line_dash="dot", line_color=C["dim"], line_width=1.5)
fig_proj.add_hline(y=0, line_color=C["dim"], line_width=0.8)
apply(fig_proj, h=380,
      xaxis_title="", yaxis_title="Anomalie (°C vs 1961–1990)",
      legend=dict(orientation="h", y=1.1))
J_PROJ = fig_json(fig_proj)

# ═══════════════════════════════════════════════════════════════════════════════
# CHART 3 — Feux annuel
# ═══════════════════════════════════════════════════════════════════════════════
by_yr = fires.groupby("annee").agg(nb=("surface_totale_ha","count"), surf=("surface_totale_ha","sum")).reset_index()
fig_feux = make_subplots(specs=[[{"secondary_y": True}]])
fig_feux.add_bar(x=by_yr["annee"].tolist(), y=by_yr["surf"].round(0).tolist(),
                 name="Surface (ha)", marker_color=C["red"], marker_opacity=0.65,
                 hovertemplate="%{x} : %{y:,.0f} ha<extra></extra>")
fig_feux.add_scatter(x=by_yr["annee"].tolist(), y=by_yr["nb"].tolist(),
                     name="Nb incendies", mode="lines+markers",
                     line=dict(color=C["amber"], width=2),
                     marker=dict(size=5, color=C["amber"]),
                     hovertemplate="%{x} : %{y:,} incendies<extra></extra>",
                     secondary_y=True)
fig_feux.update_layout(**{**PLOT, "height": 300,
                          "legend": dict(orientation="h", y=1.1, bgcolor="rgba(0,0,0,0)"),
                          "margin": dict(t=20, b=40, l=52, r=52)})
fig_feux.update_yaxes(title_text="Surface (ha)", secondary_y=False,
                      gridcolor="rgba(255,255,255,0.05)", tickfont=dict(color=C["muted"]))
fig_feux.update_yaxes(title_text="Nb incendies", secondary_y=True,
                      gridcolor="rgba(0,0,0,0)", tickfont=dict(color=C["muted"]))
J_FEUX = fig_json(fig_feux)

# ═══════════════════════════════════════════════════════════════════════════════
# CHART 4 — Carte feux
# ═══════════════════════════════════════════════════════════════════════════════
dept_agg = fires.groupby("departement").agg(surf=("surface_totale_ha","sum"), nb=("surface_totale_ha","count")).reset_index()
if dept_geojson:
    fig_map = px.choropleth(
        dept_agg, geojson=dept_geojson,
        locations="departement", featureidkey="properties.code",
        color="surf",
        color_continuous_scale=[[0,"#0a0d14"],[0.2,"#431407"],[0.5,"#c2410c"],[1,"#fbbf24"]],
        hover_data={"surf":":.0f", "nb":True},
        labels={"surf":"Surface (ha)","nb":"Incendies","departement":"Dép."},
    )
    fig_map.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)")
    fig_map.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", geo_bgcolor="rgba(0,0,0,0)",
        height=380, margin=dict(t=0,b=0,l=0,r=0),
        coloraxis_colorbar=dict(title="ha", thickness=10,
                                tickfont=dict(color=C["muted"]),
                                titlefont=dict(color=C["muted"])),
    )
    J_MAP = fig_json(fig_map)
else:
    top = dept_agg.nlargest(20,"surf")
    fig_map = go.Figure(go.Bar(
        x=top["surf"].round(0).tolist(), y=top["departement"].tolist(),
        orientation="h", marker_color=C["red"], marker_opacity=0.7,
        hovertemplate="Dép. %{y} : %{x:,.0f} ha<extra></extra>",
    ))
    apply(fig_map, h=380, xaxis_title="Surface brûlée (ha)", yaxis_title="")
    J_MAP = fig_json(fig_map)

# ═══════════════════════════════════════════════════════════════════════════════
# CHART 5 — CO2
# ═══════════════════════════════════════════════════════════════════════════════
fig_co2 = go.Figure()
fig_co2.add_scatter(x=co2["year"].tolist(), y=co2["co2_ppm"].round(2).tolist(),
                    fill="tozeroy", fillcolor="rgba(251,191,36,0.08)",
                    line=dict(color=C["amber"], width=2),
                    hovertemplate="%{x} : %{y:.1f} ppm<extra></extra>", name="CO₂")
for val, label, color in [(280,"Préindustriel",C["muted"]),(350,"Seuil sécurité",C["blue"]),(421,"Actuel",C["red"])]:
    fig_co2.add_hline(y=val, line_dash="dot", line_color=color, line_width=1,
                      annotation_text=f" {label} · {val} ppm",
                      annotation_font=dict(size=9, color=color))
apply(fig_co2, h=280, yaxis_title="ppm", showlegend=False)
J_CO2 = fig_json(fig_co2)

# ═══════════════════════════════════════════════════════════════════════════════
# CHART 6 — Émissions
# ═══════════════════════════════════════════════════════════════════════════════
fig_emi = go.Figure()
fig_emi.add_scatter(x=emi["annee"].tolist(), y=emi["emissions_production_interieure_MtCO2e"].tolist(),
                    name="Émissions intérieures", fill="tozeroy",
                    fillcolor="rgba(96,165,250,0.1)", line=dict(color=C["blue"], width=2),
                    hovertemplate="%{x} : %{y:.0f} MtCO₂e<extra></extra>")
fig_emi.add_scatter(x=emi["annee"].tolist(), y=emi["emissions_importees_MtCO2e"].tolist(),
                    name="Émissions importées", fill="tozeroy",
                    fillcolor="rgba(248,113,113,0.1)", line=dict(color=C["red"], width=2),
                    hovertemplate="%{x} : %{y:.0f} MtCO₂e<extra></extra>")
apply(fig_emi, h=280, yaxis_title="MtCO₂e", legend=dict(orientation="h", y=1.12))
J_EMI = fig_json(fig_emi)

# ═══════════════════════════════════════════════════════════════════════════════
# CHART 7 — Empreinte
# ═══════════════════════════════════════════════════════════════════════════════
fig_emp = go.Figure()
fig_emp.add_scatter(x=emp["annee"].tolist(), y=emp["empreinte_carbone_tCO2e_par_habitant"].tolist(),
                    mode="lines+markers", line=dict(color=C["blue"], width=2.5),
                    fill="tozeroy", fillcolor="rgba(96,165,250,0.07)",
                    marker=dict(size=4, color=C["blue"]),
                    hovertemplate="%{x} : %{y:.1f} tCO₂e/hab.<extra></extra>")
fig_emp.add_hline(y=2, line_dash="dash", line_color=C["green"], line_width=1.5,
                  annotation_text=" Objectif 2050 : 2 tCO₂e",
                  annotation_font=dict(size=9, color=C["green"]))
apply(fig_emp, h=280, yaxis_title="tCO₂e / habitant", showlegend=False)
J_EMP = fig_json(fig_emp)

# ═══════════════════════════════════════════════════════════════════════════════
# CHART 8 — Précipitations
# ═══════════════════════════════════════════════════════════════════════════════
fig_prec = go.Figure()
fig_prec.add_bar(x=prec_a["year"].tolist(), y=prec_a["anom"].round(2).tolist(),
                 marker_color=[C["blue"] if v>=0 else C["red"] for v in prec_a["anom"]],
                 marker_opacity=0.6, name="Anomalie précip.",
                 hovertemplate="%{x} : %{y:+.1f} mm/mois<extra></extra>")
roll_p = prec_a["anom"].rolling(10, center=True).mean()
fig_prec.add_scatter(x=prec_a["year"].tolist(), y=roll_p.round(2).tolist(), mode="lines",
                     line=dict(color=C["text"], width=2.5), name="Tendance 10 ans",
                     hovertemplate="%{x} : %{y:+.1f} mm/mois<extra></extra>")
fig_prec.add_hline(y=0, line_color=C["dim"], line_width=1)
apply(fig_prec, h=300, yaxis_title="Anomalie (mm/mois)", legend=dict(orientation="h", y=1.12))
J_PREC = fig_json(fig_prec)

# ═══════════════════════════════════════════════════════════════════════════════
# CHART 9 — Feux heatmap saisonnalité
# ═══════════════════════════════════════════════════════════════════════════════
fig_feux_hm = go.Figure(go.Heatmap(
    z=z_hm,
    x=[MONTH_NAMES[m] for m in months_hm],
    y=years_hm,
    colorscale=[[0,"#0a0d14"],[0.15,"#431407"],[0.5,"#c2410c"],[0.8,"#f97316"],[1,"#fbbf24"]],
    hovertemplate="Année %{y}, %{x} : %{z:,.0f} ha<extra></extra>",
    colorbar=dict(title="ha", thickness=10, tickfont=dict(color=C["muted"]), titlefont=dict(color=C["muted"])),
))
apply(fig_feux_hm, h=420,
      xaxis=dict(gridcolor="rgba(0,0,0,0)", side="top", tickfont=dict(color=C["muted"])),
      yaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickfont=dict(color=C["muted"]), autorange="reversed"),
      margin=dict(t=40, b=20, l=52, r=16))
J_FEUX_HM = fig_json(fig_feux_hm)

# ═══════════════════════════════════════════════════════════════════════════════
# CHART 10 — Sécheresse VigiEau
# ═══════════════════════════════════════════════════════════════════════════════
fig_seche = go.Figure()
for g in GRAV_ORDER:
    if g in seche_pivot.columns:
        fig_seche.add_bar(
            x=seche_pivot.index.tolist(),
            y=seche_pivot[g].tolist(),
            name=GRAV_LABELS[g],
            marker_color=GRAV_COLORS[g],
            marker_opacity=0.8,
            hovertemplate=f"<b>{GRAV_LABELS[g]}</b><br>%{{x}} : %{{y}} dép.<extra></extra>",
        )
fig_seche.update_layout(barmode="stack")
apply(fig_seche, h=320,
      xaxis_title="", yaxis_title="Nb de départements",
      legend=dict(orientation="h", y=1.12, bgcolor="rgba(0,0,0,0)"),
      xaxis=dict(tickangle=-45, gridcolor="rgba(255,255,255,0.05)", tickfont=dict(color=C["muted"])))
J_SECHE = fig_json(fig_seche)

# ═══════════════════════════════════════════════════════════════════════════════
# CHART 11 — Glaciers bilan de masse cumulé
# ═══════════════════════════════════════════════════════════════════════════════
GLAC_COLORS = [C["blue"], C["cyan"], C["green"], C["purple"], C["amber"]]
fig_glac = go.Figure()
for i, g in enumerate(glaciers_list):
    sub = glac_cum[g]
    color = GLAC_COLORS[i % len(GLAC_COLORS)]
    fig_glac.add_scatter(
        x=sub["Year"].tolist(), y=sub["cumul"].round(3).tolist(),
        mode="lines", name=g.title(),
        line=dict(color=color, width=2),
        hovertemplate=f"<b>{g.title()}</b><br>%{{x}} : %{{y:+.2f}} m éq. eau<extra></extra>",
    )
fig_glac.add_hline(y=0, line_color=C["dim"], line_width=1)
apply(fig_glac, h=320,
      xaxis_title="", yaxis_title="Bilan cumulé (m éq. eau)",
      legend=dict(orientation="h", y=1.12, bgcolor="rgba(0,0,0,0)"))
J_GLAC = fig_json(fig_glac)

print("Generating HTML...")

# ═══════════════════════════════════════════════════════════════════════════════
# HTML
# ═══════════════════════════════════════════════════════════════════════════════
HTML = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Climat France 2100</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root {{
  --bg:     {C['bg']};
  --s1:     {C['s1']};
  --s2:     {C['s2']};
  --border: {C['border']};
  --text:   {C['text']};
  --muted:  {C['muted']};
  --dim:    {C['dim']};
  --blue:   {C['blue']};
  --amber:  {C['amber']};
  --red:    {C['red']};
  --green:  {C['green']};
  --purple: {C['purple']};
  --cyan:   {C['cyan']};
}}

*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
html {{ scroll-behavior: smooth; }}

body {{
  font-family: 'Inter', system-ui, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}}

/* ── NAV ── */
nav {{
  position: fixed; top: 0; left: 0; right: 0; z-index: 100;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 2.5rem;
  height: 56px;
  background: rgba(10,13,20,0.75);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border);
}}
.nav-brand {{
  font-size: 0.9rem; font-weight: 700; letter-spacing: -0.01em;
  background: linear-gradient(135deg, var(--blue), var(--purple));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}}
.nav-links {{ display: flex; gap: 1.6rem; list-style: none; }}
.nav-links a {{
  font-size: 0.78rem; font-weight: 500; color: var(--muted);
  text-decoration: none; letter-spacing: 0.02em;
  transition: color 0.2s;
}}
.nav-links a:hover {{ color: var(--text); }}
.nav-badge {{
  font-size: 0.7rem; padding: 0.25rem 0.75rem; border-radius: 20px;
  background: rgba(96,165,250,0.1); color: var(--blue);
  border: 1px solid rgba(96,165,250,0.2); font-weight: 500;
}}

/* ── LAYOUT ── */
main {{ padding-top: 56px; }}
.section {{
  padding: 5rem 2.5rem;
  max-width: 1280px;
  margin: 0 auto;
}}
.section + .section {{ border-top: 1px solid var(--border); }}

/* ── HERO ── */
#hero {{
  min-height: 88vh;
  display: flex; flex-direction: column; justify-content: center;
  padding: 6rem 2.5rem 4rem;
  max-width: 1280px;
  margin: 0 auto;
}}
.hero-eyebrow {{
  font-size: 0.72rem; font-weight: 600; letter-spacing: 0.12em;
  text-transform: uppercase; color: var(--blue); margin-bottom: 1.2rem;
}}
.hero-title {{
  font-size: clamp(2.5rem, 5vw, 4.5rem);
  font-weight: 800; letter-spacing: -0.03em; line-height: 1.05;
  max-width: 800px; margin-bottom: 1.5rem;
}}
.hero-title span {{
  background: linear-gradient(135deg, var(--blue) 0%, var(--purple) 50%, var(--amber) 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}}
.hero-sub {{
  font-size: 1.05rem; color: var(--muted); max-width: 560px;
  line-height: 1.7; margin-bottom: 3.5rem; font-weight: 400;
}}
.kpi-grid {{
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem;
}}
@media (max-width: 900px) {{ .kpi-grid {{ grid-template-columns: repeat(2,1fr); }} }}

.kpi {{
  background: var(--s1);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 1.4rem 1.5rem;
  position: relative; overflow: hidden;
  transition: border-color 0.3s, background 0.3s;
}}
.kpi:hover {{
  background: var(--s2);
  border-color: rgba(255,255,255,0.15);
}}
.kpi::before {{
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: var(--accent, var(--blue));
  opacity: 0.6;
}}
.kpi-label {{
  font-size: 0.68rem; font-weight: 600; letter-spacing: 0.1em;
  text-transform: uppercase; color: var(--muted); margin-bottom: 0.6rem;
}}
.kpi-val {{
  font-size: 2rem; font-weight: 700; letter-spacing: -0.03em;
  color: var(--text); line-height: 1;
}}
.kpi-val.accent {{ color: var(--accent, var(--blue)); }}
.kpi-sub {{ font-size: 0.75rem; color: var(--dim); margin-top: 0.4rem; }}

/* ── SECTIONS ── */
.section-eyebrow {{
  font-size: 0.68rem; font-weight: 700; letter-spacing: 0.12em;
  text-transform: uppercase; color: var(--blue); margin-bottom: 0.6rem;
}}
.section-title {{
  font-size: clamp(1.5rem, 3vw, 2.2rem);
  font-weight: 700; letter-spacing: -0.025em;
  margin-bottom: 0.6rem;
}}
.section-sub {{
  font-size: 0.9rem; color: var(--muted); max-width: 600px;
  line-height: 1.7; margin-bottom: 2.5rem;
}}

/* ── CARDS ── */
.card {{
  background: var(--s1);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 1.5rem;
  transition: border-color 0.2s;
}}
.card:hover {{ border-color: rgba(255,255,255,0.13); }}
.card-title {{
  font-size: 0.75rem; font-weight: 600;
  letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--muted); margin-bottom: 1rem;
}}

/* ── GRID LAYOUTS ── */
.grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.2rem; }}
.grid-3 {{ display: grid; grid-template-columns: repeat(3,1fr); gap: 1rem; }}
@media (max-width: 900px) {{
  .grid-2, .grid-3 {{ grid-template-columns: 1fr; }}
}}

/* ── SCENARIO CARDS ── */
.scenario-cards {{ display: grid; grid-template-columns: repeat(3,1fr); gap: 1rem; margin-bottom: 1.5rem; }}
.s-card {{
  background: var(--s1); border: 1px solid var(--border);
  border-radius: 12px; padding: 1.2rem 1.4rem;
  border-top: 2px solid var(--s-color);
}}
.s-card-name {{ font-size: 0.72rem; font-weight: 600; letter-spacing: 0.06em;
               text-transform: uppercase; color: var(--s-color); margin-bottom: 0.8rem; }}
.s-card-years {{ display: flex; gap: 1.5rem; }}
.s-year {{ text-align: center; }}
.s-year-label {{ font-size: 0.62rem; color: var(--muted); text-transform: uppercase;
                letter-spacing: 0.06em; }}
.s-year-val {{ font-size: 1.6rem; font-weight: 700; color: var(--s-color);
              letter-spacing: -0.03em; }}

/* ── RECO CARDS ── */
.reco {{
  background: var(--s1); border: 1px solid var(--border);
  border-radius: 14px; padding: 1.6rem;
  border-left: 2px solid var(--r-color);
}}
.reco-title {{ font-size: 0.9rem; font-weight: 600; color: var(--text);
              margin-bottom: 1rem; }}
.reco-item {{
  font-size: 0.82rem; color: var(--muted);
  padding: 0.3rem 0 0.3rem 0.9rem;
  border-left: 1px solid var(--border);
  margin-bottom: 0.3rem;
}}
.reco-source {{
  display: inline-block; margin-top: 1rem; font-size: 0.68rem;
  color: rgba(71,85,105,0.7); background: rgba(255,255,255,0.03);
  padding: 0.2rem 0.6rem; border-radius: 4px;
  border: 1px solid var(--border);
}}

/* ── REF CARDS ── */
.ref-grid {{ display: grid; grid-template-columns: repeat(5,1fr); gap: 0.8rem; }}
.ref-card {{
  background: var(--s1); border: 1px solid var(--border);
  border-radius: 10px; padding: 1rem;
  border-top: 1px solid var(--r-color);
}}
.ref-name {{ font-size: 0.68rem; font-weight: 700; color: var(--r-color);
            text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.4rem; }}
.ref-desc {{ font-size: 0.78rem; color: var(--muted); line-height: 1.4; margin-bottom: 0.5rem; }}
.ref-year {{ font-size: 0.68rem; color: rgba(71,85,105,0.6); }}

/* ── DIVIDER ── */
.divider {{ border: none; border-top: 1px solid var(--border); margin: 2rem 0; }}

/* ── CHART WRAP ── */
.chart-wrap {{ border-radius: 12px; overflow: hidden; }}

/* ── FOOTER ── */
footer {{
  border-top: 1px solid var(--border);
  padding: 2rem 2.5rem;
  display: flex; justify-content: space-between; align-items: center;
}}
.footer-left {{ font-size: 0.78rem; color: var(--muted); }}
.footer-sources {{ font-size: 0.72rem; color: rgba(71,85,105,0.6); }}

/* ── SCROLLBAR ── */
::-webkit-scrollbar {{ width: 5px; }}
::-webkit-scrollbar-track {{ background: var(--bg); }}
::-webkit-scrollbar-thumb {{ background: var(--dim); border-radius: 3px; }}

/* ── CHATBOT ── */
#chat-btn {{
  position: fixed; bottom: 2rem; right: 2rem; z-index: 200;
  width: 52px; height: 52px; border-radius: 50%;
  background: linear-gradient(135deg, var(--blue), var(--purple));
  border: none; cursor: pointer; display: flex; align-items: center; justify-content: center;
  box-shadow: 0 4px 24px rgba(96,165,250,0.35);
  transition: transform 0.2s, box-shadow 0.2s;
}}
#chat-btn:hover {{ transform: scale(1.08); box-shadow: 0 6px 32px rgba(96,165,250,0.5); }}
#chat-btn svg {{ width: 22px; height: 22px; fill: white; }}

#chat-panel {{
  position: fixed; bottom: 5.5rem; right: 2rem; z-index: 200;
  width: 380px; max-height: 520px;
  background: #0f1624;
  border: 1px solid var(--border);
  border-radius: 18px;
  display: flex; flex-direction: column;
  box-shadow: 0 24px 64px rgba(0,0,0,0.6);
  transform: scale(0.92) translateY(12px);
  opacity: 0; pointer-events: none;
  transition: opacity 0.22s ease, transform 0.22s ease;
}}
#chat-panel.open {{
  opacity: 1; transform: scale(1) translateY(0); pointer-events: all;
}}
.chat-header {{
  padding: 1rem 1.2rem 0.8rem;
  border-bottom: 1px solid var(--border);
  display: flex; align-items: center; justify-content: space-between;
}}
.chat-header-title {{
  font-size: 0.82rem; font-weight: 600; color: var(--text);
}}
.chat-header-sub {{ font-size: 0.68rem; color: var(--muted); }}
.chat-close {{
  background: none; border: none; cursor: pointer; color: var(--muted); font-size: 1.1rem;
  line-height: 1; padding: 0.1rem 0.3rem; border-radius: 4px;
  transition: color 0.15s;
}}
.chat-close:hover {{ color: var(--text); }}

/* Messages */
#chat-messages {{
  flex: 1; overflow-y: auto; padding: 1rem;
  display: flex; flex-direction: column; gap: 0.7rem;
  display: none;
}}
#chat-messages::-webkit-scrollbar {{ width: 3px; }}
#chat-messages::-webkit-scrollbar-thumb {{ background: var(--dim); }}

.chat-msg {{
  max-width: 88%; padding: 0.65rem 0.9rem;
  border-radius: 12px; font-size: 0.82rem; line-height: 1.55;
}}
.chat-msg.user {{
  background: linear-gradient(135deg, rgba(96,165,250,0.18), rgba(167,139,250,0.18));
  border: 1px solid rgba(96,165,250,0.2);
  align-self: flex-end; color: var(--text);
}}
.chat-msg.assistant {{
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--border);
  align-self: flex-start; color: var(--text);
}}
.chat-msg.thinking {{
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--border);
  align-self: flex-start; color: var(--muted);
  font-style: italic; font-size: 0.75rem;
}}

#chat-input-wrap {{
  padding: 0.8rem 1rem; border-top: 1px solid var(--border);
  display: flex; gap: 0.6rem; align-items: flex-end;
}}
#chat-input {{
  flex: 1; background: rgba(255,255,255,0.05);
  border: 1px solid var(--border); border-radius: 10px;
  padding: 0.55rem 0.85rem; color: var(--text); font-size: 0.82rem;
  font-family: 'Inter', sans-serif; outline: none; resize: none;
  max-height: 100px; line-height: 1.4;
}}
#chat-input:focus {{ border-color: var(--blue); }}
#chat-send {{
  background: linear-gradient(135deg, var(--blue), var(--purple));
  border: none; border-radius: 8px; padding: 0.55rem 0.9rem;
  color: white; font-size: 0.78rem; font-weight: 600; cursor: pointer;
  white-space: nowrap; transition: opacity 0.15s;
}}
#chat-send:hover {{ opacity: 0.85; }}
#chat-send:disabled {{ opacity: 0.4; cursor: not-allowed; }}
</style>
</head>
<body>

<!-- NAV -->
<nav>
  <div class="nav-brand">Climat France 2100</div>
  <ul class="nav-links">
    <li><a href="#temperatures">Températures</a></li>
    <li><a href="#feux">Feux de forêt</a></li>
    <li><a href="#emissions">Émissions</a></li>
    <li><a href="#precipitations">Précipitations</a></li>
    <li><a href="#secheresse">Sécheresse</a></li>
    <li><a href="#glaciers">Glaciers</a></li>
    <li><a href="#preconisations">Préconisations</a></li>
  </ul>
  <span class="nav-badge">IPCC AR6</span>
</nav>

<main>

<!-- HERO -->
<div id="hero" class="section" style="max-width:1280px;margin:0 auto">
  <div class="hero-eyebrow">Hackathon Big Data & IA — Mastère Informatique</div>
  <h1 class="hero-title">
    La France face au<br><span>changement climatique</span>
  </h1>
  <p class="hero-sub">
    Analyse historique 1931–2023 · Modèle IA log-linéaire entraîné sur la relation CO₂/température ·
    Projections IPCC AR6 pour 2030, 2050 et 2100.
  </p>

  <div class="kpi-grid">
    <div class="kpi" style="--accent:{C['red']}">
      <div class="kpi-label">Anomalie température 2023</div>
      <div class="kpi-val accent">{anom_2023:+.2f}°C</div>
      <div class="kpi-sub">vs référence 1961–1990</div>
    </div>
    <div class="kpi" style="--accent:{C['amber']}">
      <div class="kpi-label">CO₂ atmosphérique</div>
      <div class="kpi-val accent">{co2_last:.0f} ppm</div>
      <div class="kpi-sub">Mauna Loa · NOAA 2024</div>
    </div>
    <div class="kpi" style="--accent:#f97316">
      <div class="kpi-label">Surface brûlée totale</div>
      <div class="kpi-val accent">{fires_tot/1e6:.1f} Mha</div>
      <div class="kpi-sub">Incendies France 2003–2024</div>
    </div>
    <div class="kpi" style="--accent:{C['blue']}">
      <div class="kpi-label">Empreinte carbone</div>
      <div class="kpi-val accent">{emp_last} t</div>
      <div class="kpi-sub">CO₂e par habitant · 2024</div>
    </div>
  </div>
</div>

<!-- TEMPÉRATURES -->
<section class="section" id="temperatures">
  <div class="section-eyebrow">01 — Températures</div>
  <h2 class="section-title">Réchauffement historique & projections</h2>
  <p class="section-sub">
    Modèle log-linéaire : anomalie = f(log CO₂/280). Sensibilité climatique France estimée à
    {coef:.2f}°C par doublement du CO₂ (référence GIEC mondiale : ~3°C).
  </p>

  <div class="scenario-cards">
    {''.join(f"""
    <div class="s-card" style="--s-color:{color}">
      <div class="s-card-name">{name}</div>
      <div class="s-card-years">
        {''.join(f'<div class="s-year"><div class="s-year-label">{yr}</div><div class="s-year-val">{proj_vals[name][yr]:+.1f}°C</div></div>' for yr in [2030, 2050, 2100])}
      </div>
    </div>""" for name, color in SCENE.items())}
  </div>

  <div class="card">
    <div class="card-title">Projections 2024–2100 par scénario IPCC AR6</div>
    <div class="chart-wrap" id="chart-proj"></div>
  </div>

  <div style="margin-top:1.2rem">
    <div class="card">
      <div class="card-title">Anomalie historique France 1931–2023</div>
      <div class="chart-wrap" id="chart-hist"></div>
    </div>
  </div>
</section>

<!-- FEUX -->
<section class="section" id="feux">
  <div class="section-eyebrow">02 — Feux de forêt</div>
  <h2 class="section-title">Incendies en France 2003–2024</h2>
  <p class="section-sub">
    59 618 incendies recensés. La heatmap révèle l'allongement de la saison des feux —
    de juillet–août vers juin–septembre. Source : base BDIFF / Prométhée.
  </p>

  <div class="card" style="margin-bottom:1.2rem">
    <div class="card-title">Saisonnalité des incendies — surface brûlée par mois et par année</div>
    <div class="chart-wrap" id="chart-feux-hm"></div>
  </div>

  <div class="grid-2">
    <div class="card">
      <div class="card-title">Surface brûlée par département (cumul)</div>
      <div class="chart-wrap" id="chart-map"></div>
    </div>
    <div class="card">
      <div class="card-title">Évolution annuelle — surface & nombre d'incendies</div>
      <div class="chart-wrap" id="chart-feux"></div>
    </div>
  </div>
</section>

<!-- ÉMISSIONS -->
<section class="section" id="emissions">
  <div class="section-eyebrow">03 — Émissions & CO₂</div>
  <h2 class="section-title">Trajectoire des gaz à effet de serre</h2>
  <p class="section-sub">
    Concentrations NOAA 1958–2026 · Émissions France SDES 1995–2024 · Empreinte carbone par habitant.
  </p>

  <div class="card" style="margin-bottom:1.2rem">
    <div class="card-title">Concentration atmosphérique CO₂ — Mauna Loa</div>
    <div class="chart-wrap" id="chart-co2"></div>
  </div>

  <div class="grid-2">
    <div class="card">
      <div class="card-title">Émissions France — production vs importées (MtCO₂e)</div>
      <div class="chart-wrap" id="chart-emi"></div>
    </div>
    <div class="card">
      <div class="card-title">Empreinte carbone par habitant (tCO₂e)</div>
      <div class="chart-wrap" id="chart-emp"></div>
    </div>
  </div>
</section>

<!-- PRÉCIPITATIONS -->
<section class="section" id="precipitations">
  <div class="section-eyebrow">04 — Précipitations</div>
  <h2 class="section-title">Déficit pluviométrique</h2>
  <p class="section-sub">
    Anomalie mensuelle moyenne agrégée sur les stations LSH Météo-France · 1947–2023.
    Référence : moyenne 1961–1990 ({REF_P:.1f} mm/mois).
  </p>

  <div class="card">
    <div class="card-title">Anomalie de précipitation annuelle</div>
    <div class="chart-wrap" id="chart-prec"></div>
  </div>
</section>

<!-- SÉCHERESSE -->
<section class="section" id="secheresse">
  <div class="section-eyebrow">05 — Sécheresse</div>
  <h2 class="section-title">Restrictions eau VigiEau 2023–2024</h2>
  <p class="section-sub">
    Nombre de départements sous arrêté de restriction par mois, selon le niveau de gravité.
    Le pic d'août 2024 montre 51 départements en vigilance, 23 en crise. Source : plateforme VigiEau.
  </p>

  <div class="card">
    <div class="card-title">Départements sous restriction par mois et niveau de gravité</div>
    <div class="chart-wrap" id="chart-seche"></div>
  </div>
</section>

<!-- GLACIERS -->
<section class="section" id="glaciers">
  <div class="section-eyebrow">06 — Glaciers</div>
  <h2 class="section-title">Fonte des glaciers français</h2>
  <p class="section-sub">
    Bilan de masse annuel cumulé pour {len(glaciers_list)} glacier(s) français suivi(s) par le WGMS.
    Un bilan négatif croissant indique une perte nette de masse glaciaire.
  </p>

  <div class="card">
    <div class="card-title">Bilan de masse cumulé depuis le début des mesures (m éq. eau)</div>
    <div class="chart-wrap" id="chart-glac"></div>
  </div>
</section>

<!-- PRÉCONISATIONS -->
<section class="section" id="preconisations">
  <div class="section-eyebrow">07 — Préconisations</div>
  <h2 class="section-title">Actions citoyennes & politiques</h2>
  <p class="section-sub">
    Recommandations alignées avec le PNACC 3, l'Earth Action Report 2025
    et la Stratégie Nationale Bas-Carbone.
  </p>

  <div class="grid-2" style="margin-bottom:1.2rem">
    <div class="reco" style="--r-color:{C['red']}">
      <div class="reco-title">Risque accru de feux de forêt</div>
      <div class="reco-item">Débroussaillement obligatoire — 50m autour des habitations</div>
      <div class="reco-item">Essences résistantes au feu en zone à risque</div>
      <div class="reco-item">Plans d'évacuation et voies d'accès pompiers</div>
      <div class="reco-item">Limiter les activités ignifuges en période de sécheresse</div>
      <div class="reco-item">Surveillance par drones et détection précoce (IA)</div>
      <span class="reco-source">PNACC 3 — Axe Forêts & Biodiversité</span>
    </div>
    <div class="reco" style="--r-color:{C['amber']}">
      <div class="reco-title">Vagues de chaleur & caniculaire</div>
      <div class="reco-item">Végétalisation urbaine — arbres, toitures et murs végétalisés</div>
      <div class="reco-item">Rénovation des bâtiments — isolation, ventilation, protections solaires</div>
      <div class="reco-item">Identifier les personnes vulnérables, activer les plans canicule</div>
      <div class="reco-item">Développer des îlots de fraîcheur accessibles en ville</div>
      <div class="reco-item">Adapter les horaires de travail extérieur aux heures fraîches</div>
      <span class="reco-source">Earth Action Report 2025 — Adaptation urbaine</span>
    </div>
    <div class="reco" style="--r-color:{C['blue']}">
      <div class="reco-title">Sécheresse & stress hydrique</div>
      <div class="reco-item">Réduire la consommation d'eau domestique (objectif −10% / 2030)</div>
      <div class="reco-item">Dispositifs de récupération d'eau de pluie</div>
      <div class="reco-item">Variétés agricoles adaptées à la sécheresse</div>
      <div class="reco-item">Anticiper les restrictions via la plateforme VigiEau</div>
      <div class="reco-item">Renaturer les zones humides pour recharge des nappes</div>
      <span class="reco-source">PNACC 3 — Axe Eau & Milieux aquatiques</span>
    </div>
    <div class="reco" style="--r-color:{C['green']}">
      <div class="reco-title">Réduction de l'empreinte carbone</div>
      <div class="reco-item">Objectif national : 2 tCO₂e/hab. d'ici 2050 (actuel : {emp_last} t)</div>
      <div class="reco-item">Mobilité douce et transports collectifs</div>
      <div class="reco-item">Régime alimentaire bas-carbone</div>
      <div class="reco-item">Rénovation énergétique — CEE, MaPrimeRénov</div>
      <div class="reco-item">Réduire les émissions importées via la consommation responsable</div>
      <span class="reco-source">SNBC — Neutralité carbone 2050</span>
    </div>
  </div>

  <hr class="divider">
  <div class="ref-grid">
    <div class="ref-card" style="--r-color:{C['blue']}">
      <div class="ref-name">PNACC 3</div>
      <div class="ref-desc">Adaptation nationale au changement climatique</div>
      <div class="ref-year">Horizon 2030</div>
    </div>
    <div class="ref-card" style="--r-color:{C['green']}">
      <div class="ref-name">SNBC</div>
      <div class="ref-desc">Neutralité carbone France</div>
      <div class="ref-year">Horizon 2050</div>
    </div>
    <div class="ref-card" style="--r-color:{C['amber']}">
      <div class="ref-name">Earth Action 2025</div>
      <div class="ref-desc">Réduction émissions mondiales</div>
      <div class="ref-year">Horizon 2030</div>
    </div>
    <div class="ref-card" style="--r-color:{C['red']}">
      <div class="ref-name">Accord de Paris</div>
      <div class="ref-desc">Limiter le réchauffement à +1.5°C</div>
      <div class="ref-year">Horizon 2100</div>
    </div>
    <div class="ref-card" style="--r-color:{C['purple']}">
      <div class="ref-name">Fit for 55 (UE)</div>
      <div class="ref-desc">−55% émissions vs 1990</div>
      <div class="ref-year">Horizon 2030</div>
    </div>
  </div>
</section>

</main>

<footer>
  <div class="footer-left">Climat France 2100 · Hackathon Big Data & IA</div>
  <div class="footer-sources">Météo-France · NOAA · SDES · GéoRisques · VigiEau · WGMS · IPCC AR6</div>
</footer>

<!-- CHATBOT -->
<button id="chat-btn" title="Assistant climatique IA" onclick="toggleChat()">
  <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 2C6.48 2 2 6.48 2 12c0 1.85.5 3.58 1.37 5.07L2 22l4.93-1.37A9.96 9.96 0 0012 22c5.52 0 10-4.48 10-10S17.52 2 12 2zm1 15H7v-2h6v2zm3-4H7v-2h8v2zm0-4H7V7h8v2z"/>
  </svg>
</button>

<div id="chat-panel">
  <div class="chat-header">
    <div>
      <div class="chat-header-title">Assistant Climatique</div>
      <div class="chat-header-sub">Alimenté par Claude · données France 2023</div>
    </div>
    <button class="chat-close" onclick="toggleChat()">✕</button>
  </div>

  <div id="chat-messages" style="display:flex"></div>
  <div id="chat-input-wrap">
    <textarea id="chat-input" rows="1" placeholder="Posez une question sur le climat..."></textarea>
    <button id="chat-send" onclick="sendMessage()">Envoyer</button>
  </div>
</div>

<script>
const CFG = {{displayModeBar: false, responsive: true}};

Plotly.newPlot('chart-proj',    {J_PROJ}.data,    {J_PROJ}.layout,    CFG);
Plotly.newPlot('chart-hist',    {J_HIST}.data,    {J_HIST}.layout,    CFG);
Plotly.newPlot('chart-feux-hm', {J_FEUX_HM}.data, {J_FEUX_HM}.layout, CFG);
Plotly.newPlot('chart-map',     {J_MAP}.data,     {J_MAP}.layout,     CFG);
Plotly.newPlot('chart-feux',    {J_FEUX}.data,    {J_FEUX}.layout,    CFG);
Plotly.newPlot('chart-co2',     {J_CO2}.data,     {J_CO2}.layout,     CFG);
Plotly.newPlot('chart-emi',     {J_EMI}.data,     {J_EMI}.layout,     CFG);
Plotly.newPlot('chart-emp',     {J_EMP}.data,     {J_EMP}.layout,     CFG);
Plotly.newPlot('chart-prec',    {J_PREC}.data,    {J_PREC}.layout,    CFG);
Plotly.newPlot('chart-seche',   {J_SECHE}.data,   {J_SECHE}.layout,   CFG);
Plotly.newPlot('chart-glac',    {J_GLAC}.data,    {J_GLAC}.layout,    CFG);

// Fade-in on scroll
const observer = new IntersectionObserver((entries) => {{
  entries.forEach(e => {{ if (e.isIntersecting) e.target.style.opacity = '1'; }});
}}, {{ threshold: 0.05 }});
document.querySelectorAll('.kpi, .card, .reco, .s-card').forEach(el => {{
  el.style.opacity = '0';
  el.style.transition = 'opacity 0.5s ease';
  observer.observe(el);
}});

// ── Chatbot ──────────────────────────────────────────────────────────────────
let chatOpen = false;
let history  = [];

const MISTRAL_KEY = 'nmCABRK2Azl0J99UOfKVcLOctIzRG99M';
const SYSTEM = {json.dumps(chatbot_context)};

function toggleChat() {{
  chatOpen = !chatOpen;
  document.getElementById('chat-panel').classList.toggle('open', chatOpen);
}}

function addMsg(role, text) {{
  const d = document.getElementById('chat-messages');
  const el = document.createElement('div');
  el.className = 'chat-msg ' + role;
  el.textContent = text;
  d.appendChild(el);
  d.scrollTop = d.scrollHeight;
  return el;
}}

async function sendMessage() {{
  const input = document.getElementById('chat-input');
  const btn   = document.getElementById('chat-send');
  const text  = input.value.trim();
  if (!text) return;

  input.value = '';
  input.style.height = 'auto';
  addMsg('user', text);
  history.push({{ role: 'user', content: text }});

  btn.disabled = true;
  const thinking = addMsg('thinking', 'En train de répondre...');

  try {{
    const res = await fetch('https://api.mistral.ai/v1/chat/completions', {{
      method: 'POST',
      headers: {{
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + MISTRAL_KEY,
      }},
      body: JSON.stringify({{
        model: 'mistral-small-latest',
        max_tokens: 512,
        messages: [
          {{ role: 'system', content: SYSTEM }},
          ...history,
        ],
      }}),
    }});

    const data = await res.json();
    thinking.remove();

    if (data.error) {{
      addMsg('assistant', 'Erreur : ' + (data.error.message || JSON.stringify(data.error)));
    }} else {{
      const reply = data.choices[0].message.content;
      addMsg('assistant', reply);
      history.push({{ role: 'assistant', content: reply }});
    }}
  }} catch(e) {{
    thinking.remove();
    addMsg('assistant', 'Erreur réseau : ' + e.message);
  }}

  btn.disabled = false;
}}

// Init welcome message
addMsg('assistant', 'Bonjour ! Je suis votre assistant climatique, alimenté par Mistral. Posez-moi une question sur les données — températures, projections, incendies, sécheresse, glaciers...');

// Enter key sends
document.getElementById('chat-input').addEventListener('keydown', e => {{
  if (e.key === 'Enter' && !e.shiftKey) {{ e.preventDefault(); sendMessage(); }}
}});

// Auto-resize textarea
document.getElementById('chat-input').addEventListener('input', function() {{
  this.style.height = 'auto';
  this.style.height = Math.min(this.scrollHeight, 100) + 'px';
}});
</script>
</body>
</html>"""

OUT.write_text(HTML, encoding="utf-8")
size = OUT.stat().st_size / 1024
print(f"\nDone → {OUT}  ({size:.0f} KB)")
print("Open with:  open dashboard.html")
