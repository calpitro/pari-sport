import streamlit as st
import pandas as pd
import numpy as np
import requests

st.set_page_config(page_title="🎯 QuantBet Auto - Foot & Tennis", layout="wide")
st.title("🎯 QuantBet Studio - Dashboard Automatique")
st.caption("Données API, Effectifs, Loi de Poisson, Surface & Altitude")
st.markdown("---")

st.sidebar.header("⚙️ Configuration API")
API_KEY = st.sidebar.text_input("Entre ta clé The Odds API :", type="password")

if not API_KEY:
    st.warning("👈 Veuillez entrer votre clé API dans le panneau de gauche.")
    st.info("Obtenez une clé gratuite sur : https://the-odds-api.com/")
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
    altitude_choice = st.sidebar.checkbox("Tournoi en Altitude (> 500m, ex: Madrid, Gstaad)", value=False)
    format_grand_chelem = st.sidebar.checkbox("Format Grand Chelem (3 sets gagnants)", value=False)

@st.cache_data(ttl=1800)
def get_active_tennis_keys(api_k):
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

all_matches = []
league_choice = ""

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
    tennis_keys = get_active_tennis_keys(API_KEY)
    for key in tennis_keys:
        matches = fetch_odds(key, API_KEY)
        if matches:
            all_matches.extend(matches)

# FALLBACK FOOTBALL
if not all_matches and sport_choice == "Football" and "Trophée des Champions" in league_choice:
    all_matches = [{
        'home_team': 'Lens',
        'away_team': 'Paris SG',
        'bookmakers': [{
            'markets': [{
                'outcomes': [
                    {'name': 'Lens', 'price': 4.30},
                    {'name': 'Paris SG', 'price': 1.68}
                ]
            }]
        }]
    }]

# --- BASE DE DONNÉES EFFECTIFS ET JOUEURS ---
EFFECTIFS_FOOT = {
    "Paris SG": ["Donnarumma", "Marquinhos", "Hakimi", "Nuno Mendes", "Vitinha", "Zaïre-Emery", "Dembélé", "Barcola", "Kolo Muani"],
    "Lens": ["Samba", "Gradit", "Medina", "Danso", "Frankowski", "Machado", "Diouf", "Sotoca", "Saïd"],
    "Real Madrid": ["Courtois", "Carvajal", "Rüdiger", "Militao", "Mendy", "Valverde", "Bellingham", "Vinicius Jr", "Mbappé"],
    "Barcelona": ["Ter Stegen", "Koundé", "Araujo", "Cubarsí", "Balde", "Pedri", "Gavi", "Yamal", "Lewandowski"],
    "Manchester City": ["Ederson", "Walker", "Dias", "Akanji", "Gvardiol", "Rodri", "De Bruyne", "Foden", "Haaland"],
    "Arsenal": ["Raya", "White", "Saliba", "Gabriel", "Timber", "Rice", "Odegaard", "Saka", "Martinelli", "Havertz"]
}

TENNIS_PROFILES = {
    "Tsitsipas": {"main": "Droitier", "style": "Attaquant / Service-Volée", "aces_avg": 9},
    "Auger-Aliassime": {"main": "Droitier", "style": "Puissant / Serveur", "aces_avg": 11},
    "Fonseca": {"main": "Droitier", "style": "Attaquant de fond de court", "aces_avg": 6},
    "van de Zandschulp": {"main": "Droitier", "style": "Polyvalent", "aces_avg": 6},
    "Altmaier": {"main": "Droitier", "style": "Terre-battue / Revers 1 main", "aces_avg": 5},
    "Musetti": {"main": "Droitier", "style": "Créatif / Revers 1 main", "aces_avg": 5},
    "Hurkacz": {"main": "Droitier", "style": "Gros Serveur", "aces_avg": 14},
    "Berrettini": {"main": "Droitier", "style": "Gros Serveur / Coup droit", "aces_avg": 12},
    "Shelton": {"main": "Gaucher", "style": "Gros Serveur / Explosif", "aces_avg": 14},
    "Sinner": {"main": "Droitier", "style": "Cadenceur de fond de court", "aces_avg": 8},
    "Alcaraz": {"main": "Droitier", "style": "Complet / Variation", "aces_avg": 5},
    "Djokovic": {"main": "Droitier", "style": "Relanceur / Contreur", "aces_avg": 7}
}

