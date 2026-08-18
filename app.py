import streamlit as st
import numpy as np
from scipy.stats import poisson

# Configuration de la page Streamlit
st.set_page_config(page_title="ATP Aces Predictor - Advanced Engine", layout="centered")

st.title("🎾 ATP Aces & Market Predictor Engine (Pro)")
st.markdown("Moteur avancé : Surface, Météo/Altitude, Volume de sets & 1ère balle.")

# ==============================================================================
# 1. BASE DE DONNÉES AVANCÉE (Top 100 & Paramètres de Service)
# Format : "Surface": {"aces": moyenne par set/match de base, "return_1st": vulnérabilité, "1st_serve_pct": taux de 1ère balle}
# ==============================================================================
ATP_PLAYER_DATABASE = {
    "Jannik Sinner": {"Hard": {"aces": 5.2, "return_1st": 0.34, "1st_serve_pct": 0.62}, "Clay": {"aces": 2.6, "return_1st": 0.31, "1st_serve_pct": 0.60}, "Grass": {"aces": 6.0, "return_1st": 0.33, "1st_serve_pct": 0.64}},
    "Carlos Alcaraz": {"Hard": {"aces": 3.5, "return_1st": 0.36, "1st_serve_pct": 0.65}, "Clay": {"aces": 2.0, "return_1st": 0.33, "1st_serve_pct": 0.63}, "Grass": {"aces": 4.8, "return_1st": 0.35, "1st_serve_pct": 0.66}},
    "Alexander Zverev": {"Hard": {"aces": 5.2, "return_1st": 0.30, "1st_serve_pct": 0.72}, "Clay": {"aces": 3.2, "return_1st": 0.28, "1st_serve_pct": 0.70}, "Grass": {"aces": 5.9, "return_1st": 0.29, "1st_serve_pct": 0.73}},
    "Daniil Medvedev": {"Hard": {"aces": 5.3, "return_1st": 0.33, "1st_serve_pct": 0.63}, "Clay": {"aces": 2.2, "return_1st": 0.30, "1st_serve_pct": 0.60}, "Grass": {"aces": 5.5, "return_1st": 0.32, "1st_serve_pct": 0.64}},
    "Ben Shelton": {"Hard": {"aces": 7.0, "return_1st": 0.27, "1st_serve_pct": 0.61}, "Clay": {"aces": 3.8, "return_1st": 0.25, "1st_serve_pct": 0.58}, "Grass": {"aces": 8.0, "return_1st": 0.26, "1st_serve_pct": 0.63}},
    "Taylor Fritz": {"Hard": {"aces": 7.7, "return_1st": 0.27, "1st_serve_pct": 0.67}, "Clay": {"aces": 4.0, "return_1st": 0.25, "1st_serve_pct": 0.65}, "Grass": {"aces": 8.2, "return_1st": 0.26, "1st_serve_pct": 0.68}},
    "Hubert Hurkacz": {"Hard": {"aces": 7.8, "return_1st": 0.26, "1st_serve_pct": 0.66}, "Clay": {"aces": 4.5, "return_1st": 0.24, "1st_serve_pct": 0.64}, "Grass": {"aces": 9.0, "return_1st": 0.25, "1st_serve_pct": 0.68}},
    "Alexander Bublik": {"Hard": {"aces": 7.0, "return_1st": 0.29, "1st_serve_pct": 0.59}, "Clay": {"aces": 3.8, "return_1st": 0.26, "1st_serve_pct": 0.57}, "Grass": {"aces": 7.8, "return_1st": 0.28, "1st_serve_pct": 0.60}},
    "Giovanni Mpetshi Perricard": {"Hard": {"aces": 9.5, "return_1st": 0.22, "1st_serve_pct": 0.64}, "Clay": {"aces": 5.5, "return_1st": 0.20, "1st_serve_pct": 0.62}, "Grass": {"aces": 10.8, "return_1st": 0.21, "1st_serve_pct": 0.65}},
    "Flavio Cobolli": {"Hard": {"aces": 2.4, "return_1st": 0.30, "1st_serve_pct": 0.60}, "Clay": {"aces": 1.7, "return_1st": 0.31, "1st_serve_pct": 0.58}, "Grass": {"aces": 2.8, "return_1st": 0.28, "1st_serve_pct": 0.61}},
    "Andrey Rublev": {"Hard": {"aces": 4.6, "return_1st": 0.31, "1st_serve_pct": 0.61}, "Clay": {"aces": 2.8, "return_1st": 0.29, "1st_serve_pct": 0.59}, "Grass": {"aces": 5.2, "return_1st": 0.30, "1st_serve_pct": 0.62}},
    "Nuno Borges": {"Hard": {"aces": 3.8, "return_1st": 0.31, "1st_serve_pct": 0.63}, "Clay": {"aces": 2.1, "return_1st": 0.29, "1st_serve_pct": 0.61}, "Grass": {"aces": 4.2, "return_1st": 0.30, "1st_serve_pct": 0.64}}
}

