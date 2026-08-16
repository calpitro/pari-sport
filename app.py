import math
import numpy as np
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="QuantBet Pro - Multi-Championnats",
    page_icon="⚽",
    layout="wide",
)

st.title("⚽ QuantBet Pro - Quantitative Engine")
st.caption(
    "Multi-Championnats | Cotes Auto (Winamax/EU) | Modélisation Dixon-Coles /"
    " Poisson | Kelly Criterion"
)
st.markdown("---")


# --- POISSON NATIF ---
def poisson_pmf(k, lamb):
  return (lamb**k * math.exp(-lamb)) / math.factorial(k)


# ==========================================
# SIDEBAR
# ==========================================
st.sidebar.header("🔑 Clé API & Bankroll")
ODDS_API_KEY = st.sidebar.text_input("Clé The Odds API :", type="password")

bankroll = st.sidebar.number_input(
    "Bankroll Totale (€) :", min_value=10.0, value=1000.0, step=50.0
)
kelly_fraction = st.sidebar.select_slider(
    "Gestion du risque (Kelly) :",
    options=[0.1, 0.25, 0.5, 1.0],
    value=0.25,
    format_func=lambda x: {
        0.1: "1/10 Kelly",
        0.25: "1/4 Kelly (Recommandé)",
        0.5: "1/2 Kelly",
        1.0: "Full Kelly",
    }[x],
)
min_ev_threshold = (
    st.sidebar.slider("Seuil EV minimum (% Value) :", 0.0, 15.0, 3.0, 0.5) / 100.0
)

st.sidebar.markdown("---")
st.sidebar.header("🏆 Championnat")
league_choice = st.sidebar.selectbox(
    "Sélectionne la compétition :",
    [
        "🇫🇷 France - Ligue 1",
        "🇫🇷 France - Ligue 2",
        "🇫🇷 France - Trophée des Champions",
        "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Angleterre - Premier League",
        "🇪🇸 Espagne - La Liga",
        "🇮🇹 Italie - Serie A",
        "🇩🇪 Allemagne - Bundesliga",
        "🇪🇺 Europe - Ligue des Champions",
        "🇪🇺 Europe - Ligue Europa",
    ],
)

league_map_odds = {
    "🇫🇷 France - Ligue 1": "soccer_france_ligue_one",
    "🇫🇷 France - Ligue 2": "soccer_france_ligue_two",
    "🇫🇷 France - Trophée des Champions": "soccer_france_trophee_des_champions",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Angleterre - Premier League": "soccer_epl",
    "🇪🇸 Espagne - La Liga": "soccer_spain_la_liga",
    "🇮🇹 Italie - Serie A": "soccer_italy_serie_a",
    "🇩🇪 Allemagne - Bundesliga": "soccer_germany_bundesliga",
    "🇪🇺 Europe - Ligue des Champions": "soccer_uefa_champs_league",
    "🇪🇺 Europe - Ligue Europa": "soccer_uefa_europa_league",
}

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Ajustements Modèle")
home_advantage = st.sidebar.slider(
    "Bonus xG Domicile :", 1.0, 1.30, 1.15, 0.01
)
dixon_coles_corr = st.sidebar.slider(
    "Correction Dixon-Coles :", -0.20, 0.0, -0.05, 0.01
)

if not ODDS_API_KEY:
  st.warning("👈 Insère ta clé API dans le menu à gauche.")
  st.stop()


# ==========================================
# FETCH DATA SANS FILTRE TROP STRICT
# ==========================================
@st.cache_data(ttl=1800)
def fetch_odds_data(s_key, api_k):
  url = f"https://api.the-odds-api.com/v4/sports/{s_key}/odds/?apiKey={api_k}&regions=eu&markets=h2h,totals&oddsFormat=decimal"
  try:
    res = requests.get(url)
    if res.status_code == 200:
      return res.json()
  except Exception:
    pass
  return []


def dixon_coles_adjustment(h, a, lambda_h, lambda_a, rho):
  if h == 0 and a == 0:
    return 1.0 - (lambda_h * lambda_a * rho)
  elif h == 0 and a == 1:
    return 1.0 + (lambda_h * rho)
  elif h == 1 and a == 0:
    return 1.0 + (lambda_a * rho)
  elif h == 1 and a == 1:
    return 1.0 - rho
  return 1.0


def build_bivariate_poisson_matrix(xg_home, xg_away, max_goals=7, rho=-0.05):
  matrix = np.zeros((max_goals, max_goals))
  for h in range(max_goals):
    for a in range(max_goals):
      p_h = poisson_pmf(h, xg_home)
      p_a = poisson_pmf(a, xg_away)
      adj = dixon_coles_adjustment(h, a, xg_home, xg_away, rho)
      matrix[h, a] = max(0.0, p_h * p_a * adj)
  matrix /= np.sum(matrix)
  return matrix


def calculate_kelly_stake(prob, odds, bankroll, fraction):
  b = odds - 1.0
  p = prob
  q = 1.0 - p
  f = (b * p - q) / b
  if f <= 0:
    return 0.0
  return round(f * fraction * bankroll, 2)


# ==========================================
# TRAITEMENT DES MATCHS
# ==========================================
matches = fetch_odds_data(league_map_odds[league_choice], ODDS_API_KEY)

if not matches:
  st.error(
      f"Aucun match disponible actuellement pour {league_choice}. Réessaye"
      " avec un autre championnat (ex: Premier League / Ligue des Champions) !"
  )
