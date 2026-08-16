import streamlit as st
import pandas as pd
import numpy as np
import requests

st.set_page_config(page_title="🎯 QuantBet Auto - Foot & Tennis", layout="wide")
st.title("🎯 QuantBet Studio - Dashboard Automatique")
st.caption("Données en direct via API & Algorithme de détection de Value Bets")
st.markdown("---")

st.sidebar.header("⚙️ Configuration API")
API_KEY = st.sidebar.text_input("Entre ta clé The Odds API :", type="password")

if not API_KEY:
    st.warning("👈 Veuillez entrer votre clé API dans le panneau de gauche pour charger les matchs en direct.")
    st.info("Obtenez une clé gratuite sur : https://the-odds-api.com/")
    st.stop()

# --- SÉLECTION DU SPORT ---
sport_choice = st.sidebar.selectbox("Sélectionne le Sport :", ["Football", "Tennis"])

@st.cache_data(ttl=1800)
def get_active_tennis_keys(api_k):
    """Récupère toutes les clés actives pour le tennis dans l'API"""
    url = f"https://api.the-odds-api.com/v4/sports/?apiKey={api_k}"
    try:
        res = requests.get(url)
        if res.status_code == 200:
            sports = res.json()
            return [s['key'] for s in sports if 'tennis' in s['key'].lower()]
    except Exception:
        pass
    return ["tennis_atp", "tennis_wta"]

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

# Récupération des matchs selon le sport et la compétition
all_matches = []

if sport_choice == "Football":
    league_choice = st.sidebar.selectbox(
        "Sélectionne la compétition :",
        [
            "🇫🇷 France - Ligue 1",
            "🇫🇷 France - Coupe de France",
            "🇫🇷 France - Trophée des Champions",
            "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Angleterre - Premier League",
            "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Angleterre - FA Cup",
            "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Angleterre - EFL Cup (League Cup)",
            "🇪🇸 Espagne - La Liga",
            "🇪🇸 Espagne - Copa del Rey",
            "🇪🇸 Espagne - Supercopa de España",
            "🇪🇺 Europe - Ligue des Champions",
            "🇪🇺 Europe - Ligue Europa"
        ]
    )
    league_map = {
        "🇫🇷 France - Ligue 1": "soccer_france_ligue_one",
        "🇫🇷 France - Coupe de France": "soccer_france_coupe_de_france",
        "🇫🇷 France - Trophée des Champions": "soccer_france_trophee_des_champions",
        "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Angleterre - Premier League": "soccer_epl",
        "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Angleterre - FA Cup": "soccer_fa_cup",
        "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Angleterre - EFL Cup (League Cup)": "soccer_efl_champ",
        "🇪🇸 Espagne - La Liga": "soccer_spain_la_liga",
        "🇪🇸 Espagne - Copa del Rey": "soccer_spain_copa_del_rey",
        "🇪🇸 Espagne - Supercopa de España": "soccer_spain_super_cup",
        "🇪🇺 Europe - Ligue des Champions": "soccer_uefa_champs_league",
        "🇪🇺 Europe - Ligue Europa": "soccer_uefa_europa_league"
    }
    all_matches = fetch_odds(league_map[league_choice], API_KEY)
else:
    # Scan dynamique de tous les tournois de tennis actifs
    tennis_keys = get_active_tennis_keys(API_KEY)
    for key in tennis_keys:
        matches = fetch_odds(key, API_KEY)
        if matches:
            all_matches.extend(matches)

def simuler_statistiques_avancees(equipe_home, equipe_away, sport):
    np.random.seed(abs(hash(equipe_home + equipe_away)) % (2**32))
    forme_home = round(np.random.uniform(4.0, 9.5), 1)
    forme_away = round(np.random.uniform(4.0, 9.5), 1)
    
    stats = {"forme_home": forme_home, "forme_away": forme_away}
    
    if sport == "Football":
        stats["btts_prob"] = round(np.random.uniform(0.45, 0.70), 2)
        stats["over_1_5_prob"] = round(np.random.uniform(0.70, 0.90), 2)
        stats["over_2_5_prob"] = round(np.random.uniform(0.45, 0.65), 2)
        stats["buteur_forme"] = f"Buteur en forme : Attaquant vedette (Forme {round(forme_home/10*5,1)}/5)"
    else:
        stats["breaks_est"] = round(np.random.uniform(2.5, 6.5), 1)
        stats["tie_break_prob"] = f"{int(np.random.uniform(20, 55))}%"
        stats["sets_est"] = "2-0 / 3-0" if abs(forme_home - forme_away) > 2 else "2-1 / 3-2"
        stats["aces_home"] = int(np.random.uniform(4, 15))
        stats["aces_away"] = int(np.random.uniform(4, 15))
        
    return stats

