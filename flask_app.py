"""
flask_app.py — Climat France 2100 · Flask SPA
"""
from flask import Flask, render_template, jsonify, request
import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from pathlib import Path
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error
import requests as http_req
import functools
import json

app = Flask(__name__)
DATA = Path("data")

# ── Palette ───────────────────────────────────────────────────────────────────
BG       = "#07090f"
BG_CARD  = "#0d1117"
BG_CARD2 = "#111827"
BORDER   = "rgba(255,255,255,0.07)"
TEXT     = "#f0f4f8"
TEXT_SUB = "#6b7f99"
TEXT_DIM = "#3d4f63"
BLUE     = "#3b82f6"
AMBER    = "#f59e0b"
RED      = "#ef4444"
GREEN    = "#10b981"

SCENARIO_COLORS = {
    "Optimiste (+1.4°C)":      BLUE,
    "Intermédiaire (+2.7°C)":  AMBER,
    "Pessimiste (+4.4°C)":     RED,
}
SCENARIO_CO2 = {
    "Optimiste (+1.4°C)":      {2024:422, 2030:430, 2040:438, 2050:428, 2075:400, 2100:390},
    "Intermédiaire (+2.7°C)":  {2024:422, 2030:435, 2040:455, 2050:480, 2075:530, 2100:550},
    "Pessimiste (+4.4°C)":     {2024:422, 2030:445, 2040:490, 2050:550, 2075:750, 2100:1100},
}

PLOT = dict(
    plot_bgcolor=BG_CARD,
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color=TEXT_SUB, family="Inter, system-ui, sans-serif", size=11),
    xaxis=dict(gridcolor="rgba(255,255,255,0.04)", linecolor="rgba(255,255,255,0.08)",
               tickcolor=TEXT_DIM, title_font=dict(color=TEXT_SUB)),
    yaxis=dict(gridcolor="rgba(255,255,255,0.04)", linecolor="rgba(255,255,255,0.08)",
               tickcolor=TEXT_DIM, title_font=dict(color=TEXT_SUB)),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT_SUB)),
    hoverlabel=dict(bgcolor="#1e293b", font_color=TEXT, bordercolor=BORDER),
    margin=dict(t=30, b=40, l=50, r=20),
)

# ── Simple dict cache ─────────────────────────────────────────────────────────
_cache = {}

def cached(key):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            if key not in _cache:
                _cache[key] = fn(*args, **kwargs)
            return _cache[key]
        return wrapper
    return decorator

# ── Helpers ───────────────────────────────────────────────────────────────────
def apply(fig, h=340, **kw):
    layout = {**PLOT, "height": h, **kw}
    fig.update_layout(**layout)
    return fig

def fig_json(fig):
    d = json.loads(fig.to_json())
    return {"data": d["data"], "layout": d["layout"]}

def project_scenario(model, ref, target_year=2100):
    results = {}
    years = np.arange(2024, target_year + 1)
    for name, anchors in SCENARIO_CO2.items():
        pts = sorted(anchors.items())
        co2 = np.interp(years, [p[0] for p in pts], [p[1] for p in pts])
        anom = model.predict(np.log(co2 / 280).reshape(-1, 1)).flatten()
        results[name] = pd.DataFrame({"year": years, "co2": co2, "anomalie": anom, "tmoy": ref + anom})
    return results

# ── Data loaders ──────────────────────────────────────────────────────────────
@cached("temperatures")
def load_temperatures():
    def _load(path):
        df = pd.read_csv(path, low_memory=False)
        df = df[df["Q_HOM"] == 1].copy()
        df["year"]  = df["YYYYMM"] // 100
        df["month"] = df["YYYYMM"] % 100
        return df
    tx = _load(DATA / "temperatures/SH_TX_metropole_concat.csv")
    tn = _load(DATA / "temperatures/SH_TN_metropole_concat.csv")
    monthly = pd.concat([
        tx.groupby(["year","month"])["VALEUR"].mean().rename("tx"),
        tn.groupby(["year","month"])["VALEUR"].mean().rename("tn"),
    ], axis=1).dropna().reset_index()
    monthly["tmoy"] = (monthly["tx"] + monthly["tn"]) / 2
    annual = monthly.groupby("year")[["tx","tn","tmoy"]].mean().reset_index()
    ref = annual[(annual.year>=1961)&(annual.year<=1990)]["tmoy"].mean()
    annual["anomalie"] = annual["tmoy"] - ref
    return annual, ref

@cached("co2")
def load_co2():
    df = pd.read_csv(DATA / "emissions_gaz/co2_mm_mlo.csv", comment="#")
    df.columns = [c.strip() for c in df.columns]
    return (df[df["average"]>0]
            .groupby("year")["average"].mean()
            .reset_index()
            .rename(columns={"average":"co2_ppm"}))

@cached("fires")
def load_fires():
    df = pd.read_csv(DATA / "feux/incendies_2003_2024.csv", low_memory=False)
    df["mois"] = pd.to_datetime(df["date_alerte"], errors="coerce").dt.month
    return df

