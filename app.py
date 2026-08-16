import streamlit as st
import pandas as pd
import numpy as np
import requests

st.set_page_config(page_title="🎯 QuantBet Auto - Football Studio", layout="wide")
st.title("⚽ QuantBet Studio - Dashboard Football Auto")
st.caption("Données API-Sports & The Odds API | Analyse Poisson/xG & Forme Réelle 5 Matchs")
st.markdown("---")

# --- CONFIGURATION DES CLÉS API EN SIDEBAR ---
st.sidebar.header("⚙️ Configuration APIs")
ODDS_API_KEY = st.sidebar.text_input("Clé The Odds API :", type="password")
API_SPORTS_KEY = st.sidebar.text_input(
    "Clé API-Sports (dashboard.api-football.com) :", 
    type="password", 
    help="Utilisée pour récupérer automatiquement les 5 derniers résultats"
)

if not ODDS_API_KEY:
    st.warning("👈 Veuillez entrer au moins votre clé The Odds API dans le panneau de gauche pour charger les matchs.")
    st.stop()

# --- SÉLECTION DE LA COMPÉTITION FOOTBALL ---
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

league_map = {
    "🇫🇷 France - Ligue 1": "soccer_france_ligue_one",
    "🇫🇷 France - Ligue 2": "soccer_france_ligue_two",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Angleterre - Premier League": "soccer_epl",
    "🇪🇸 Espagne - La Liga": "soccer_spain_la_liga",
    "🇮🇹 Italie - Serie A": "soccer_italy_serie_a",
    "🇩🇪 Allemagne - Bundesliga": "soccer_germany_bundesliga",
    "🇪🇺 Europe - Ligue des Champions": "soccer_uefa_champs_league",
    "🇪🇺 Europe - Ligue Europa": "soccer_uefa_europa_league"
}

# --- FONCTION CACHÉE : RÉCUPÉRATION DES COTES (The Odds API) ---
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

# --- FONCTION CACHÉE : RECHERCHE AUTO AVEC NETTOYAGE DES NOMS D'ÉQUIPES ---
@st.cache_data(ttl=3600)
def get_team_last_5_results(team_name, api_key):
    """
    Interroge dashboard.api-football.com avec nettoyage de nom
    et fallback sur le premier mot-clé pour éviter les erreurs d'identification.
    """
    if not api_key:
        return {"v": 2, "n": 2, "d": 1, "status": "Simulé (Pas de clé API-Sports)"}

    headers = {"x-apisports-key": api_key}
    
    # Nettoyage des préfixes / suffixes fréquents
    clean_name = (
        team_name.replace("USL ", "")
        .replace("FC ", "")
        .replace("AS ", "")
        .replace(" SC", "")
        .replace(" AJ", "")
        .strip()
    )
    
    try:
        # 1. Premier essai avec le nom nettoyé
        search_url = f"https://v3.football.api-sports.io/teams?search={clean_name}"
        res_team = requests.get(search_url, headers=headers).json()
        
        # 2. Deuxième essai (fallback) si non trouvé : premier mot du nom de l'équipe
        if not res_team.get("response"):
            first_word = clean_name.split()[0] if clean_name else team_name
            search_url = f"https://v3.football.api-sports.io/teams?search={first_word}"
            res_team = requests.get(search_url, headers=headers).json()

        if not res_team.get("response"):
            return {"v": 2, "n": 2, "d": 1, "status": f"Non trouvé ({team_name})"}
            
        team_id = res_team["response"][0]["team"]["id"]
        
        # 3. Récupération des 5 derniers matchs joués
        fixtures_url = f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=5"
        res_fix = requests.get(fixtures_url, headers=headers).json()
        
        v, n, d = 0, 0, 0
        matches = res_fix.get("response", [])
        
        if not matches:
            return {"v": 2, "n": 2, "d": 1, "status": "Aucun match récent"}

        for match in matches:
            goals_home = match["goals"]["home"]
            goals_away = match["goals"]["away"]
            is_home = match["teams"]["home"]["id"] == team_id
            
            if goals_home is None or goals_away is None:
                continue
                
            if goals_home == goals_away:
                n += 1
            elif (is_home and goals_home > goals_away) or (not is_home and goals_away > goals_home):
                v += 1
            else:
                d += 1
                
        return {"v": v, "n": n, "d": d, "status": "Auto (API-Sports)"}
    except Exception:
        return {"v": 2, "n": 2, "d": 1, "status": "Erreur connexion"}

def calculer_note_forme(v, n, d, est_domicile=True):
    pts = (v * 3) + (n * 1)
    note_base = (pts / 15.0) * 10
    bonus = 1.10 if est_domicile else 0.90
    return round(min(max(note_base * bonus, 1.5), 9.8), 1)