else:
  st.success(f"✅ {len(matches)} match(s) chargé(s) pour {league_choice} !")

  for idx, match in enumerate(matches):
    home_team = match["home_team"]
    away_team = match["away_team"]

    bookmakers = match.get("bookmakers", [])
    if not bookmakers:
      continue

    # Priorité à Winamax, sinon premier bookmaker dispo
    selected_bm = next(
        (b for b in bookmakers if b["key"].lower() == "winamax"), bookmakers[0]
    )
    bm_name = selected_bm.get("title", "Bookmaker")

    markets = selected_bm.get("markets", [])
    h2h_market = next((m for m in markets if m["key"] == "h2h"), None)
    totals_market = next((m for m in markets if m["key"] == "totals"), None)

    if not h2h_market:
      continue

    cote_1 = next(
        (
            item["price"]
            for item in h2h_market["outcomes"]
            if item["name"] == home_team
        ),
        1.0,
    )
    cote_2 = next(
        (
            item["price"]
            for item in h2h_market["outcomes"]
            if item["name"] == away_team
        ),
        1.0,
    )
    cote_N = next(
        (
            item["price"]
            for item in h2h_market["outcomes"]
            if item["name"] == "Draw"
        ),
        1.0,
    )

    cote_o25, cote_u25 = 1.85, 1.85
    if totals_market:
      for outcome in totals_market["outcomes"]:
        if outcome.get("point") == 2.5:
          if outcome["name"] == "Over":
            cote_o25 = outcome["price"]
          elif outcome["name"] == "Under":
            cote_u25 = outcome["price"]

    with st.expander(
        f"⚽ {home_team} vs {away_team} — (Source cotes : {bm_name})",
        expanded=True,
    ):
      c_att, c_def = st.columns(2)

      with c_att:
        att_h = st.slider(
            f"Attaque {home_team} :",
            0.5,
            3.0,
            1.6,
            0.05,
            key=f"att_h_{idx}",
        )
        def_h = st.slider(
            f"Faiblesse Défense {home_team} :",
            0.5,
            2.5,
            0.9,
            0.05,
            key=f"def_h_{idx}",
        )

      with c_def:
        att_a = st.slider(
            f"Attaque {away_team} :",
            0.5,
            3.0,
            1.4,
            0.05,
            key=f"att_a_{idx}",
        )
        def_a = st.slider(
            f"Faiblesse Défense {away_team} :",
            0.5,
            2.5,
            1.1,
            0.05,
            key=f"def_a_{idx}",
        )

      xg_home = round(att_h * def_a * home_advantage, 2)
      xg_away = round(att_a * def_h, 2)

      matrix = build_bivariate_poisson_matrix(
          xg_home, xg_away, max_goals=7, rho=dixon_coles_corr
      )

      prob_1 = float(np.sum(np.tril(matrix, -1)))
      prob_N = float(np.sum(np.diag(matrix)))
      prob_2 = float(np.sum(np.triu(matrix, 1)))

      prob_over25 = float(
          1.0
          - np.sum([
              matrix[h, a] for h in range(3) for a in range(3) if h + a <= 2
          ])
      )
      prob_under25 = 1.0 - prob_over25

      col_left, col_right = st.columns([1.3, 1])

      with col_left:
        st.markdown(
            f"📊 **xG Attendu :** `{xg_home}` ({home_team}) - `{xg_away}`"
            f" ({away_team})"
        )

        data_markets = [
            {
                "Marché": f"Victoire {home_team} (1)",
                "Probabilité": prob_1,
                "Cote": cote_1,
            },
            {"Marché": "Match Nul (N)", "Probabilité": prob_N, "Cote": cote_N},
            {
                "Marché": f"Victoire {away_team} (2)",
                "Probabilité": prob_2,
                "Cote": cote_2,
            },
            {
                "Marché": "Over 2.5 Buts",
                "Probabilité": prob_over25,
                "Cote": cote_o25,
            },
            {
                "Marché": "Under 2.5 Buts",
                "Probabilité": prob_under25,
                "Cote": cote_u25,
            },
        ]

        df_analysis = pd.DataFrame(data_markets)
        df_analysis["Cote Équitable"] = df_analysis["Probabilité"].apply(
            lambda x: round(1 / x, 2) if x > 0 else 99
        )
        df_analysis["Expected Value (EV)"] = (
            df_analysis["Probabilité"] * df_analysis["Cote"]
        ) - 1.0
        df_analysis["Mise (€)"] = df_analysis.apply(
            lambda r: calculate_kelly_stake(
                r["Probabilité"], r["Cote"], bankroll, kelly_fraction
            ),
            axis=1,
        )

        df_disp = df_analysis.copy()
        df_disp["Probabilité"] = df_disp["Probabilité"].apply(
            lambda x: f"{round(x*100, 1)}%"
        )
        df_disp["Expected Value (EV)"] = df_disp["Expected Value (EV)"].apply(
            lambda x: f"{'+' if x>0 else ''}{round(x*100, 1)}%"
        )
        df_disp["Mise (€)"] = df_disp["Mise (€)"].apply(
            lambda x: f"{x} €" if x > 0 else "-"
        )

        st.dataframe(
            df_disp[
                [
                    "Marché",
                    "Probabilité",
                    "Cote Équitable",
                    "Cote",
                    "Expected Value (EV)",
                    "Mise (€)",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

      with col_right:
        st.markdown(f"**🎯 Value Bets ({bm_name})**")
        val_bets = df_analysis[
            df_analysis["Expected Value (EV)"] >= min_ev_threshold
        ]

        if len(val_bets) == 0:
          st.info("Aucun paris à valeur détecté.")
        else:
          for _, row in val_bets.iterrows():
            ev_pct = round(row["Expected Value (EV)"] * 100, 1)
            st.success(
                f"🔥 **{row['Marché']}** @ **{round(row['Cote'], 2)}**\n\n→ Value"
                f" : **+{ev_pct}%** | Mise Kelly : **{row['Mise (€)']} €**"
            )