@cached("emissions")
def load_emissions():
    return pd.read_csv(DATA / "emissions_gaz/emissions_france_1995_2024.csv")

@cached("empreinte")
def load_empreinte():
    return pd.read_csv(DATA / "emissions_gaz/empreinte_carbone_france_par_habitant_1990_2024.csv")

@cached("ges_secteur")
def load_ges_secteur():
    df = pd.read_csv(DATA / "emissions_gaz/sdes_ges_namea.csv", sep=";")
    df.columns = [c.strip() for c in df.columns]
    return df

@cached("precipitation")
def load_precipitation():
    df = pd.read_csv(DATA / "precipitations/SH_RR_metropole_concat.csv", low_memory=False)
    df = df[df["Q_HOM"]==1].copy()
    df["year"] = df["YYYYMM"] // 100
    annual = df.groupby("year")["VALEUR"].mean().reset_index().rename(columns={"VALEUR":"precip_mm"})
    ref = annual[(annual.year>=1961)&(annual.year<=1990)]["precip_mm"].mean()
    annual["anomalie"] = annual["precip_mm"] - ref
    return annual, ref

@cached("precip_by_dept")
def load_precip_by_dept():
    df = pd.read_csv(DATA / "precipitations/SH_RR_metropole_concat.csv", low_memory=False)
    df = df[df["Q_HOM"] == 1].copy()
    df["year"] = df["YYYYMM"] // 100
    df["dept"] = df["num_poste"].astype(str).str.zfill(8).str[:2]
    annual = (df.groupby(["dept","year"])["VALEUR"]
              .mean().reset_index()
              .rename(columns={"VALEUR":"precip_mm"}))
    ref = (annual[(annual.year>=1961)&(annual.year<=1990)]
           .groupby("dept")["precip_mm"].mean().rename("ref_p"))
    annual = annual.merge(ref, on="dept")
    annual["anomalie"] = annual["precip_mm"] - annual["ref_p"]
    return annual

@cached("hot_days")
def load_hot_days():
    df = pd.read_csv(
        DATA / "temperatures/Q_75_previous-1950-2024_RR-T-Vent.csv.gz",
        compression="gzip", sep=";",
        usecols=["NUM_POSTE","AAAAMMJJ","TX"],
    )
    df = df[df["NUM_POSTE"] == 75114001].dropna(subset=["TX"])
    df["year"] = df["AAAAMMJJ"].astype(str).str[:4].astype(int)
    hot = df[df["TX"]>=30].groupby("year").size().reset_index(name="jours_30")
    all_years = pd.DataFrame({"year": range(df["year"].min(), df["year"].max()+1)})
    hot = all_years.merge(hot, on="year", how="left").fillna(0)
    hot["jours_30"] = hot["jours_30"].astype(int)
    ref = hot[(hot.year>=1961)&(hot.year<=1990)]["jours_30"].mean()
    return hot, ref

@cached("dept_geojson")
def get_dept_geojson():
    url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements-version-simplifiee.geojson"
    try:
        return http_req.get(url, timeout=8).json()
    except Exception:
        return None

@cached("model")
def build_model():
    annual, ref = load_temperatures()
    co2 = load_co2()
    df = annual.merge(co2, on="year").dropna()
    df["log_co2"] = np.log(df["co2_ppm"] / 280)
    X = df[["log_co2"]].values
    y = df["anomalie"].values
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=False)

    def make_models():
        return {
            "Régression linéaire": LinearRegression(),
            "Polynomiale (deg. 2)": Pipeline([
                ("poly", PolynomialFeatures(2, include_bias=False)),
                ("lr", LinearRegression()),
            ]),
            "Random Forest": RandomForestRegressor(n_estimators=100, random_state=42),
            "Gradient Boosting": GradientBoostingRegressor(n_estimators=100, random_state=42),
        }

    metrics = {}
    for name, m in make_models().items():
        m.fit(X_train, y_train)
        pred = m.predict(X_test)
        rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
        mae  = float(mean_absolute_error(y_test, pred))
        mask = y_test != 0
        mape = float(np.mean(np.abs((y_test[mask]-pred[mask])/y_test[mask]))*100)
        metrics[name] = {"RMSE": round(rmse,4), "MAE": round(mae,4), "MAPE (%)": round(mape,1)}

    best_name = min(metrics, key=lambda k: metrics[k]["RMSE"])
    best_model = make_models()[best_name]
    best_model.fit(X, y)
    return best_model, ref, metrics, best_name

# ══════════════════════════════════════════════════════════════════════════════
# ROUTES
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/")
def index():
    return render_template("index.html")

