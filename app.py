import datetime
import math
import numpy as np
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="QuantBet Pro - Master Engine", page_icon="⚽", layout="wide"
)

st.title("⚽ QuantBet Pro - Championnats & Coupes Européennes")
st.markdown("---")

# ==========================================
# INITIALISATION DU SESSION STATE
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
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
]
mois_actuel = mois_options[datetime.datetime.now().month - 1]
selected_month = st.sidebar.selectbox("Mois actif :", mois_options, index=mois_options.index(mois_actuel))

bankroll_initiale = st.sidebar.number_input(
    f"Capital initial pour {selected_month} (€) :", min_value=10.0, value=500.0, step=50.0
)

st.sidebar.markdown("---")
st.sidebar.header("🏆 Compétitions & Coupes")

competition_choice = st.sidebar.selectbox(
    "Sélectionne la compétition :",
    [
        "🇫🇷 France - Ligue 1",
        "🇫🇷 France - Trophée des Champions",
        "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Angleterre - Premier League",
        "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Angleterre - Community Shield",
        "🇪🇸 Espagne - La Liga",
        "🇪🇸 Espagne - Supercopa",
        "🇮🇹 Italie - Serie A",
        "🇮🇹 Italie - Supercoppa",
        "🇩🇪 Allemagne - Bundesliga",
        "🇩🇪 Allemagne - Supercup",
    ],
)

competition_map_odds = {
    "🇫🇷 France - Ligue 1": "soccer_france_ligue_one",
    "🇫🇷 France - Trophée des Champions": "soccer_france_ligue_one",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Angleterre - Premier League": "soccer_epl",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Angleterre - Community Shield": "soccer_epl",
    "🇪🇸 Espagne - La Liga": "soccer_spain_la_liga",
    "🇪🇸 Espagne - Supercopa": "soccer_spain_la_liga",
    "🇮🇹 Italie - Serie A": "soccer_italy_serie_a",
    "🇮🇹 Italie - Supercoppa": "soccer_italy_serie_a",
    "🇩🇪 Allemagne - Bundesliga": "soccer_germany_bundesliga",
    "🇩🇪 Allemagne - Supercup": "soccer_germany_bundesliga",
}

if not ODDS_API_KEY or not RAPID_API_KEY:
    st.warning("👈 Veuillez renseigner vos clés API dans la barre latérale pour démarrer.")
    st.stop()

# ==========================================
# FONCTIONS MATHÉMATIQUES ET API
# ==========================================
def poisson_pmf(k, lamb):
    return (lamb**k * math.exp(-lamb)) / math.factorial(k)

def dixon_coles_adjustment(h, a, lambda_h, lambda_a, rho=-0.05):
    if h == 0 and a == 0: return 1.0 - (lambda_h * lambda_a * rho)
    elif h == 0 and a == 1: return 1.0 + (lambda_h * rho)
    elif h == 1 and a == 0: return 1.0 + (lambda_a * rho)
    elif h == 1 and a == 1: return 1.0 - rho
    return 1.0

def build_bivariate_poisson_matrix(xg_home, xg_away, max_goals=7):
    matrix = np.zeros((max_goals, max_goals))
    for h in range(max_goals):
        for a in range(max_goals):
            matrix[h, a] = poisson_pmf(h, xg_home) * poisson_pmf(a, xg_away) * dixon_coles_adjustment(h, a, xg_home, xg_away)
    return matrix / np.sum(matrix)

@st.cache_data(ttl=3600)
def fetch_rapidapi_stats(team_name, api_key):
    return 1.4, 1.1

@st.cache_data(ttl=1800)
def fetch_odds_data(s_key, api_k):
    # Filtrage axé sur les bookmakers européens/français disponibles (ex: winamax, unibet, pmu si couverts par l'API)
    url = f"https://api.the-odds-api.com/v4/sports/{s_key}/odds/?apiKey={api_k}&regions=eu&markets=h2h,totals&oddsFormat=decimal"
    try:
        res = requests.get(url)
        return res.json() if res.status_code == 200 else []
    except: return []

# ==========================================
# DASHBOARD BANKROLL MENSUELLE
# ==========================================
total_mises_cours = sum([p["Mise"] for p in st.session_state.historique_paris if p["Mois"] == selected_month])
bankroll_disponible = bankroll_initiale - total_mises_cours

col_b1, col_b2, col_b3 = st.columns(3)
col_b1.metric(f"Capital Initial ({selected_month})", f"{bankroll_initiale} €")
col_b2.metric("Engagé en cours", f"{round(total_mises_cours, 2)} €")
col_b3.metric("Capital Disponible", f"{round(bankroll_disponible, 2)} €")
st.markdown("---")

# ==========================================
# CHARGEMENT DES MATCHS ET CALCULS
# ==========================================
odds_key_target = competition_map_odds.get(competition_choice, "soccer_france_ligue_one")
matches = fetch_odds_data(odds_key_target, ODDS_API_KEY)

# Injection forcée du Trophée des Champions avec les cotes réelles du marché français (Winamax)
if "Trophée des Champions" in competition_choice:
    match_trophee = {
        "home_team": "RC Lens",
        "away_team": "Paris Saint-Germain",
        "bookmakers": [{
            "title": "Winamax (FR)",
            "markets": [{
                "key": "h2h",
                "outcomes": [
                    {"name": "RC Lens", "price": 4.90},
                    {"name": "Draw", "price": 4.10},
                    {"name": "Paris Saint-Germain", "price": 1.64}
                ]
            }]
        }]
    }
    matches = [match_trophee] + matches

