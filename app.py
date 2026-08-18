import streamlit as st
import numpy as np
import requests
from scipy.stats import poisson

# Configuration
st.set_page_config(page_title="ATP Aces Predictor - Top 100", layout="centered")
st.title("🎾 ATP Aces & Market Predictor (Top 100)")

# ==============================================================================
# 1. BASE DE DONNÉES ÉTENDUE (Top 100 ATP - Valeurs moyennes par MATCH complet)
# ==============================================================================
ATP_PLAYER_DATABASE = {
    # Top Joueurs / Gros Serveurs
    "Jannik Sinner": {"Hard": {"aces": 9.5, "return_1st": 0.34}, "Clay": {"aces": 6.0, "return_1st": 0.31}, "Grass": {"aces": 11.0, "return_1st": 0.33}},
    "Carlos Alcaraz": {"Hard": {"aces": 6.5, "return_1st": 0.36}, "Clay": {"aces": 5.0, "return_1st": 0.33}, "Grass": {"aces": 8.0, "return_1st": 0.35}},
    "Alexander Zverev": {"Hard": {"aces": 10.5, "return_1st": 0.30}, "Clay": {"aces": 7.0, "return_1st": 0.28}, "Grass": {"aces": 11.5, "return_1st": 0.29}},
    "Daniil Medvedev": {"Hard": {"aces": 10.0, "return_1st": 0.33}, "Clay": {"aces": 5.0, "return_1st": 0.30}, "Grass": {"aces": 9.5, "return_1st": 0.32}},
    "Hubert Hurkacz": {"Hard": {"aces": 14.5, "return_1st": 0.26}, "Clay": {"aces": 8.5, "return_1st": 0.24}, "Grass": {"aces": 16.5, "return_1st": 0.25}},
    "Ben Shelton": {"Hard": {"aces": 13.0, "return_1st": 0.27}, "Clay": {"aces": 7.5, "return_1st": 0.25}, "Grass": {"aces": 14.0, "return_1st": 0.26}},
    "Taylor Fritz": {"Hard": {"aces": 13.5, "return_1st": 0.27}, "Clay": {"aces": 7.5, "return_1st": 0.25}, "Grass": {"aces": 14.5, "return_1st": 0.26}},
    "Giovanni Mpetshi Perricard": {"Hard": {"aces": 18.0, "return_1st": 0.22}, "Clay": {"aces": 10.0, "return_1st": 0.20}, "Grass": {"aces": 20.0, "return_1st": 0.21}},
    "Alexander Bublik": {"Hard": {"aces": 13.0, "return_1st": 0.29}, "Clay": {"aces": 7.0, "return_1st": 0.26}, "Grass": {"aces": 14.0, "return_1st": 0.28}},
    "Felix Auger-Aliassime": {"Hard": {"aces": 12.0, "return_1st": 0.27}, "Clay": {"aces": 7.0, "return_1st": 0.25}, "Grass": {"aces": 13.5, "return_1st": 0.26}},
    "Alex De Minaur": {"Hard": {"aces": 5.5, "return_1st": 0.34}, "Clay": {"aces": 3.0, "return_1st": 0.32}, "Grass": {"aces": 6.5, "return_1st": 0.33}},
    "Novak Djokovic": {"Hard": {"aces": 7.0, "return_1st": 0.35}, "Clay": {"aces": 4.5, "return_1st": 0.32}, "Grass": {"aces": 8.5, "return_1st": 0.34}},
    "Stefanos Tsitsipas": {"Hard": {"aces": 9.0, "return_1st": 0.29}, "Clay": {"aces": 6.0, "return_1st": 0.27}, "Grass": {"aces": 10.0, "return_1st": 0.28}},
    "Andrey Rublev": {"Hard": {"aces": 8.0, "return_1st": 0.30}, "Clay": {"aces": 5.0, "return_1st": 0.28}, "Grass": {"aces": 9.0, "return_1st": 0.29}},
    "Grigor Dimitrov": {"Hard": {"aces": 9.5, "return_1st": 0.29}, "Clay": {"aces": 5.5, "return_1st": 0.27}, "Grass": {"aces": 10.5, "return_1st": 0.28}},
    "Matteo Berrettini": {"Hard": {"aces": 14.0, "return_1st": 0.26}, "Clay": {"aces": 8.0, "return_1st": 0.24}, "Grass": {"aces": 16.0, "return_1st": 0.25}},
    "Karen Khachanov": {"Hard": {"aces": 10.0, "return_1st": 0.29}, "Clay": {"aces": 6.0, "return_1st": 0.27}, "Grass": {"aces": 11.0, "return_1st": 0.28}},
    "Ugo Humbert": {"Hard": {"aces": 11.0, "return_1st": 0.28}, "Clay": {"aces": 6.5, "return_1st": 0.26}, "Grass": {"aces": 12.5, "return_1st": 0.27}},
    "Flavio Cobolli": {"Hard": {"aces": 5.0, "return_1st": 0.30}, "Clay": {"aces": 3.5, "return_1st": 0.31}, "Grass": {"aces": 5.5, "return_1st": 0.28}},
    "Alexander Blockx": {"Hard": {"aces": 7.5, "return_1st": 0.31}, "Clay": {"aces": 3.5, "return_1st": 0.26}, "Grass": {"aces": 8.5, "return_1st": 0.29}},
}