# ── API: Vue d'ensemble ───────────────────────────────────────────────────────
@app.route("/api/overview")
def api_overview():
    annual, ref     = load_temperatures()
    co2_df          = load_co2()
    fires_df        = load_fires()
    empreinte       = load_empreinte()
    model, ref_t, _, _ = build_model()
    hot_days, _     = load_hot_days()

    anom_2023  = float(annual[annual.year==2023]["anomalie"].values[0])
    co2_last   = float(co2_df["co2_ppm"].iloc[-1])
    fires_surf = float(fires_df["surface_totale_ha"].sum())
    emp_last   = float(empreinte["empreinte_carbone_tCO2e_par_habitant"].iloc[-1])
    hot_v      = hot_days[hot_days.year==2023]["jours_30"].values
    hot_2023   = int(hot_v[0]) if len(hot_v) else 0
    hot_ref    = float(hot_days[(hot_days.year>=1961)&(hot_days.year<=1990)]["jours_30"].mean())

    # Temperature anomaly chart
    fig_t = go.Figure()
    pos = annual[annual["anomalie"] > 0]
    neg = annual[annual["anomalie"] <= 0]
    fig_t.add_bar(x=pos["year"].tolist(), y=pos["anomalie"].round(3).tolist(),
                  marker_color=RED, marker_opacity=0.55, name="Anomalie positive")
    fig_t.add_bar(x=neg["year"].tolist(), y=neg["anomalie"].round(3).tolist(),
                  marker_color=BLUE, marker_opacity=0.55, name="Anomalie négative")
    roll = annual["anomalie"].rolling(10, center=True, min_periods=1).mean()
    fig_t.add_scatter(x=annual["year"].tolist(), y=roll.round(3).tolist(),
                      mode="lines", line=dict(color="#f8fafc", width=2.5),
                      name="Moyenne 10 ans", opacity=0.9)
    fig_t.add_hline(y=0, line_color=TEXT_DIM, line_width=1)
    apply(fig_t, h=310, showlegend=True,
          legend=dict(orientation="h", y=1.12, font=dict(color=TEXT_SUB)),
          margin=dict(t=10, b=30, l=40, r=10))

    # CO2 gauge
    fig_g = go.Figure(go.Indicator(
        mode="gauge+number",
        value=co2_last,
        number={"suffix":" ppm","font":{"size":36,"color":TEXT,"family":"Inter"}},
        gauge={
            "axis": {"range":[280,600],"tickwidth":1,"tickcolor":TEXT_DIM,"tickfont":{"color":TEXT_DIM}},
            "bar":  {"color":AMBER,"thickness":0.25},
            "bgcolor": BG_CARD2, "bordercolor": BORDER,
            "steps": [
                {"range":[280,350],"color":"rgba(59,130,246,0.15)"},
                {"range":[350,450],"color":"rgba(245,158,11,0.15)"},
                {"range":[450,600],"color":"rgba(239,68,68,0.15)"},
            ],
            "threshold": {"line":{"color":RED,"width":2.5},"value":450},
        }
    ))
    apply(fig_g, h=220, margin=dict(t=20,b=10,l=30,r=30))

    # Projections summary
    proj = project_scenario(model, ref_t)
    proj_data = {}
    for name, color in SCENARIO_COLORS.items():
        df_s = proj[name]
        vals = {str(yr): round(float(df_s[df_s.year==yr]["anomalie"].values[0]),2)
                for yr in [2030,2050,2100]}
        proj_data[name] = {"vals": vals, "color": color}

    return jsonify({
        "kpis": {
            "anom_2023":     round(anom_2023, 2),
            "co2_last":      round(co2_last, 0),
            "fires_mha":     round(fires_surf/1e6, 1),
            "emp_last":      round(emp_last, 1),
            "hot_2023":      hot_2023,
            "hot_ref":       round(hot_ref, 0),
        },
        "co2_delta":  round(co2_last - 280, 0),
        "charts": {
            "temp":      fig_json(fig_t),
            "co2_gauge": fig_json(fig_g),
        },
        "projections": proj_data,
    })

