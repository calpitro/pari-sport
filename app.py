import streamlit as st
import pandas as pd
import numpy as np
import requests

st.set_page_config(page_title="🎯 QuantBet Auto - Football Studio", layout="wide")
st.title("⚽ QuantBet Studio - Dashboard Football Auto")
st.caption("Données The Odds API | Modélisation Poisson/xG & Forme Personnalisable")
st.markdown("---")

# --- CONFIGURATION DES CLÉS API EN SIDEBAR ---
st.sidebar.header("⚙️ Configuration API")
ODDS_API_KEY = st.sidebar.text_input("Clé The Odds API :", type="password")

if not ODDS_API_KEY:
    st.warning("👈 Veuillez entrer votre clé The Odds API dans le panneau de gauche pour charger les matchs.")
    st.stop()

# --- SÉLECTION DE LA COMPÉTITION ---
league_choice = st.sidebar.selectbox(
    "Sélectionne la compétition :",
    [
        "🇫🇷 France - Ligue 1",
        "🇫🇷 France - Ligue 2",
        "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Angleterre - Premier League",
        "🇪🇸 Espagne - La Liga",
        "🇮🇹 Italie - Serie A",
        "🇩🇪 Allemagne - Bundesliga",
        "🇪🇺 Europe - Ligue des Champions",
        "🇪🇺 Europe - Ligue Europa"
    ]
)

league_map_odds = {
    "🇫🇷 France - Ligue 1": "soccer_france_ligue_one",
    "🇫🇷 France - Ligue 2": "soccer_france_ligue_two",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Angleterre - Premier League": "soccer_epl",
    "🇪🇸 Espagne - La Liga": "soccer_spain_la_liga",
    "🇮🇹 Italie - Serie A": "soccer_italy_serie_a",
    "🇩🇪 Allemagne - Bundesliga": "soccer_germany_bundesliga",
    "🇪🇺 Europe - Ligue des Champions": "soccer_uefa_champs_league",
    "🇪🇺 Europe - Ligue Europa": "soccer_uefa_europa_league"
}

# --- FONCTION : RÉCUPÉRATION COTES (The Odds API) ---
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

# --- CHARGEMENT DES MATCHS ---
all_matches = fetch_odds(league_map_odds[league_choice], ODDS_API_KEY)

if not all_matches:
    st.warning("Aucun match à venir trouvé pour cette compétition.")
else:
    st.success(f"✅ {len(all_matches)} match(s) chargé(s) pour {league_choice} !")
    
    for idx, match in enumerate(all_matches):
        home = match['home_team']
        away = match['away_team']
        
        bookmakers = match.get('bookmakers', [])
        if not bookmakers:
            continue
            
        markets = bookmakers[0]['markets'][0]['outcomes']
        cote_home = next((item['price'] for item in markets if item['name'] == home), 1.0)
        cote_away = next((item['price'] for item in markets if item['name'] == away), 1.0)

        with st.expander(f"⚽ {home} vs {away}", expanded=True):
            
            c1, c2, c3 = st.columns([1, 1, 1])
            
            with c1:
                st.markdown("**📊 Forme des Équipes (Sur 10)**")
                note_h = st.slider(f"Forme {home} (Dom)", 1.0, 10.0, 5.0, 0.5, key=f"h_{idx}")
                note_a = st.slider(f"Forme {away} (Ext)", 1.0, 10.0, 5.0, 0.5, key=f"a_{idx}")
                
                st.markdown("**💰 Cotes Bookmakers**")
                st.write(f"1 ({home}) : **{cote_home}**")
                st.write(f"2 ({away}) : **{cote_away}**")

            # Calculations Poisson & xG réactifs
            diff_forme = (note_h - note_a) / 10.0
            lambda_base = max(1.8, 3.2 - (abs(cote_home - cote_away) * 0.2))
            lambda_buts = max(1.2, lambda_base + (diff_forme * 0.5))
            
            prob_0_buts = np.exp(-lambda_buts)
            prob_1_but = lambda_buts * np.exp(-lambda_buts)
            prob_over_1_5 = round(1.0 - (prob_0_buts + prob_1_but), 2)
            prob_over_2_5 = round(prob_over_1_5 - 0.22, 2)
            prob_btts = round(0.52 + (0.08 if abs(cote_home - cote_away) < 0.8 else -0.06) + (diff_forme * 0.05), 2)
            prob_btts = min(max(prob_btts, 0.30), 0.85)

            with c2:
                prob_algo_home = int((1 / cote_home) * 100)
                prob_algo_away = int((1 / cote_away) * 100)
                
                st.markdown("**🤖 Probabilités Marché**")
                st.write(f"Prob. {home} : **{prob_algo_home}%**")
                st.write(f"Prob. {away} : **{prob_algo_away}%**")
                
                st.markdown("**⚽ Métriques Buts (xG)**")
                st.write(f"• Espérance de buts : **{round(lambda_buts, 2)}**")
                st.write(f"• BTTS (Les 2 marquent) : **{int(prob_btts*100)}%**")
                st.write(f"• Over 1.5 buts : **{int(prob_over_1_5*100)}%**")
                st.write(f"• Over 2.5 buts : **{int(prob_over_2_5*100)}%**")

            with c3:
                st.markdown("**🎯 Value Bets Détectées**")
                has_value = False
                
                if note_h >= 7.0 and prob_algo_home < 55:
                    st.success(f"VALUE : Victoire {home} (Bonne forme dom)")
                    has_value = True
                elif note_a >= 7.0 and prob_algo_away < 45:
                    st.success(f"VALUE : Victoire {away} (Bonne forme ext)")
                    has_value = True
                    
                if prob_over_1_5 > 0.78:
                    st.success("VALUE : Over 1.5 Buts")
                    has_value = True
                    
                if prob_btts > 0.60:
                    st.success("VALUE : Les 2 équipes marquent")
                    has_value = True
                    
                if not has_value:
                    st.info("Aucune Value majeure détectée sur ce match.")
