import streamlit as st
import pandas as pd
import numpy as np
import requests

st.set_page_config(page_title="🎯 QuantBet Auto - Foot & Tennis", layout="wide")
st.title("🎯 QuantBet Studio - Dashboard Automatique")
st.caption("Données API, Scraping Auto des 5 derniers matchs & Calcul de Forme")
st.markdown("---")

st.sidebar.header("⚙️ Configuration API")
ODDS_API_KEY = st.sidebar.text_input("Clé The Odds API :", type="password")
FOOTBALL_API_KEY = st.sidebar.text_input("Clé API-Football (RapidAPI) :", type="password", help="Optionnel : pour charger la forme automatique")

if not ODDS_API_KEY:
    st.warning("👈 Veuillez entrer au moins votre clé The Odds API dans le panneau de gauche.")
    st.stop()

# --- SÉLECTION DU SPORT & OPTIONS TENNIS ---
sport_choice = st.sidebar.selectbox("Sélectionne le Sport :", ["Football", "Tennis"])

surface_choice = "Dur"
vitesse_choice = "Médium"
altitude_choice = False
format_grand_chelem = False

if sport_choice == "Tennis":
    st.sidebar.subheader("🎾 Configuration Tournoi & Conditions")
    surface_choice = st.sidebar.selectbox("Surface du tournoi :", ["Dur", "Terre battue", "Gazon"])
    vitesse_choice = st.sidebar.selectbox(
        "Vitesse du Court :", 
        ["Lent (ex: Montréal, Indian Wells)", "Médium (ex: US Open, Paris-Bercy)", "Rapide (ex: Cincinnati, Shanghai)"]
    )
    altitude_choice = st.sidebar.checkbox("Tournoi en Altitude (> 500m)", value=False)
    format_grand_chelem = st.sidebar.checkbox("Format Grand Chelem (3 sets)", value=False)

@st.cache_data(ttl=1800)
def fetch_odds(s_key, api_k):
    url = f"https://api.the-odds-api.com/v4/sports/{s_key}/odds/?apiKey={api_k}&regions=eu&markets=h2h&oddsFormat=decimal"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return []

# --- FONCTION AUTO-FETCH DES 5 DERNIERS MATCHS ---
@st.cache_data(ttl=3600)
def get_team_last_5_results(team_name, api_key):
    """
    Interroge l'API Football pour récupérer le bilan réel des 5 derniers matchs
    """
    if not api_key:
        return {"v": 3, "n": 1, "d": 1, "status": "Simulé (Pas de clé API-Football)"}

    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "v3.football.api-sports.io"
    }
    
    try:
        # 1. Recherche de l'ID de l'équipe
        search_url = f"https://v3.football.api-sports.io/teams?search={team_name}"
        res_team = requests.get(search_url, headers=headers).json()
        
        if not res_team.get("response"):
            return {"v": 2, "n": 2, "d": 1, "status": "Équipe non trouvée"}
            
        team_id = res_team["response"][0]["team"]["id"]
        
        # 2. Récupération des 5 derniers matchs
        fixtures_url = f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=5"
        res_fix = requests.get(fixtures_url, headers=headers).json()
        
        v, n, d = 0, 0, 0
        for match in res_fix.get("response", []):
            goals_home = match["goals"]["home"]
            goals_away = match["goals"]["away"]
            is_home = match["teams"]["home"]["id"] == team_id
            
            if goals_home == goals_away:
                n += 1
            elif (is_home and goals_home > goals_away) or (not is_home and goals_away > goals_home):
                v += 1
            else:
                d += 1
                
        return {"v": v, "n": n, "d": d, "status": "Auto (API)"}
    except Exception:
        return {"v": 2, "n": 2, "d": 1, "status": "Erreur connexion"}

def calculer_note_forme(v, n, d, est_domicile=True):
    pts = (v * 3) + (n * 1)
    note_base = (pts / 15.0) * 10
    bonus = 1.10 if est_domicile else 0.90
    return round(min(max(note_base * bonus, 1.5), 9.8), 1)