# --- CHARGEMENT DES MATCHS ---
all_matches = fetch_odds(league_map[league_choice], ODDS_API_KEY)

# --- AFFICHAGE DASHBOARD ---
if not all_matches:
    st.warning("Aucun match à venir trouvé pour cette compétition.")
else:
    st.success(f"✅ {len(all_matches)} match(s) chargé(s) pour {league_choice} !")
    
    for match in all_matches:
        home = match['home_team']
        away = match['away_team']
        
        bookmakers = match.get('bookmakers', [])
        if not bookmakers:
            continue
            
        markets = bookmakers[0]['markets'][0]['outcomes']
        cote_home = next((item['price'] for item in markets if item['name'] == home), 1.0)
        cote_away = next((item['price'] for item in markets if item['name'] == away), 1.0)
        
        # Récupération automatique de la forme via l'API
        data_h = get_team_last_5_results(home, API_SPORTS_KEY)
        data_a = get_team_last_5_results(away, API_SPORTS_KEY)
        
        note_h = calculer_note_forme(data_h["v"], data_h["n"], data_h["d"], est_domicile=True)
        note_a = calculer_note_forme(data_a["v"], data_a["n"], data_a["d"], est_domicile=False)
        
        # Calculs Poisson & xG
        diff_forme = (note_h - note_a) / 10.0
        lambda_base = max(1.8, 3.2 - (abs(cote_home - cote_away) * 0.2))
        lambda_buts = max(1.2, lambda_base + (diff_forme * 0.5))
        
        prob_0_buts = np.exp(-lambda_buts)
        prob_1_but = lambda_buts * np.exp(-lambda_buts)
        prob_over_1_5 = round(1.0 - (prob_0_buts + prob_1_but), 2)
        prob_over_2_5 = round(prob_over_1_5 - 0.22, 2)
        prob_btts = round(0.52 + (0.08 if abs(cote_home - cote_away) < 0.8 else -0.06) + (diff_forme * 0.05), 2)
        prob_btts = min(max(prob_btts, 0.30), 0.85)

        with st.expander(f"⚽ {home} vs {away}", expanded=True):
            st.info(f"💡 **Analyse Poisson/xG :** Espérance de buts estimée à **{round(lambda_buts, 2)} buts** (Ajustée à la forme Domicile/Extérieur).")
            
            c1, c2, c3 = st.columns([1, 1, 1])
            
            with c1:
                st.markdown("**📊 État de Forme Réel**")
                st.write(f"• **{home}** (Dom) : **{note_h}/10** ({data_h['v']}V-{data_h['n']}N-{data_h['d']}D)")
                st.write(f"• **{away}** (Ext) : **{note_a}/10** ({data_a['v']}V-{data_a['n']}N-{data_a['d']}D)")
                st.caption(f"Source : {data_h['status']}")
                
                st.markdown("**💰 Cotes Bookmakers**")
                st.write(f"1 ({home}) : **{cote_home}**")
                st.write(f"2 ({away}) : **{cote_away}**")

            with c2:
                prob_algo_home = int((1 / cote_home) * 100)
                prob_algo_away = int((1 / cote_away) * 100)
                
                st.markdown("**🤖 Probabilités Marché**")
                st.write(f"Prob. {home} : **{prob_algo_home}%**")
                st.write(f"Prob. {away} : **{prob_algo_away}%**")
                
                st.markdown("**⚽ Métriques Buts**")
                st.write(f"• BTTS (Les 2 marquent) : **{int(prob_btts*100)}%**")
                st.write(f"• Over 1.5 buts : **{int(prob_over_1_5*100)}%**")
                st.write(f"• Over 2.5 buts : **{int(prob_over_2_5*100)}%**")

            with c3:
                st.markdown("**🎯 Value Bets Détectées**")
                has_value = False
                
                if note_h >= 7.0 and prob_algo_home < 55:
                    st.success(f"VALUE : Victoire {home} (Excellente forme dom)")
                    has_value = True
                elif note_a >= 7.0 and prob_algo_away < 45:
                    st.success(f"VALUE : Victoire {away} (Excellente forme ext)")
                    has_value = True
                    
                if prob_over_1_5 > 0.78:
                    st.success("VALUE : Over 1.5 Buts")
                    has_value = True
                    
                if prob_btts > 0.60:
                    st.success("VALUE : Les 2 équipes marquent")
                    has_value = True
                    
                if not has_value:
                    st.info("Aucune Value majeure détectée sur ce match.")