# ── API: Températures & Projections ──────────────────────────────────────────
@app.route("/api/temperatures")
def api_temperatures():
    target_year = int(request.args.get("year", 2060))
    annual, _   = load_temperatures()
    model, ref_t, model_metrics, best_name = build_model()
    proj = project_scenario(model, ref_t, target_year)

    # Projection chart
    last_year = int(annual["year"].iloc[-1])
    last_anom = float(annual["anomalie"].iloc[-1])

    fig = go.Figure()
    fig.add_scatter(x=annual["year"].tolist(), y=annual["anomalie"].round(3).tolist(),
                    mode="lines", line=dict(color=TEXT_DIM, width=1),
                    name="Historique (brut)", opacity=0.5)
    roll = annual["anomalie"].rolling(5, center=True, min_periods=1).mean()
    fig.add_scatter(x=annual["year"].tolist(), y=roll.round(3).tolist(),
                    mode="lines", line=dict(color="#f8fafc", width=2),
                    name="Historique (moy. 5 ans)")
    for name, color in SCENARIO_COLORS.items():
        df_s = proj[name]
        # Prepend last historical point so projection connects to history
        x_proj = [last_year] + df_s["year"].tolist()
        y_proj = [round(last_anom, 3)] + df_s["anomalie"].round(3).tolist()
        fig.add_scatter(x=x_proj, y=y_proj,
                        mode="lines", line=dict(color=color, width=2.5), name=name)
        val = float(df_s[df_s.year==target_year]["anomalie"].values[0])
        fig.add_scatter(x=[target_year], y=[round(val,2)], mode="markers+text",
                        marker=dict(size=9, color=color),
                        text=[f" {val:+.1f}°C"], textposition="middle right",
                        textfont=dict(size=11, color=color), showlegend=False)
    fig.add_vline(x=last_year, line_dash="dot", line_color=TEXT_DIM, line_width=1)
    fig.add_hline(y=0, line_color=TEXT_DIM, line_width=0.7)
    fig.add_vrect(x0=1961, x1=1990, fillcolor="rgba(59,130,246,0.06)", line_width=0,
                  annotation_text="Référence", annotation_position="top left",
                  annotation_font=dict(color=TEXT_DIM, size=10))
    apply(fig, h=420, legend=dict(orientation="h", y=1.08),
          margin=dict(t=20,b=40,l=50,r=100),
          yaxis_title="Anomalie (°C vs 1961–1990)", xaxis_title="Année")

    # Model comparison
    df_met = pd.DataFrame(model_metrics).T.reset_index()
    df_met.columns = ["Modèle","RMSE","MAE","MAPE (%)"]
    fig_m = go.Figure()
    for metric, col_m in [("RMSE", GREEN), ("MAE", AMBER)]:
        fig_m.add_bar(name=metric, x=df_met["Modèle"].tolist(),
                      y=df_met[metric].tolist(),
                      marker_color=col_m, opacity=0.75 if metric=="RMSE" else 0.55)
    apply(fig_m, h=280, barmode="group",
          legend=dict(orientation="h", y=1.1),
          yaxis_title="Erreur (°C)",
          margin=dict(t=10,b=80,l=50,r=20))

    # TX vs TN
    ann = annual.copy()
    ref_tx = ann[(ann.year>=1961)&(ann.year<=1990)]["tx"].mean()
    ref_tn = ann[(ann.year>=1961)&(ann.year<=1990)]["tn"].mean()
    ann["anom_tx"] = (ann["tx"] - ref_tx).rolling(5, center=True, min_periods=1).mean()
    ann["anom_tn"] = (ann["tn"] - ref_tn).rolling(5, center=True, min_periods=1).mean()
    fig2 = go.Figure()
    fig2.add_scatter(x=ann["year"].tolist(), y=ann["anom_tx"].round(3).tolist(),
                     name="Tmax — jours", line=dict(color=RED, width=2))
    fig2.add_scatter(x=ann["year"].tolist(), y=ann["anom_tn"].round(3).tolist(),
                     name="Tmin — nuits", line=dict(color=BLUE, width=2))
    fig2.add_hline(y=0, line_color=TEXT_DIM, line_width=0.7)
    apply(fig2, h=280, legend=dict(orientation="h", y=1.12),
          yaxis_title="°C (moy. mobile 5 ans)", xaxis_title="Année",
          margin=dict(t=10,b=40,l=50,r=20))

    # Hot days
    hot_days, hot_ref = load_hot_days()
    fig3 = go.Figure()
    fig3.add_bar(x=hot_days["year"].tolist(), y=hot_days["jours_30"].tolist(),
                 marker_color=[RED if v > hot_ref else TEXT_DIM for v in hot_days["jours_30"]],
                 marker_opacity=0.7, name="Jours TX≥30°C")
    roll_h = hot_days["jours_30"].rolling(10, center=True).mean()
    fig3.add_scatter(x=hot_days["year"].tolist(), y=roll_h.round(3).tolist(),
                     mode="lines", line=dict(color="#f8fafc", width=2.5), name="Tendance 10 ans")
    fig3.add_hline(y=float(hot_ref), line_dash="dot", line_color=BLUE, line_width=1.5,
                   annotation_text=f" Réf. 1961–1990 : {hot_ref:.0f} j/an",
                   annotation_font=dict(size=9, color=BLUE))
    apply(fig3, h=280, legend=dict(orientation="h", y=1.12),
          yaxis_title="Nombre de jours", xaxis_title="Année",
          margin=dict(t=10,b=40,l=50,r=20))

    # Projection table
    rows = []
    for name in SCENARIO_COLORS:
        df_s = proj[name]
        row = {"Scénario": name}
        for yr in [2030, 2050, 2075, 2100]:
            if yr <= target_year:
                v = float(df_s[df_s.year==yr]["anomalie"].values[0])
                row[str(yr)] = f"{v:+.2f}°C"
        rows.append(row)

    return jsonify({
        "charts": {
            "projection": fig_json(fig),
            "models":     fig_json(fig_m),
            "tx_tn":      fig_json(fig2),
            "hot_days":   fig_json(fig3),
        },
        "metrics":      model_metrics,
        "best_model":   best_name,
        "table":        rows,
        "target_year":  target_year,
    })

