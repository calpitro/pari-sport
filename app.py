import datetime
import math
import numpy as np
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="QuantBet Pro - Monthly Tracker", page_icon="📈", layout="wide"
)

st.title("⚽ QuantBet Pro - Moteur +EV & Suivi Mensuel")
st.markdown("---")

# ==========================================
# INITIALISATION DU SESSION STATE (Suivi du mois)
# ==========================================
if "historique_paris" not in st.session_state:
  st.session_state.historique_paris = []

# ==========================================
# SIDEBAR - CONFIGURATION & BUDGET
# ==========================================
st.sidebar.header("🔑 Clés API")
ODDS_API_KEY = st.sidebar.text_input("The Odds API Key :", type="password")
RAPID_API_KEY = st.sidebar.text_input("RapidAPI Key :", type="password")

st.sidebar.markdown("---")
st.sidebar.header("📅 Budget Mensuel")

mois_options = [
    "Janvier",
    "Février",
    "Mars",
    "Avril",
    "Mai",
    "Juin",
    "Juillet",
    "Août",
    "Septembre",
    "Octobre",
    "Novembre",
    "Décembre",
]
mois_actuel = mois_options[datetime.datetime.now().month - 1]
selected_month = st.sidebar.selectbox(
    "Mois actif :", mois_options, index=mois_options.index(mois_actuel)
)

bankroll_initiale = st.sidebar.number_input(
    f"Capital initial pour {selected_month} (€) :",
    min_value=10.0,
    value=500.0,
    step=50.0,
)

kelly_fraction = st.sidebar.select_slider(
    "Fraction Kelly :", options=[0.1, 0.25, 0.5, 1.0], value=0.25
)
min_ev_threshold = (
    st.sidebar.slider("Seuil EV minimum (%) :", 0.0, 15.0, 2.0, 0.5) / 100.0
)

st.sidebar.markdown("---")
league_choice = st.sidebar.selectbox(
    "Championnat :",
    [
        "🇫🇷 France - Ligue 1",
        "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Angleterre - Premier League",
        "🇪🇸 Espagne - La Liga",
        "🇮🇹 Italie - Serie A",
        "🇩🇪 Allemagne - Bundesliga",
    ],
)

league_map_odds = {
    "🇫🇷 France - Ligue 1": "soccer_france_ligue_one",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Angleterre - Premier League": "soccer_epl",
    "🇪🇸 Espagne - La Liga": "soccer_spain_la_liga",
    "🇮🇹 Italie - Serie A": "soccer_italy_serie_a",
    "🇩🇪 Allemagne - Bundesliga": "soccer_germany_bundesliga",
}

if not ODDS_API_KEY or not RAPID_API_KEY:
  st.warning(
      "👈 Veuillez renseigner vos clés API dans la barre latérale pour"
      " démarrer."
  )
  st.stop()


# ==========================================
# FONCTIONS MATHÉMATIQUES ET API
# ==========================================
def poisson_pmf(k, lamb):
  return (lamb**k * math.exp(-lamb)) / math.factorial(k)


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


@st.cache_data(ttl=3600)
def fetch_rapidapi_stats(team_name, api_key):
  # Logique d'appel RapidAPI pour récupérer les xG/buts
  try:
    # Intègre ici ton endpoint réel RapidAPI
    return 1.4, 1.1
  except Exception:
    return 1.3, 1.2


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


def calculate_kelly_stake(prob, odds, bankroll, fraction):
  b = odds - 1.0
  f = (b * prob - (1.0 - prob)) / b
  return round(f * fraction * bankroll, 2) if f > 0 else 0.0


# ==========================================
# TABLEAU DE BORD BANGRKOL MENSUEL
# ==========================================
total_mises_cours = sum(
    [p["Mise"] for p in st.session_state.historique_paris if p["Mois"] == selected_month]
)
bankroll_disponible = bankroll_initiale - total_mises_cours

col_b1, col_b2, col_b3 = st.columns(3)
col_b1.metric(
    f"Capital Initial ({selected_month})", f"{bankroll_initiale} €"
)
col_b2.metric("Engagé en cours", f"{round(total_mises_cours, 2)} €")
col_b3.metric("Capital Disponible", f"{round(bankroll_disponible, 2)} €")
st.markdown("---")

# ==========================================
# CHARGEMENT DES MATCHS ET CALCULS
# ==========================================
matches = fetch_odds_data(league_map_odds[league_choice], ODDS_API_KEY)

if not matches:
  st.error(
      f"Aucun match disponible pour {league_choice}. Vérifiez vos clés ou la"
      " ligue."
  )
else:
  st.success(f"⚡ {len(matches)} matchs chargés pour {league_choice} !")

  for match in matches:
    home_team = match["home_team"]
    away_team = match["away_team"]

    bookmakers = match.get("bookmakers", [])
    if not bookmakers:
      continue

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

    h_for, h_ag = fetch_rapidapi_stats(home_team, RAPID_API_KEY)
    a_for, a_ag = fetch_rapidapi_stats(away_team, RAPID_API_KEY)

    xg_home = round(h_for * (a_ag / 1.2) * 1.1, 2)
    xg_away = round(a_for * (h_ag / 1.2), 2)

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
        f"⚽ {home_team} vs {away_team} ({bm_title})", expanded=False
    ):
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
      # Le calcul de mise prend en compte le capital réellement disponible du mois
      df["Mise (€)"] = df.apply(
          lambda r: calculate_kelly_stake(
              r["Probabilité"], r["Cote Bookie"], bankroll_disponible, kelly_fraction
          ),
          axis=1,
      )

      val_bets = df[df["Expected Value (EV)"] >= min_ev_threshold]

      if len(val_bets) == 0:
        st.info("Aucune valeur détectée sur ce match.")
      else:
        for _, row in val_bets.iterrows():
          ev_pct = round(row["Expected Value (EV)"] * 100, 1)
          col_v1, col_v2 = st.columns([3, 1])
          with col_v1:
            st.success(
                f"🔥 **{row['Marché']}** @ **{row['Cote Bookie']}** | Value :"
                f" **+{ev_pct}%** | Mise conseillée : **{row['Mise (€)']} €**"
            )
          with col_v2:
            bet_id = f"{home_team}-{away_team}-{row['Marché']}"
            if st.button("Valider le Pari", key=bet_id):
              st.session_state.historique_paris.append({
                  "Mois": selected_month,
                  "Match": f"{home_team} vs {away_team}",
                  "Pari": row["Marché"],
                  "Cote": row["Cote Bookie"],
                  "Mise": row["Mise (€)"],
              })
              st.rerun()

# ==========================================
# HISTORIQUE DES PARIS DU MOIS
# ==========================================
st.markdown("---")
st.subheader(f"📋 Suivi des paris validés pour {selected_month}")

paris_du_mois = [
    p for p in st.session_state.historique_paris if p["Mois"] == selected_month
]

if not paris_du_mois:
  st.info(
      "Aucun pari enregistré pour ce mois-ci. Clique sur 'Valider le Pari' pour"
      " l'ajouter à ton suivi."
  )
else:
  df_historique = pd.DataFrame(paris_du_mois)
  st.dataframe(df_historique[["Match", "Pari", "Cote", "Mise"]], use_container_width=True, hide_index=True)
  
  if st.button("🗑️ Effacer l'historique du mois"):
    st.session_state.historique_paris = [
        p for p in st.session_state.historique_paris if p["Mois"] != selected_month
    ]
    st.rerun()