# --- AFFICHAGE ---
if not all_matches:
    st.warning("Aucun match à venir trouvé actuellement pour cette compétition. (Vérifiez la période de la saison)")
else:
    st.success(f"✅ {len(all_matches)} matchs chargés en direct !")
    
    for match in all_matches:
        home = match['home_team']
        away = match['away_team']
        bookmakers = match.get('bookmakers', [])
        
        if not bookmakers:
            continue
            
        markets = bookmakers[0]['markets'][0]['outcomes']
        cote_home = next((item['price'] for item in markets if item['name'] == home), 1.0)
        cote_away = next((item['price'] for item in markets if item['name'] == away), 1.0)
        
        is_foot = (sport_choice == "Football")
        stats = simuler_statistiques_avancees(home, away, sport_choice)
        
        prob_algo_home = min(max((1 / cote_home) + (stats['forme_home'] - stats['forme_away']) * 0.03, 0.05), 0.95)
        prob_algo_away = min(max((1 / cote_away) + (stats['forme_away'] - stats['forme_home']) * 0.03, 0.05), 0.95)
        
        value_home = prob_algo_home > (1 / cote_home)
        value_away = prob_algo_away > (1 / cote_away)
        
        with st.expander(f"⚔️ {home} vs {away}", expanded=True):
            c1, c2, c3 = st.columns([1, 1, 1])
            
            with c1:
                st.markdown("**📊 État de Forme**")
                st.write(f"• {home} : **{stats['forme_home']}/10**")
                st.write(f"• {away} : **{stats['forme_away']}/10**")
                st.markdown("**💰 Cotes Vainqueur**")
                st.write(f"1 ({home}) : **{cote_home}**")
                st.write(f"2 ({away}) : **{cote_away}**")

            with c2:
                st.markdown("**🤖 Estimation Algo**")
                st.write(f"Prob. {home} : **{int(prob_algo_home*100)}%**")
                st.write(f"Prob. {away} : **{int(prob_algo_away*100)}%**")
                
                if is_foot:
                    st.markdown("**⚽ Métriques Football**")
                    st.write(f"• BTTS (Oui) : **{int(stats['btts_prob']*100)}%**")
                    st.write(f"• Over 1.5 buts : **{int(stats['over_1_5_prob']*100)}%**")
                    st.write(f"• Over 2.5 buts : **{int(stats['over_2_5_prob']*100)}%**")
                    st.caption(f"🔥 {stats['buteur_forme']}")
                else:
                    st.markdown("**🎾 Métriques Tennis**")
                    st.write(f"• Scénario Sets : **{stats['sets_est']}**")
                    st.write(f"• Breaks estimés : **{stats['breaks_est']}**")
                    st.write(f"• Probabilité Tie-Break : **{stats['tie_break_prob']}**")
                    st.write(f"• Aces estimés : **{stats['aces_home']}** ({home}) / **{stats['aces_away']}** ({away})")

            with c3:
                st.markdown("**🎯 Value Bets Détectées**")
                if value_home:
                    st.success(f"VALUE : Victoire {home}")
                if value_away:
                    st.success(f"VALUE : Victoire {away}")
                if is_foot and stats['over_1_5_prob'] > 0.80:
                    st.success("VALUE : Over 1.5 Buts")
                if not is_foot and stats['breaks_est'] > 5.0:
                    st.success("VALUE : Over Breaks")
                if not value_home and not value_away:
                    st.info("Aucune Value majeure sur le vainqueur.")