SERVEURS_TOP = {
    "Isner": 18, "Opelka": 17, "Karlovic": 19, "Hurkacz": 14, "Berrettini": 12,
    "Raonic": 15, "Kyrgios": 13, "Bublik": 12, "Zverev": 10, "Medvedev": 9,
    "Fritz": 11, "Shelton": 14, "Cilic": 12, "Khachanov": 9, "Tsitsipas": 9,
    "Sinner": 8, "Alcaraz": 5, "Djokovic": 7, "Rune": 7, "Monfils": 8
}

def get_tennis_profile(player_name):
    for key, data in TENNIS_PROFILES.items():
        if key.lower() in player_name.lower():
            return data
    return {"main": "Droitier", "style": "Standard", "aces_avg": 6}

def analyser_rencontre(equipe_home, equipe_away, sport, cote_home, cote_away, surface="Dur", vitesse="Médium", is_alt=False, is_gc=False):
    seed_value = abs(hash(equipe_home + equipe_away)) % (2**32)
    np.random.seed(seed_value)
    
    prob_mkt_home = 1 / cote_home
    prob_mkt_away = 1 / cote_away
    
    stats = {}
    
    if sport == "Football":
        stats["forme_home"] = round(min(max((prob_mkt_home * 10) + 2.5, 3.0), 9.5), 1)
        stats["forme_away"] = round(min(max((prob_mkt_away * 10) + 1.5, 3.0), 9.5), 1)
        
        lambda_buts = max(1.8, 3.2 - (abs(cote_home - cote_away) * 0.2))
        prob_0_buts = np.exp(-lambda_buts)
        prob_1_but = lambda_buts * np.exp(-lambda_buts)
        
        stats["over_1_5_prob"] = round(1.0 - (prob_0_buts + prob_1_but), 2)
        stats["over_2_5_prob"] = round(stats["over_1_5_prob"] - 0.22, 2)
        stats["btts_prob"] = round(0.52 + (0.08 if abs(cote_home - cote_away) < 0.8 else -0.06), 2)
        
        # Effectifs
        eff_h = EFFECTIFS_FOOT.get(equipe_home, ["Joueurs clés non répertoriés"])
        eff_a = EFFECTIFS_FOOT.get(equipe_away, ["Joueurs clés non répertoriés"])
        
        stats["eff_home"] = ", ".join(eff_h[:6]) + "..."
        stats["eff_away"] = ", ".join(eff_a[:6]) + "..."
        
        summary = f"💡 **Analyse Poisson/xG :** Espérance de buts estimée à {round(lambda_buts, 2)} buts."
        stats["summary"] = summary
    else:
        stats["forme_home"] = round(min(max(prob_mkt_home * 10 + 1.5, 3.0), 9.5), 1)
        stats["forme_away"] = round(min(max(prob_mkt_away * 10 + 1.5, 3.0), 9.5), 1)
        
        coef_surface = 0.65 if surface == "Terre battue" else (1.35 if surface == "Gazon" else 1.0)
        coef_vitesse = 0.82 if "Lent" in vitesse else (1.20 if "Rapide" in vitesse else 1.0)
        coef_alt = 1.25 if is_alt else 1.0
        coef_format = 1.5 if is_gc else 1.0
        
        prof_h = get_tennis_profile(equipe_home)
        prof_a = get_tennis_profile(equipe_away)
        
        stats["prof_home"] = f"{prof_h['main']} | {prof_h['style']}"
        stats["prof_away"] = f"{prof_a['main']} | {prof_a['style']}"
        
        aces_h_base = prof_h["aces_avg"]
        aces_a_base = prof_a["aces_avg"]
        
        aces_h_final = int(aces_h_base * coef_surface * coef_vitesse * coef_alt * coef_format)
        aces_a_final = int(aces_a_base * coef_surface * coef_vitesse * coef_alt * coef_format)
        
        stats["aces_home"] = aces_h_final
        stats["aces_away"] = aces_a_final
        
        palier_h = max(3.5, np.floor(aces_h_final - 1) + 0.5)
        palier_a = max(3.5, np.floor(aces_a_final - 1) + 0.5)
        
        stats["palier_h"] = f"Over {palier_h} Aces ({equipe_home}) @ 1.80"
        stats["palier_a"] = f"Over {palier_a} Aces ({equipe_away}) @ 1.80"
        
        if aces_h_final > aces_a_final:
            stats["cote_aces_fav"] = f"Plus d'aces : {equipe_home} (@ 1.55)"
        elif aces_a_final > aces_h_final:
            stats["cote_aces_fav"] = f"Plus d'aces : {equipe_away} (@ 1.60)"
        else:
            stats["cote_aces_fav"] = "Volume d'aces équivalent attendu"

        stats["summary"] = f"💡 **Conditions :** {surface} ({vitesse.split(' ')[0]}) | Altitude : {'Oui (+25% aces)' if is_alt else 'Non'}"
        
    return stats