# Liste complète de référence du Top 100 ATP pour alimenter le selectbox instantanément
TOP_100_ATP = sorted(list(ATP_PLAYER_DATABASE.keys()) + [
    "Holger Rune", "Casper Ruud", "Tommy Paul", "Frances Tiafoe", "Jack Draper", 
    "Lorenzo Musetti", "Jiri Lehecka", "Sebastian Korda", "Alejandro Tabilo", 
    "Francisco Cerundolo", "Arthur Fils", "Tomas Martin Etcheverry", "Nuno Borges", 
    "Jordan Thompson", "Alex Michelsen", "Brandon Nakashima", "Marcos Giron", 
    "Luciano Darderi", "Tallon Griekspoor", "Roman Safiullin", "Pavel Kotov", 
    "Miomir Kecmanovic", "Fabian Marozsan", "Alexei Popyrin", "Zizou Bergs", 
    "Matteo Arnaldi", "Mariano Navone", "Sebastian Baez", "Cameron Norrie", 
    "Arthur Rinderknech", "Corentin Moutet", "Adrian Mannarino", "Qentin Halys", 
    "David Goffin", "Milos Raonic", "Stan Wawrinka", "Gaël Monfils", "Richard Gasquet"
])

def get_stats(player, surf):
    """Récupère les stats du joueur ou applique une moyenne standard du circuit si absent"""
    if player in ATP_PLAYER_DATABASE and surf in ATP_PLAYER_DATABASE[player]:
        return ATP_PLAYER_DATABASE[player][surf]
    # Valeur par défaut robuste pour tout joueur du top 100 non listé manuellement
    return {"aces": 7.0, "return_1st": 0.30}

# ==============================================================================
# 2. CONFIGURATION & SIDEBAR
# ==============================================================================
st.sidebar.header("⚙️ Configuration")
player_a = st.sidebar.selectbox("Joueur 1 (Serveur A)", TOP_100_ATP, index=0)
player_b = st.sidebar.selectbox("Joueur 2 (Serveur B)", TOP_100_ATP, index=1)
surface = st.sidebar.selectbox("Surface", ["Hard", "Clay", "Grass"])

# Multiplicateurs
format_match = st.sidebar.selectbox("Format du match", ["2 Sets Gagnants (Standard)", "3 Sets Gagnants (Grand Chelem)"])
format_multiplier = 1.0 if format_match == "2 Sets Gagnants (Standard)" else 1.65 

meteo = st.sidebar.selectbox("Conditions Météo", ["Normal", "Altitude (+10%)", "Lourd/Humide (-10%)"])
meteo_val = {"Normal": 1.0, "Altitude (+10%)": 1.10, "Lourd/Humide (-10%)": 0.90}[meteo]

line_book = st.sidebar.number_input("Ligne Bookmaker (Total Aces)", value=12.5, step=0.5)

# ==============================================================================
# 3. CALCUL DU MODÈLE
# ==============================================================================
stats_a = get_stats(player_a, surface)
stats_b = get_stats(player_b, surface)

# Calcul des espérances (Aces de base * Impact adverse * Multiplicateurs)
expected_a = stats_a["aces"] * (1.0 - stats_b["return_1st"]) * meteo_val * format_multiplier
expected_b = stats_b["aces"] * (1.0 - stats_a["return_1st"]) * meteo_val * format_multiplier
total_expected = expected_a + expected_b

# Distribution de Poisson
prob_over = (1 - poisson.cdf(line_book, total_expected)) * 100

# ==============================================================================
# 4. AFFICHAGE
# ==============================================================================
st.subheader(f"📊 Résultat : {player_a} vs {player_b}")
col1, col2, col3 = st.columns(3)
col1.metric("Aces A", round(expected_a, 1))
col2.metric("Aces B", round(expected_b, 1))
col3.metric("Total", round(total_expected, 1))

st.markdown("---")
st.write(f"### Probabilité Over {line_book} : **{round(prob_over, 1)}%**")

if prob_over > 55:
    st.success("✅ Value détectée sur l'OVER")
elif prob_over < 45:
    st.warning("✅ Value détectée sur l'UNDER")
else:
    st.info("⚠️ Marché équilibré (Pas de value claire)")
    
