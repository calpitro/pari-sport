import streamlit as st
import numpy as np
from scipy.stats import poisson

# Configuration de la page Streamlit
st.set_page_config(page_title="ATP Aces Predictor Engine", layout="centered")

st.title("🎾 ATP Aces & Market Predictor Engine")
st.markdown("Analyse prédictive des aces, lignes Over/Under et combinés par surface.")

# ==============================================================================
# 1. BASE DE DONNÉES COMPLÈTE ATP
# ==============================================================================
ATP_PLAYER_DATABASE = {
    "Jannik Sinner": {"Hard": {"aces": 10.4, "return_1st": 0.34}, "Clay": {"aces": 5.2, "return_1st": 0.31}, "Grass": {"aces": 12.0, "return_1st": 0.33}},
    "Carlos Alcaraz": {"Hard": {"aces": 7.1, "return_1st": 0.36}, "Clay": {"aces": 4.0, "return_1st": 0.33}, "Grass": {"aces": 9.5, "return_1st": 0.35}},
    "Alexander Zverev": {"Hard": {"aces": 10.4, "return_1st": 0.30}, "Clay": {"aces": 6.5, "return_1st": 0.28}, "Grass": {"aces": 11.8, "return_1st": 0.29}},
    "Novak Djokovic": {"Hard": {"aces": 9.8, "return_1st": 0.38}, "Clay": {"aces": 5.0, "return_1st": 0.36}, "Grass": {"aces": 10.5, "return_1st": 0.37}},
    "Daniil Medvedev": {"Hard": {"aces": 10.7, "return_1st": 0.33}, "Clay": {"aces": 4.5, "return_1st": 0.30}, "Grass": {"aces": 11.0, "return_1st": 0.32}},
    "Taylor Fritz": {"Hard": {"aces": 15.4, "return_1st": 0.27}, "Clay": {"aces": 8.0, "return_1st": 0.25}, "Grass": {"aces": 16.5, "return_1st": 0.26}},
    "Hubert Hurkacz": {"Hard": {"aces": 15.6, "return_1st": 0.26}, "Clay": {"aces": 9.0, "return_1st": 0.24}, "Grass": {"aces": 18.0, "return_1st": 0.25}},
    "Ben Shelton": {"Hard": {"aces": 12.1, "return_1st": 0.28}, "Clay": {"aces": 6.0, "return_1st": 0.26}, "Grass": {"aces": 14.0, "return_1st": 0.27}},
    "Alexander Bublik": {"Hard": {"aces": 13.9, "return_1st": 0.29}, "Clay": {"aces": 7.5, "return_1st": 0.26}, "Grass": {"aces": 15.5, "return_1st": 0.28}},
    "Giovanni Mpetshi Perricard": {"Hard": {"aces": 19.1, "return_1st": 0.22}, "Clay": {"aces": 11.0, "return_1st": 0.20}, "Grass": {"aces": 21.5, "return_1st": 0.21}},
    "Alexander Blockx": {"Hard": {"aces": 7.52, "return_1st": 0.31}, "Clay": {"aces": 3.10, "return_1st": 0.26}, "Grass": {"aces": 8.90, "return_1st": 0.29}},
    "Jiri Lehecka": {"Hard": {"aces": 10.3, "return_1st": 0.32}, "Clay": {"aces": 4.5, "return_1st": 0.28}, "Grass": {"aces": 11.5, "return_1st": 0.30}},
    "Alejandro Tabilo": {"Hard": {"aces": 6.1, "return_1st": 0.29}, "Clay": {"aces": 5.2, "return_1st": 0.33}, "Grass": {"aces": 7.0, "return_1st": 0.27}},
    "Flavio Cobolli": {"Hard": {"aces": 4.8, "return_1st": 0.30}, "Clay": {"aces": 3.5, "return_1st": 0.31}, "Grass": {"aces": 5.5, "return_1st": 0.28}},
    "Arthur Fils": {"Hard": {"aces": 8.5, "return_1st": 0.30}, "Clay": {"aces": 4.2, "return_1st": 0.28}, "Grass": {"aces": 9.8, "return_1st": 0.29}},
    "Tommy Paul": {"Hard": {"aces": 7.2, "return_1st": 0.34}, "Clay": {"aces": 3.8, "return_1st": 0.32}, "Grass": {"aces": 8.0, "return_1st": 0.33}},
    "Adolfo Daniel Vallejo": {"Hard": {"aces": 5.0, "return_1st": 0.32}, "Clay": {"aces": 3.0, "return_1st": 0.35}, "Grass": {"aces": 5.8, "return_1st": 0.30}},
    "Marco Trungelliti": {"Hard": {"aces": 3.5, "return_1st": 0.33}, "Clay": {"aces": 2.1, "return_1st": 0.35}, "Grass": {"aces": 4.0, "return_1st": 0.31}}
}