# ── API: Feux de forêt ────────────────────────────────────────────────────────
@app.route("/api/fires")
def api_fires():
    start  = int(request.args.get("start", 2014))
    end    = int(request.args.get("end",   2024))
    fires  = load_fires()
    geojson = get_dept_geojson()
    df_f   = fires[(fires.annee >= start) & (fires.annee <= end)]

    top_dept = str(df_f.groupby("departement")["surface_totale_ha"].sum().idxmax())
    top_surf = float(df_f.groupby("departement")["surface_totale_ha"].sum().max())
    forest_pct = float(df_f['surface_foret_ha'].sum() / df_f['surface_totale_ha'].sum() * 100)

    # Choropleth map
    dept_agg = df_f.groupby("departement").agg(
        surface=("surface_totale_ha","sum"),
        nb=("surface_totale_ha","count"),
    ).reset_index()
    map_chart = None
    if geojson:
        fig_map = px.choropleth(
            dept_agg, geojson=geojson,
            locations="departement", featureidkey="properties.code",
            color="surface",
            color_continuous_scale=[[0,"#1a0a00"],[0.3,"#7c2d12"],[0.6,"#ea580c"],[1,"#fbbf24"]],
            hover_data={"nb":True,"surface":":.0f"},
            labels={"surface":"Surface (ha)","nb":"Incendies"},
        )
        fig_map.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)")
        fig_map.update_layout(
            height=380, paper_bgcolor="rgba(0,0,0,0)", geo_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=0,b=0,l=0,r=0),
            coloraxis_colorbar=dict(title="ha", thickness=10,
                                    tickfont=dict(color=TEXT_SUB),
                                    titlefont=dict(color=TEXT_SUB)))
        map_chart = fig_json(fig_map)

    # Time series
    by_year = fires.groupby("annee").agg(
        nb=("surface_totale_ha","count"),
        surface=("surface_totale_ha","sum"),
    ).reset_index()
    fig_ts = make_subplots(specs=[[{"secondary_y":True}]])
    fig_ts.add_bar(x=by_year["annee"].tolist(), y=by_year["surface"].round(0).tolist(),
                   name="Surface (ha)", marker_color=RED, marker_opacity=0.6)
    fig_ts.add_scatter(x=by_year["annee"].tolist(), y=by_year["nb"].tolist(),
                       name="Nb incendies", mode="lines+markers",
                       line=dict(color=AMBER, width=2), marker=dict(size=5), secondary_y=True)
    fig_ts.update_layout(**{**PLOT, "height":380,
                             "legend":dict(orientation="h",y=1.1,bgcolor="rgba(0,0,0,0)"),
                             "margin":dict(t=10,b=40,l=50,r=50)})
    fig_ts.update_yaxes(title_text="Surface (ha)", secondary_y=False,
                        gridcolor="rgba(255,255,255,0.04)", title_font=dict(color=TEXT_SUB))
    fig_ts.update_yaxes(title_text="Nb incendies", secondary_y=True,
                        gridcolor="rgba(0,0,0,0)", title_font=dict(color=TEXT_SUB))

    # Seasonality
    by_month = (fires.dropna(subset=["mois"])
                .groupby("mois")["surface_totale_ha"].sum().reset_index())
    mois_labels = ["Jan","Fév","Mar","Avr","Mai","Jun","Jul","Aoû","Sep","Oct","Nov","Déc"]
    by_month["label"] = by_month["mois"].apply(lambda x: mois_labels[int(x)-1])
    fig_s = go.Figure(go.Bar(
        x=by_month["label"].tolist(), y=by_month["surface_totale_ha"].round(0).tolist(),
        marker_color=[RED if m in [7,8,9] else AMBER if m in [6,10] else TEXT_DIM
                      for m in by_month["mois"]],
        marker_opacity=0.8,
    ))
    apply(fig_s, h=240, yaxis_title="Surface totale (ha)", margin=dict(t=10,b=30,l=50,r=10))

    return jsonify({
        "kpis": {
            "nb_incendies":   int(len(df_f)),
            "surface_ha":     round(float(df_f['surface_totale_ha'].sum()), 0),
            "surface_foret":  round(float(df_f['surface_foret_ha'].sum()), 0),
            "forest_pct":     round(forest_pct, 0),
            "top_dept":       top_dept,
            "top_surf":       round(top_surf, 0),
        },
        "charts": {
            "map":        map_chart,
            "timeseries": fig_json(fig_ts),
            "seasonality":fig_json(fig_s),
        },
    })

