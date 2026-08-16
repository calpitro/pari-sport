import math
import numpy as np
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="QuantBet Pro - Full Auto",
    page_icon="⚽",
    layout="wide",
)

st.title("⚽ QuantBet Pro - Full Auto Betting Engine")
st.caption(
    "Calcul Implicite Auto xG | Multi-Championnats | Cotes Winamax/EU |"
    " Dixon-Coles & Kelly"
)
st.markdown("---")


# --- MATH NATIF ---
def poisson_pmf(k, lamb):
  return (lamb**k * math.exp(-lamb)) / math.factorial(k)


# ==========================================
# SIDEBAR
# ==========================================
st.sidebar.header("🔑 Paramètres & Bankroll")
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
    st.sidebar.slider("Seuil EV minimum (% Value) :", 0.0, 15.0, 2.0, 0.5) / 100.0
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

if not ODDS_API_KEY:
  st.warning("👈 Entrez votre clé API dans le menu à gauche pour démarrer.")
  st.stop()


# ==========================================
# MOTEUR DE CALCULS IMPLICITES AUTOMATIQUES
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


def estimate_implied_xg(c1, cN, c2, c_o25):
  """Déduit les xG automatiques des 2 équipes à partir des cotes du marché."""
  p1_raw, p2_raw = 1 / c1, 1 / c2
  total_prob = p1_raw + p2_raw
  ratio_home = p1_raw / total_prob if total_prob > 0 else 0.5

  # Estimation des buts totaux selon le marché Over 2.5
  total_xg = 2.75 if c_o25 < 1.80 else (2.25 if c_o25 > 2.10 else 2.50)

  xg_h = round(total_xg * ratio_home * 1.05, 2)
  xg_a = round(total_xg * (1 - ratio_home) * 0.95, 2)
  return max(0.4, xg_h), max(0.4, xg_a)


def dixon_coles_adjustment(h, a, lambda_h, lambda_a, rho=-0.05):
  if h == 0 and a == 0:
    return 1.0 - (lambda_h * lambda_a * rho)
  elif h == 0 and a == 1:
    return 1.0 + (lambda_h * rho)
  elif h == 1 and a == 0:
    return 1.0 + (lambda_a * rho)
  elif h == 1 and a == 1:
    return 1.0 - rho
  return 1.0


def build_bivariate_poisson_matrix(xg_home, xg_away, max_goals=7):
  matrix = np.zeros((max_goals, max_goals))
  for h in range(max_goals):
    for a in range(max_goals):
      p_h = poisson_pmf(h, xg_home)
      p_a = poisson_pmf(a, xg_away)
      adj = dixon_coles_adjustment(h, a, xg_home, xg_away)
      matrix[h, a] = max(0.0, p_h * p_a * adj)
  matrix /= np.sum(matrix)
  return matrix


def calculate_kelly_stake(prob, odds, bankroll, fraction):
  b = odds - 1.0
  f = (b * prob - (1.0 - prob)) / b
  return round(f * fraction * bankroll, 2) if f > 0 else 0.0


# ==========================================
# RENDER DES MATCHS (100% AUTOMATIQUE)
# ==========================================
matches = fetch_odds_data(league_map_odds[league_choice], ODDS_API_KEY)

if not matches:
  st.error(
      f"Aucun match trouvé pour {league_choice}. Changez de championnat dans le"
      " menu."
  )
else:
  st.success(f"⚡ {len(matches)} matchs analysés pour {league_choice} !")

  for match in matches:
    home_team = match["home_team"]
    away_team = match["away_team"]

    bookmakers = match.get("bookmakers", [])
    if not bookmakers:
      continue

    # Priorité Winamax
    selected_bm = next(
        (b for b in bookmakers if b["key"].lower() == "winamax"), bookmakers[0]
    )
    bm_title = selected_bm.get("title", "Bookmaker")

    markets = selected_bm.get("markets", [])
    h2h = next((m for m in markets if m["key"] == "h2h"), None)
    totals = next((m for m in markets if m["key"] == "totals"), None)

    if not h2h:
      continue

    cote_1 = next(
        (i["price"] for i in h2h["outcomes"] if i["name"] == home_team), 1.0
    )
    cote_2 = next(
        (i["price"] for i in h2h["outcomes"] if i["name"] == away_team), 1.0
    )
    cote_N = next(
        (i["price"] for i in h2h["outcomes"] if i["name"] == "Draw"), 1.0
    )

    cote_o25, cote_u25 = 1.85, 1.85
    if totals:
      for o in totals["outcomes"]:
        if o.get("point") == 2.5:
          if o["name"] == "Over":
            cote_o25 = o["price"]
          elif o["name"] == "Under":
            cote_u25 = o["price"]

    # --- CALCULS XG AUTOMATIQUES ---
    xg_home, xg_away = estimate_implied_xg(cote_1, cote_N, cote_2, cote_o25)
    matrix = build_bivariate_poisson_matrix(xg_home, xg_away)

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

    with st.expander(
        f"⚽ {home_team} vs {away_team}  ({bm_title})", expanded=True
    ):
      st.write(
        f"📊 **xG Modélisés :** `{xg_home}` ({home_team}) - `{xg_away}`"
        f" ({away_team})"
      )

      data = [
          {
              "Marché": f"Victoire {home_team} (1)",
              "Probabilité": prob_1,
              "Cote Bookie": cote_1,
          },
          {"Marché": "Match Nul (N)", "Probabilité": prob_N, "Cote Bookie": cote_N},
          {
              "Marché": f"Victoire {away_team} (2)",
              "Probabilité": prob_2,
              "Cote Bookie": cote_2,
          },
          {
              "Marché": "Over 2.5 Buts",
              "Probabilité": prob_over25,
              "Cote Bookie": cote_o25,
          },
          {
              "Marché": "Under 2.5 Buts",
              "Probabilité": prob_under25,
              "Cote Bookie": cote_u25,
          },
      ]

      df = pd.DataFrame(data)
      df["Cote Équitable"] = df["Probabilité"].apply(
          lambda x: round(1 / x, 2) if x > 0 else 99
      )
      df["Expected Value (EV)"] = (df["Probabilité"] * df["Cote Bookie"]) - 1.0
      df["Mise (€)"] = df.apply(
          lambda r: calculate_kelly_stake(
              r["Probabilité"], r["Cote Bookie"], bankroll, kelly_fraction
          ),
          axis=1,
      )

      col1, col2 = st.columns([1.3, 1])

      with col1:
        df_disp = df.copy()
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
                    "Cote Bookie",
                    "Expected Value (EV)",
                    "Mise (€)",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

      with col2:
        st.markdown("**🎯 Value Bets Détectées**")
        val_bets = df[df["Expected Value (EV)"] >= min_ev_threshold]

        if len(val_bets) == 0:
          st.info("Aucune valeur détectée sur ce match.")
        else:
          for _, row in val_bets.iterrows():
            ev_pct = round(row["Expected Value (EV)"] * 100, 1)
            st.success(
                f"🔥 **{row['Marché']}** @ **{row['Cote Bookie']}**\n\n→ Value :"
                f" **+{ev_pct}%** | Mise conseillée : **{row['Mise (€)']} €**"
            )