DEFAULT_STATS = {"aces": 6.0, "return_1st": 0.30}

# ==============================================================================
# 2. INTERFACE UTILISATEUR (Sidebar & Paramètres)
# ==============================================================================
st.sidebar.header("⚙️ Paramètres du Match")

player_list = sorted(list(ATP_PLAYER_DATABASE.keys()))

player_a = st.sidebar.selectbox("Joueur 1 (Serveur A)", player_list, index=player_list.index("Alexander Blockx"))
player_b = st.sidebar.selectbox("Joueur 2 (Serveur B)", player_list, index=player_list.index("Flavio Cobolli"))

surface = st.sidebar.selectbox("Surface", ["Hard", "Clay", "Grass"])
multiplier = st.sidebar.slider("Multiplicateur de Vitesse du Tournoi", 0.5, 1.5, 1.18, 0.01)

line_book = st.sidebar.number_input("Ligne Bookmaker (Total Aces)", min_value=0.5, max_value=35.0, value=12.5, step=0.5)

# ==============================================================================
# 3. CALCULATEUR
# ==============================================================================
def get_stats(player, surf):
    return ATP_PLAYER_DATABASE.get(player, {}).get(surf, DEFAULT_STATS)

stats_a = get_stats(player_a, surface)
stats_b = get_stats(player_b, surface)

vuln_b = 1.0 - stats_b["return_1st"]
vuln_a = 1.0 - stats_a["return_1st"]

expected_a = stats_a["aces"] * vuln_b * multiplier
expected_b = stats_b["aces"] * vuln_a * multiplier
total_expected = expected_a + expected_b

prob_over = (1 - poisson.cdf(line_book, total_expected)) * 100
prob_under = 100 - prob_over

# ==============================================================================
# 4. AFFICHAGE DES RÉSULTATS SUR L'APPLICATION
# ==============================================================================
st.subheader(f"📊 Analyse : {player_a} vs {player_b}")
col1, col2, col3 = st.columns(3)

col1.metric(label=f"Aces attendus ({player_a})", value=round(expected_a, 2))
col2.metric(label=f"Aces attendus ({player_b})", value=round(expected_b, 2))
col3.metric(label="Total Match Estimé", value=round(total_expected, 2))

st.markdown("---")
st.subheader(f"🎯 Simulation pour la ligne : {line_book} Aces")

res_col1, res_col2 = st.columns(2)
res_col1.metric(label="Probabilité Over (Plus de)", value=f"{round(prob_over, 1)} %")
res_col2.metric(label="Probabilité Under (Moins de)", value=f"{round(prob_under, 1)} %")

if prob_over > 55.0:
    st.success(f"💡 **Recommandation du modèle :** Value potentielle détectée sur l'**Over {line_book}** (Forte probabilité statistique).")
elif prob_under > 55.0:
    st.warning(f"💡 **Recommandation du modèle :** Value potentielle détectée sur l'**Under {line_book}**.")
else:
    st.info("💡 Match équilibré, la ligne du bookmaker semble proche des probabilités réelles.")