# ── API: Émissions & CO₂ ─────────────────────────────────────────────────────
@app.route("/api/emissions")
def api_emissions():
    co2 = load_co2()
    emi = load_emissions()
    emp = load_empreinte()
    ges = load_ges_secteur()
    substance = request.args.get("substance", "Dioxyde de carbone")

    substances = sorted(ges["LIBELLE_SUBSTANCE"].dropna().unique().tolist())
    if substance not in substances:
        substance = substances[0]

    # CO2 concentration
    fig1 = go.Figure()
    fig1.add_scatter(x=co2["year"].tolist(), y=co2["co2_ppm"].round(2).tolist(),
                     fill="tozeroy", fillcolor="rgba(245,158,11,0.07)",
                     line=dict(color=AMBER, width=2), name="CO₂ ppm")
    for y_val, label, color in [(280,"Préindustriel",TEXT_DIM),(350,"Seuil sécurité",BLUE),(420,"Actuel ~",RED)]:
        fig1.add_hline(y=y_val, line_dash="dot", line_color=color, line_width=1.2,
                       annotation_text=f" {label} · {y_val} ppm",
                       annotation_font=dict(size=9, color=color))
    apply(fig1, h=300, yaxis_title="ppm", xaxis_title="Année",
          margin=dict(t=10,b=40,l=50,r=20))

    # Emissions production vs importées
    fig2 = go.Figure()
    fig2.add_scatter(x=emi["annee"].tolist(),
                     y=emi["emissions_production_interieure_MtCO2e"].round(2).tolist(),
                     name="Intérieures", fill="tozeroy",
                     fillcolor="rgba(59,130,246,0.1)", line=dict(color=BLUE, width=2))
    fig2.add_scatter(x=emi["annee"].tolist(),
                     y=emi["emissions_importees_MtCO2e"].round(2).tolist(),
                     name="Importées", fill="tozeroy",
                     fillcolor="rgba(239,68,68,0.1)", line=dict(color=RED, width=2))
    apply(fig2, h=300, yaxis_title="MtCO₂e", xaxis_title="Année",
          legend=dict(orientation="h", y=1.1, font=dict(color=TEXT_SUB)),
          margin=dict(t=10,b=40,l=50,r=20))

    # Empreinte carbone
    fig3 = go.Figure()
    fig3.add_scatter(x=emp["annee"].tolist(),
                     y=emp["empreinte_carbone_tCO2e_par_habitant"].round(2).tolist(),
                     mode="lines+markers", marker=dict(size=4, color=BLUE),
                     line=dict(color=BLUE, width=2.5), fill="tozeroy",
                     fillcolor="rgba(59,130,246,0.07)")
    fig3.add_hline(y=2, line_dash="dash", line_color=GREEN, line_width=1.5,
                   annotation_text=" Objectif 2050 : 2 tCO₂e",
                   annotation_font=dict(size=9, color=GREEN))
    apply(fig3, h=300, yaxis_title="tCO₂e / habitant", xaxis_title="Année",
          margin=dict(t=10,b=40,l=50,r=20))

    # GES by sector
    df_sec = ges[ges["LIBELLE_SUBSTANCE"]==substance]
    top_sec = df_sec.groupby("LIBELLE_NACE_ET_MENAGES")["MASSE"].sum().nlargest(8).index
    df_sec  = df_sec[df_sec["LIBELLE_NACE_ET_MENAGES"].isin(top_sec)]
    df_piv  = df_sec.groupby(["ANNEE","LIBELLE_NACE_ET_MENAGES"])["MASSE"].sum().reset_index()
    PALETTE = [BLUE,"#7c3aed",AMBER,RED,GREEN,"#06b6d4","#ec4899","#84cc16"]
    fig4 = px.bar(df_piv, x="ANNEE", y="MASSE", color="LIBELLE_NACE_ET_MENAGES",
                  color_discrete_sequence=PALETTE,
                  labels={"MASSE":"Masse (kg)","ANNEE":"Année","LIBELLE_NACE_ET_MENAGES":"Secteur"})
    apply(fig4, h=380,
          legend=dict(orientation="h", y=-0.4, font=dict(size=9, color=TEXT_SUB)),
          yaxis_title="kg", xaxis_title="Année",
          margin=dict(t=10,b=200,l=60,r=20))

    return jsonify({
        "charts": {
            "co2":       fig_json(fig1),
            "emissions": fig_json(fig2),
            "empreinte": fig_json(fig3),
            "sectors":   fig_json(fig4),
        },
        "substances":         substances,
        "current_substance":  substance,
    })