# --- AFFICHAGE ---
if not all_matches:
    st.warning("Aucun match à venir trouvé actuellement pour cette compétition.")
else:
    st.success(f"✅ {len(all_matches)} match(s) chargé(s) !")
    
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
        stats = analyser_rencontre(home, away, sport_choice, cote_home, cote_away, surface_choice, vitesse_choice, altitude_choice, format_grand_chelem)
        
        prob_algo_home = (1 / cote_home)
        prob_algo_away = (1 / cote_away)
        
        with st.expander(f"⚔️ {home} vs {away}", expanded=True):
            st.info(stats["summary"])
            
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
                    st.markdown("**⚽ Métriques & Effectifs**")
                    st.write(f"• BTTS (Oui) : **{int(stats['btts_prob']*100)}%**")
                    st.write(f"• Over 1.5 buts : **{int(stats['over_1_5_prob']*100)}%**")
                    st.caption(f"👥 **{home}** : {stats['eff_home']}")
                    st.caption(f"👥 **{away}** : {stats['eff_away']}")
                else:
                    st.markdown("**🎾 Profils & Paliers Aces**")
                    st.caption(f"👤 **{home}** : {stats['prof_home']}")
                    st.caption(f"👤 **{away}** : {stats['prof_away']}")
                    st.write(f"• Est. Aces : **{stats['aces_home']}** ({home}) / **{stats['aces_away']}** ({away})")
                    st.write(f"• {stats['palier_h']}")
                    st.write(f"• {stats['palier_a']}")

            with c3:
                st.markdown("**🎯 Value Bets Détectées**")
                if is_foot:
                    if stats['over_1_5_prob'] > 0.78:
                        st.success("VALUE : Over 1.5 Buts")
                    if stats['btts_prob'] > 0.58:
                        st.success("VALUE : Les 2 équipes marquent")
                    if stats['over_1_5_prob'] <= 0.78 and stats['btts_prob'] <= 0.58:
                        st.info("Aucune Value majeure sur les marchés principaux.")
                else:
                    has_value = False
                    if stats['aces_home'] >= (14 if format_grand_chelem else 10):
                        st.success(f"VALUE : {stats['palier_h']}")
                        has_value = True
                    if stats['aces_away'] >= (14 if format_grand_chelem else 10):
                        st.success(f"VALUE : {stats['palier_a']}")
                        has_value = True
                    if abs(cote_home - cote_away) < 0.25:
                        st.success("VALUE : Over Games / Match accroché")
                        has_value = True
                    if not has_value:
                        st.info("Aucune Value majeure détectée.")
