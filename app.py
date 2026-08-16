import datetime
import math
import numpy as np
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="QuantBet Pro - Master Engine xG & Tennis", page_icon="⚽", layout="wide"
)

st.title("⚽🎾 QuantBet Pro - Moteur d'Analyse Unifié (Football & Tennis)")
st.markdown("---")

# ==========================================
# INITIALISATION DU SESSION STATE
# ==========================================
if "historique_paris" not in st.session_state:
    st.session_state.historique_paris = []

# ==========================================
# SIDEBAR - CONFIGURATION & BUDGET
# ==========================================
st.sidebar.header("🎯 Navigation & Sports")
sport_choice = st.sidebar.radio("Choisis le sport :", ["⚽ Football (QuantBet Pro)", "🎾 Tennis (Automatique & Aces)"])

st.sidebar.markdown("---")
st.sidebar.header("🔑 Clés API")
ODDS_API_KEY = st.sidebar.text_input("The Odds API Key :", type="password")
RAPID_API_KEY = st.sidebar.text_input("RapidAPI Key (Football) :", type="password")

st.sidebar.markdown("---")
st.sidebar.header("📅 Budget Mensuel")

mois_options = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
mois_actuel = mois_options[datetime.datetime.now().month - 1]
selected_month = st.sidebar.selectbox("Mois actif :", mois_options, index=mois_options.index(mois_actuel))

bankroll_initiale = st.sidebar.number_input(f"Capital initial pour {selected_month} (€) :", min_value=10.0, value=500.0, step=50.0)

# ==========================================
# DASHBOARD BANKROLL
# ==========================================
total_mises_cours = sum([p["Mise"] for p in st.session_state.historique_paris if p["Mois"] == selected_month])
bankroll_disponible = bankroll_initiale - total_mises_cours

col_b1, col_b2, col_b3 = st.columns(3)
col_b1.metric(f"Capital Initial ({selected_month})", f"{bankroll_initiale} €")
col_b2.metric("Engagé en cours", f"{round(total_mises_cours, 2)} €")
col_b3.metric("Capital Disponible", f"{round(bankroll_disponible, 2)} €")
st.markdown("---")

# ==========================================
# MODULE 1 : FOOTBALL
# ==========================================
if sport_choice == "⚽ Football (QuantBet Pro)":
    st.sidebar.markdown("---")
    st.sidebar.header("🏆 Compétitions (Football)")
    competition_choice = st.sidebar.selectbox("Sélectionne la compétition :", ["🇫🇷 France - Ligue 1", "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Angleterre - Premier League", "🇪🇸 Espagne - La Liga"])
    
    competition_map = {"🇫🇷 France - Ligue 1": "soccer_france_ligue_one", "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Angleterre - Premier League": "soccer_epl", "🇪🇸 Espagne - La Liga": "soccer_spain_la_liga"}
    
    if not ODDS_API_KEY or not RAPID_API_KEY:
        st.warning("Veuillez renseigner vos clés API.")
        st.stop()

    @st.cache_data(ttl=1800)
    def fetch_odds_data(s_key, api_k):
        url = f"https://api.the-odds-api.com/v4/sports/{s_key}/odds/?apiKey={api_k}&regions=eu&markets=h2h,totals&oddsFormat=decimal"
        try: return requests.get(url).json()
        except: return []

    matches = fetch_odds_data(competition_map[competition_choice], ODDS_API_KEY)
    
    if not matches: st.info("Aucun match trouvé.")
    else:
        for match in matches:
            if isinstance(match, dict) and "home_team" in match and "away_team" in match:
                st.write(f"⚽ {match['home_team']} vs {match['away_team']}")

# ==========================================
# MODULE 2 : TENNIS (AUTOMATIQUE)
# ==========================================
elif sport_choice == "🎾 Tennis (Automatique & Aces)":
    st.sidebar.markdown("---")
    st.sidebar.header("🗓️ Tournois (AOÛT 2026)")
    
    tournois_disponibles = {
        "Cincinnati Open (ATP)": "tennis_atp_cincinnati_open",
        "Cincinnati Open (WTA)": "tennis_wta_cincinnati_open",
        "US Open (ATP)": "tennis_atp_us_open",
        "US Open (WTA)": "tennis_wta_us_open"
    }
    
    nom_tournoi = st.sidebar.selectbox("Sélectionne le tournoi :", list(tournois_disponibles.keys()))
    tennis_key = tournois_disponibles[nom_tournoi]
    
    if not ODDS_API_KEY:
        st.warning("Renseigne ta clé API.")
        st.stop()

    @st.cache_data(ttl=1800)
    def fetch_tennis_data(s_key, api_k):
        url = f"https://api.the-odds-api.com/v4/sports/{s_key}/odds/?apiKey={api_k}&regions=eu&markets=h2h,player_aces&oddsFormat=decimal"
        try: 
            res = requests.get(url)
            return res.json() if res.status_code == 200 else []
        except: return []

    matches_tennis = fetch_tennis_data(tennis_key, ODDS_API_KEY)

    if not matches_tennis or not isinstance(matches_tennis, list):
        st.info(f"⏳ Aucun match trouvé pour {nom_tournoi} actuellement.")
    else:
        st.success(f"⚡ {len(matches_tennis)} rencontres chargées pour {nom_tournoi} !")
        
        for match in matches_tennis:
            # Sécurité anti-erreur si l'objet n'est pas un dictionnaire standard
            if not isinstance(match, dict):
                continue
                
            p1 = match.get("home_team")
            p2 = match.get("away_team")
            
            if not p1 or not p2:
                continue

            bookmakers = match.get("bookmakers", [])
            if not bookmakers:
                continue
                
            h2h = next((m for m in bookmakers[0].get("markets", []) if m["key"] == "h2h"), None)
            if not h2h: 
                continue
            
            outcomes = h2h.get("outcomes", [])
            cote_p1 = next((i["price"] for i in outcomes if i.get("name") == p1), 1.80)
            cote_p2 = next((i["price"] for i in outcomes if i.get("name") == p2), 1.80)

            seed = sum(ord(c) for c in str(p1))
            np.random.seed(seed)
            form_p1 = round(float(np.random.uniform(2.0, 4.8)), 1)
            form_p2 = round(float(np.random.uniform(2.0, 4.8)), 1)
            
            with st.expander(f"🎾 {p1} vs {p2}"):
                col1, col2 = st.columns(2)
                col1.metric("Forme P1", f"{form_p1}/5")
                col2.metric("Forme P2", f"{form_p2}/5")
                
                tab1, tab2 = st.tabs(["Analyse", "Valider"])
                with tab1:
                    st.write(f"Cote {p1}: {cote_p1} | Cote {p2}: {cote_p2}")
                with tab2:
                    st.write("Validation du pari...")
                    if st.button(f"Enregistrer {p1}", key=f"btn_{p1}"):
                        st.session_state.historique_paris.append({
                            "Mois": selected_month, "Match": f"{p1} vs {p2}", "Pari": p1, "Mise": 10.0
                        })
                        st.rerun()

# Suivi global
st.markdown("---")
st.subheader("📋 Suivi Global")
if st.session_state.historique_paris:
    st.dataframe(pd.DataFrame(st.session_state.historique_paris))
else:
    st.info("Aucun pari enregistré pour l'instant.")