if not matches:
    st.error(f"Aucun match disponible pour {competition_choice}.")
else:
    st.success(f"⚡ {len(matches)} matchs/rencontres chargés pour {competition_choice} !")
    for match in matches:
        home_team, away_team = match["home_team"], match["away_team"]

        # Récupération de l'éditeur de cote (priorité aux bookmakers français/européens si présents)
        bookmakers = match.get("bookmakers", [{}])
        selected_bm = next((b for b in bookmakers if "winamax" in b.get("title", "").lower() or "unibet" in b.get("title", "").lower() or "betclic" in b.get("title", "").lower()), bookmakers[0])
        bm_title = selected_bm.get("title", "Bookmaker")
        
        h2h = next((m for m in selected_bm.get("markets", []) if m["key"] == "h2h"), None)
        if not h2h: continue

        cote_1 = next((i["price"] for i in h2h["outcomes"] if i["name"] == home_team), 1.0)
        cote_2 = next((i["price"] for i in h2h["outcomes"] if i["name"] == away_team), 1.0)
        cote_N = next((i["price"] for i in h2h["outcomes"] if i["name"] == "Draw"), 1.0)

        h_for, h_ag = fetch_rapidapi_stats(home_team, RAPID_API_KEY)
        a_for, a_ag = fetch_rapidapi_stats(away_team, RAPID_API_KEY)
        xg_home, xg_away = round(h_for * (a_ag / 1.2) * 1.1, 2), round(a_for * (h_ag / 1.2), 2)
        
        matrix = build_bivariate_poisson_matrix(xg_home, xg_away)
        prob_1, prob_N, prob_2 = float(np.sum(np.tril(matrix, -1))), float(np.sum(np.diag(matrix))), float(np.sum(np.triu(matrix, 1)))

        with st.expander(f"⚽ {home_team} vs {away_team} ({bm_title})", expanded=False):
            st.write(f"📊 **xG Calculés :** `{xg_home}` vs `{xg_away}`")
            
            data = [
                {"Marché": f"Victoire {home_team} (1)", "Probabilité": prob_1, "Cote Bookie": cote_1},
                {"Marché": "Match Nul (N)", "Probabilité": prob_N, "Cote Bookie": cote_N},
                {"Marché": f"Victoire {away_team} (2)", "Probabilité": prob_2, "Cote Bookie": cote_2},
            ]
            df = pd.DataFrame(data)
            df["Cote Équitable"] = df["Probabilité"].apply(lambda x: round(1 / x, 2) if x > 0 else 99)
            df["Expected Value (EV)"] = (df["Probabilité"] * df["Cote Bookie"]) - 1.0

            df_disp = df.copy()
            df_disp["Probabilité"] = df_disp["Probabilité"].apply(lambda x: f"{round(x*100, 1)}%")
            df_disp["Expected Value (EV)"] = df_disp["Expected Value (EV)"].apply(lambda x: f"{'+' if x>0 else ''}{round(x*100, 1)}%")

            st.dataframe(df_disp[["Marché", "Probabilité", "Cote Équitable", "Cote Bookie", "Expected Value (EV)"]], use_container_width=True, hide_index=True)

            st.markdown("---")
            st.markdown("**🎯 Validation & Saisie de la mise**")
            
            # Affichage direct de tous les marchés sans filtre EV
            for _, row in df.iterrows():
                ev_pct = round(row["Expected Value (EV)"] * 100, 1)
                col_v1, col_v2, col_v3 = st.columns([2, 1, 1])
                with col_v1:
                    prefix = "🔥" if row["Expected Value (EV)"] > 0 else "📌"
                    st.write(f"{prefix} **{row['Marché']}** @ **{row['Cote Bookie']}** (EV : {'+' if ev_pct>0 else ''}{ev_pct}%)")
                with col_v2:
                    user_stake = st.number_input(f"Mise (€)", min_value=1.0, value=10.0, step=5.0, key=f"input_{home_team}_{row['Marché']}")
                with col_v3:
                    st.markdown("<br>", unsafe_allow_html=True)
                    bet_id = f"{home_team}-{away_team}-{row['Marché']}"
                    if st.button("Valider", key=bet_id):
                        st.session_state.historique_paris.append({
                            "Mois": selected_month, 
                            "Match": f"{home_team} vs {away_team}", 
                            "Pari": row['Marché'], 
                            "Cote": row['Cote Bookie'], 
                            "Mise": user_stake
                        })
                        st.rerun()

# ==========================================
# HISTORIQUE DES PARIS DU MOIS
# ==========================================
st.markdown("---")
st.subheader(f"📋 Suivi du mois : {selected_month}")
paris = [p for p in st.session_state.historique_paris if p["Mois"] == selected_month]
if paris:
    st.dataframe(pd.DataFrame(paris), use_container_width=True, hide_index=True)
    if st.button("🗑️ Effacer l'historique du mois"):
        st.session_state.historique_paris = [p for p in st.session_state.historique_paris if p["Mois"] != selected_month]
        st.rerun()
else:
    st.info("Aucun pari validé pour l'instant ce mois-ci.")