# ── API: Précipitations ───────────────────────────────────────────────────────
@app.route("/api/precipitations")
def api_precipitations():
    precip, ref_p   = load_precipitation()
    dept_precip     = load_precip_by_dept()
    geojson         = get_dept_geojson()
    dept            = request.args.get("dept", "all")

    last    = precip.iloc[-1]
    dry     = int(len(precip[precip["anomalie"] < -2]))
    dept_names = {}

    # Choropleth map
    dept_avg = (dept_precip.groupby("dept")
                .agg(anomalie=("anomalie","mean"), precip_mm=("precip_mm","mean"))
                .reset_index())
    map_chart = None
    if geojson:
        dept_names = {f["properties"]["code"]: f["properties"]["nom"]
                      for f in geojson["features"]}
        dept_avg["nom"] = dept_avg["dept"].map(dept_names).fillna("")
        fig_map = px.choropleth(
            dept_avg, geojson=geojson,
            locations="dept", featureidkey="properties.code",
            color="anomalie",
            color_continuous_scale=[[0,"#7c2d12"],[0.35,"#991b1b"],
                                    [0.5,"#111827"],[0.65,"#1e3a5f"],[1,"#3b82f6"]],
            range_color=[-8,8],
            hover_name="nom",
            hover_data={"dept":True,"precip_mm":":.1f","anomalie":":.1f","nom":False},
            labels={"anomalie":"Anomalie (mm/mois)","precip_mm":"Préc. moy. (mm/mois)","dept":"Dép."},
        )
        fig_map.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)")
        fig_map.update_layout(
            height=440, paper_bgcolor="rgba(0,0,0,0)", geo_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=0,b=0,l=0,r=0),
            coloraxis_colorbar=dict(
                title="Anom.<br>(mm/mois)", thickness=10,
                tickfont=dict(color=TEXT_SUB), titlefont=dict(color=TEXT_SUB)),
        )
        map_chart = fig_json(fig_map)

    # Time series
    if dept != "all" and dept in dept_precip["dept"].values:
        df_ts    = dept_precip[dept_precip["dept"]==dept].copy()
        nom_dept = dept_names.get(dept, dept)
        title_ts = f"Dép. {dept} — {nom_dept}"
    else:
        df_ts    = precip.copy()
        title_ts = "France entière"

    fig_ts = go.Figure()
    fig_ts.add_bar(x=df_ts["year"].tolist(), y=df_ts["anomalie"].round(3).tolist(),
                   marker_color=[BLUE if v>=0 else RED for v in df_ts["anomalie"]],
                   marker_opacity=0.6, name="Anomalie")
    roll_ts = df_ts["anomalie"].rolling(10, center=True).mean()
    fig_ts.add_scatter(x=df_ts["year"].tolist(), y=roll_ts.round(3).tolist(),
                       mode="lines", line=dict(color="#f8fafc", width=2.5), name="Tendance 10 ans")
    fig_ts.add_hline(y=0, line_color=TEXT_DIM, line_width=1)
    apply(fig_ts, h=440,
          legend=dict(orientation="h", y=1.06, font=dict(color=TEXT_SUB)),
          yaxis_title="Anomalie (mm/mois)", xaxis_title="Année",
          margin=dict(t=10,b=40,l=50,r=20))

    # Décennal
    pr = precip.copy()
    pr["decade"] = (pr["year"] // 10) * 10
    by_dec = pr.groupby("decade")["precip_mm"].mean().reset_index()
    by_dec["delta"] = by_dec["precip_mm"] - ref_p
    fig2 = go.Figure(go.Bar(
        x=(by_dec["decade"].astype(str) + "s").tolist(),
        y=by_dec["delta"].round(2).tolist(),
        marker_color=[BLUE if v>=0 else RED for v in by_dec["delta"]],
        marker_opacity=0.75,
        text=[f"{v:+.1f}" for v in by_dec["delta"]],
        textposition="outside",
        textfont=dict(color=TEXT_SUB, size=11),
    ))
    fig2.add_hline(y=0, line_color=TEXT_DIM, line_width=1)
    apply(fig2, h=280, yaxis_title="Écart vs réf. (mm/mois)",
          margin=dict(t=30,b=40,l=50,r=20))

    depts_list = sorted(dept_precip["dept"].unique().tolist())
    dept_labels = {d: f"{d} – {dept_names.get(d,'')}" for d in depts_list}

    return jsonify({
        "kpis": {
            "ref_p":       round(float(ref_p), 1),
            "last_year":   int(last["year"]),
            "last_precip": round(float(last["precip_mm"]), 1),
            "last_anom":   round(float(last["anomalie"]), 1),
            "dry_years":   dry,
        },
        "charts": {
            "map":       map_chart,
            "timeseries":fig_json(fig_ts),
            "decennial": fig_json(fig2),
        },
        "title_ts":     title_ts,
        "depts":        depts_list,
        "dept_labels":  dept_labels,
        "selected_dept":dept,
    })

# ── API: Préconisations ───────────────────────────────────────────────────────
@app.route("/api/preconisations")
def api_preconisations():
    scenario = request.args.get("scenario", "Intermédiaire (+2.7°C)")
    if scenario not in SCENARIO_COLORS:
        scenario = "Intermédiaire (+2.7°C)"
    model, ref_t, _, _ = build_model()
    proj = project_scenario(model, ref_t)
    df_s = proj[scenario]
    vals = {str(yr): round(float(df_s[df_s.year==yr]["anomalie"].values[0]),2) for yr in [2030,2050,2100]}
    return jsonify({
        "vals":      vals,
        "color":     SCENARIO_COLORS[scenario],
        "scenario":  scenario,
        "scenarios": list(SCENARIO_COLORS.keys()),
    })

# ── API: Chatbot Mistral ──────────────────────────────────────────────────────
def build_climate_context():
    """Construit un résumé des données pour le system prompt."""
    try:
        annual, ref      = load_temperatures()
        co2_df           = load_co2()
        fires_df         = load_fires()
        empreinte        = load_empreinte()
        model, ref_t, metrics, best = build_model()
        hot_days, _      = load_hot_days()
        precip, ref_p    = load_precipitation()

        anom_2023  = float(annual[annual.year==2023]["anomalie"].values[0])
        co2_last   = float(co2_df["co2_ppm"].iloc[-1])
        fires_surf = float(fires_df["surface_totale_ha"].sum())
        emp_last   = float(empreinte["empreinte_carbone_tCO2e_par_habitant"].iloc[-1])
        hot_2023_v = hot_days[hot_days.year==2023]["jours_30"].values
        hot_2023   = int(hot_2023_v[0]) if len(hot_2023_v) else 0
        last_precip = float(precip.iloc[-1]["anomalie"])

        proj = project_scenario(model, ref_t)
        proj_vals = {}
        for name in SCENARIO_COLORS:
            df_s = proj[name]
            proj_vals[name] = {yr: round(float(df_s[df_s.year==yr]["anomalie"].values[0]),2) for yr in [2030,2050,2100]}

        return f"""Tu es un assistant expert en climatologie qui répond aux questions sur ce tableau de bord climatique de la France.

DONNÉES DU TABLEAU DE BORD :

Températures (Météo-France, stations homogénéisées) :
- Référence climatologique : {ref:.2f}°C (moyenne 1961–1990)
- Anomalie 2023 : {anom_2023:+.2f}°C vs 1961–1990
- Tendance : hausse continue depuis les années 1980, accélération post-2000

CO₂ atmosphérique (NOAA, Mauna Loa) :
- Niveau actuel : {co2_last:.0f} ppm
- Niveau préindustriel : 280 ppm
- Hausse : +{co2_last-280:.0f} ppm depuis 1850

Jours de chaleur extrême (Paris-Montsouris) :
- Jours TX ≥ 30°C en 2023 : {hot_2023} jours
- Référence 1961–1990 : ~8 jours/an

Incendies de forêt (BDIFF, 2003–2024) :
- Surface totale brûlée : {fires_surf/1e6:.1f} millions d'hectares
- Année record : 2022

Empreinte carbone France :
- Actuelle : {emp_last} tCO₂e/habitant/an
- Objectif SNBC 2050 : 2 tCO₂e/habitant/an

Précipitations :
- Anomalie dernière année : {last_precip:+.1f} mm/mois vs référence 1961–1990

Projections IPCC AR6 (modèle log-linéaire CO₂/température, meilleur modèle : {best}) :
- Optimiste (SSP1-1.9) : {proj_vals["Optimiste (+1.4°C)"][2050]:+.1f}°C en 2050, {proj_vals["Optimiste (+1.4°C)"][2100]:+.1f}°C en 2100
- Intermédiaire (SSP2-4.5) : {proj_vals["Intermédiaire (+2.7°C)"][2050]:+.1f}°C en 2050, {proj_vals["Intermédiaire (+2.7°C)"][2100]:+.1f}°C en 2100
- Pessimiste (SSP5-8.5) : {proj_vals["Pessimiste (+4.4°C)"][2050]:+.1f}°C en 2050, {proj_vals["Pessimiste (+4.4°C)"][2100]:+.1f}°C en 2100

INSTRUCTIONS :
- Réponds en français, de manière concise et factuelle
- Appuie-toi sur les données ci-dessus quand elles sont pertinentes
- Si une donnée n'est pas dans le dashboard, dis-le clairement
- Reste accessible (pas trop technique) mais rigoureux"""
    except Exception:
        return "Tu es un assistant expert en climatologie pour la France. Réponds en français de manière concise et factuelle."

@app.route("/api/chat", methods=["POST"])
def api_chat():
    api_key = os.environ.get("MISTRAL_API_KEY", "")
    if not api_key:
        return jsonify({"error": "MISTRAL_API_KEY non définie"}), 500

    body = request.get_json()
    messages = body.get("messages", [])
    if not messages:
        return jsonify({"error": "messages vide"}), 400

    system_prompt = build_climate_context()

    payload = {
        "model": "mistral-small-latest",
        "messages": [{"role": "system", "content": system_prompt}] + messages,
        "max_tokens": 600,
        "temperature": 0.4,
    }

    resp = http_req.post(
        "https://api.mistral.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    if not resp.ok:
        return jsonify({"error": f"Mistral {resp.status_code}: {resp.text}"}), 502

    content = resp.json()["choices"][0]["message"]["content"]
    return jsonify({"reply": content})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(debug=True, port=port, host="0.0.0.0")