DEFAULT_PLAYER_STATS = {"aces": 3.0, "return_1st": 0.30, "1st_serve_pct": 0.60}
FULL_PLAYER_LIST = sorted(list(ATP_PLAYER_DATABASE.keys()))

# ==============================================================================
# 2. INTERFACE UTILISATEUR AVANCÉE (Sidebar)
# ==============================================================================
st.sidebar.header("⚙️ Configuration du Match")

player_a = st.sidebar.selectbox("Joueur 1 (Serveur A)", FULL_PLAYER_LIST, index=0)
player_b = st.sidebar.selectbox("Joueur 2 (Serveur B)", FULL_PLAYER_LIST, index=1)

surface = st.sidebar.selectbox("Surface", ["Hard", "Clay", "Grass"])

st.sidebar.markdown("---")
st.sidebar.subheader("🌡️ Facteurs Environnementaux & Match")
# Facteur de sets prévus (2 sets secs vs match serré en 3 sets)
format_match = st.sidebar.selectbox("Format / Longueur du match", ["2 Sets Gagnants (Standard)", "3 Sets (Très serré / Tie-breaks)"])
sets_multiplier = 1.0 if format_match == "2 Sets Gagnants (Standard)" else 1.45

# Facteur Météo / Altitude (Ex: Madrid en altitude accélère la balle, humidité ralentit)
meteo_condition = st.sidebar.selectbox("Conditions Météo / Altitude", [
    "Normal / Neutre (1.0x)", 
    "Altitude Élevée (Balle rapide +10%)", 
    "Chaud & Sec (Balle vive +5%)", 
    "Humide / Lourd / Intérieur lent (-10%)"
])

meteo_multipliers = {
    "Normal / Neutre (1.0x)": 1.0,
    "Altitude Élevée (Balle rapide +10%)": 1.10,
    "Chaud & Sec (Balle vive +5%)": 1.05,
    "Humide / Lourd / Intérieur lent (-10%)": 0.90
}
meteo_factor = meteo_multipliers[meteo_condition]

# Vitesse propre du tournoi
surface_base_speed = {"Hard": 1.12, "Clay": 0.70, "Grass": 1.18}[surface]
total_multiplier = surface_base_speed * meteo_factor

line_book = st.sidebar.number_input("Ligne Bookmaker (Total Aces)", min_value=0.5, max_value=40.0, value=12.5, step=0.5)

# ==============================================================================
# 3. MOTEUR DE CALCUL MATHÉMATIQUE PRÉCIS
# ==============================================================================
def get_stats(player, surf):
    if player in ATP_PLAYER_DATABASE and surf in ATP_PLAYER_DATABASE[player]:
        return ATP_PLAYER_DATABASE[player][surf]
    return DEFAULT_PLAYER_STATS

stats_a = get_stats(player_a, surface)
stats_b = get_stats(player_b, surface)

# Pondération par le taux de 1ère balle (rapporté à la moyenne du circuit de 62%)
serve_power_a = stats_a["aces"] * (stats_a["1st_serve_pct"] / 0.62)
serve_power_b = stats_b["aces"] * (stats_b["1st_serve_pct"] / 0.62)

# Vulnérabilité de l'adversaire au retour
vuln_b = 1.0 - stats_b["return_1st"]
vuln_a = 1.0 - stats_a["return_1st"]

# Calcul final des espérances d'aces combinant surface, météo, sets et régularité
expected_a = serve_power_a * vuln_b * total_multiplier * sets_multiplier
expected_b = serve_power_b * vuln_a * total_multiplier * sets_multiplier
total_expected = expected_a + expected_b

# Application de la Loi de Poisson pour l'Over / Under
prob_over = (1 - poisson.cdf(line_book, total_expected)) * 100
prob_under = 100 - prob_over

# ==============================================================================
# 4. AFFICHAGE DES RÉSULTATS SUR L'APPLICATION
# ==============================================================================
st.subheader(f"📊 Analyse Précise : {player_a} vs {player_b}")
col1, col2, col3 = st.columns(3)

col1.metric(label=f"Aces ({player_a})", value=round(expected_a, 2))
col2.metric(label=f"Aces ({player_b})", value=round(expected_b, 2))
col3.metric(label="Total Estimé", value=round(total_expected, 2))

st.markdown("---")
st.subheader(f"🎯 Simulation de la Ligne : {line_book} Aces")

res_col1, res_col2 = st.columns(2)
res_col1.metric(label="Probabilité Over", value=f"{round(prob_over, 1)} %")
res_col2.metric(label="Probabilité Under", value=f"{round(prob_under, 1)} %")

if prob_over > 56.0:
    st.success(f"💡 **Recommandation :** Value avérée sur l'**Over {line_book}** (Conditions et profil favorables).")
elif prob_under > 56.0:
    st.warning(f"💡 **Recommandation :** Value avérée sur l'**Under {line_book}** (Conditions ou retours solides).")
else:
    st.info("💡 Match neutre par rapport aux lignes des bookmakers.")
    