# --- RECUPERATION DES MATCHS ---
all_matches = []
league_choice = ""

if sport_choice == "Football":
    league_choice = st.sidebar.selectbox(
        "Sélectionne la compétition :",
        ["🇫🇷 France - Ligue 1", "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Angleterre - Premier League", "🇪🇸 Espagne - La Liga", "🇪🇺 Europe - Ligue des Champions"]
    )
    league_map = {
        "🇫🇷 France - Ligue 1": "soccer_france_ligue_one",
        "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Angleterre - Premier League": "soccer_epl",
        "🇪🇸 Espagne - La Liga": "soccer_spain_la_liga",
        "🇪🇺 Europe - Ligue des Champions": "soccer_uefa_champs_league"
    }
    all_matches = fetch_odds(league_map[league_choice], ODDS_API_KEY)

# --- AFFICHAGE ---
if not all_matches:
    st.warning("Aucun match trouvé.")
else:
    st.success(f"✅ {len(all_matches)} match(s) chargé(s) !")
    
    for match in all_matches:
        home = match['home_team']
        away = match['away_team']
        markets = match.get('bookmakers', [{}])[0].get('markets', [{}])[0].get('outcomes', [])
        
        cote_home = next((item['price'] for item in markets if item['name'] == home), 1.0)
        cote_away = next((item['price'] for item in markets if item['name'] == away), 1.0)
        
        # Récupération automatique des 5 derniers matchs
        data_h = get_team_last_5_results(home, FOOTBALL_API_KEY)
        data_a = get_team_last_5_results(away, FOOTBALL_API_KEY)
        
        note_h = calculer_note_forme(data_h["v"], data_h["n"], data_h["d"], est_domicile=True)
        note_a = calculer_note_forme(data_a["v"], data_a["n"], data_a["d"], est_domicile=False)
        
        with st.expander(f"⚔️ {home} vs {away}", expanded=True):
            c1, c2, c3 = st.columns([1, 1, 1])
            
            with c1:
                st.markdown("**📊 Forme Auto (5 derniers matchs)**")
                st.write(f"• **{home}** (Dom) : **{note_h}/10** ({data_h['v']}V-{data_h['n']}N-{data_h['d']}D)")
                st.write(f"• **{away}** (Ext) : **{note_a}/10** ({data_a['v']}V-{data_a['n']}N-{data_a['d']}D)")
                st.caption(f"Source données : {data_h['status']}")
                
                st.markdown("**💰 Cotes Vainqueur**")
                st.write(f"1 ({home}) : **{cote_home}** | 2 ({away}) : **{cote_away}**")

            with c2:
                prob_h = int((1 / cote_home) * 100)
                prob_a = int((1 / cote_away) * 100)
                st.markdown("**🤖 Estimation Algo**")
                st.write(f"Prob. {home} : **{prob_h}%** | Prob. {away} : **{prob_a}%**")
                
                diff_forme = (note_h - note_a) / 10.0
                lambda_buts = max(1.2, 2.5 + (diff_forme * 0.6))
                
                st.markdown("**⚽ Métriques Marchés**")
                st.write(f"• xG Estimé : **{round(lambda_buts, 2)} buts**")
                st.write(f"• Over 1.5 buts : **{int(min(lambda_buts * 30, 88))}%**")

            with c3:
                st.markdown("**🎯 Value Bets**")
                if note_h >= 7.0 and prob_h < 60:
                    st.success(f"VALUE : Victoire {home} (Bonne forme dom)")
                elif note_a >= 7.0 and prob_a < 50:
                    st.success(f"VALUE : Victoire {away} (Bonne forme ext)")
                elif lambda_buts > 2.7:
                    st.success("VALUE : Over 2.5 Buts")
                else:
                    st.info("Aucune Value majeure")
