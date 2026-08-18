import streamlit as st
import numpy as np
from scipy.stats import poisson

# Configuration de la page Streamlit
st.set_page_config(page_title="ATP Aces Predictor - Top 100", layout="centered")

st.title("🎾 ATP Aces & Market Predictor Engine (Top 100)")
st.markdown("Moteur de prédiction interactif basé sur l'intégralité du circuit professionnel ATP.")

# ==============================================================================
# 1. BASE DE DONNÉES ÉTENDUE (TOP 100 ATP & PROFILS CLÉS)
# ==============================================================================
ATP_PLAYER_DATABASE = {
    # Top 10 & Cadres
    "Jannik Sinner": {"Hard": {"aces": 10.4, "return_1st": 0.34}, "Clay": {"aces": 5.2, "return_1st": 0.31}, "Grass": {"aces": 12.0, "return_1st": 0.33}},
    "Carlos Alcaraz": {"Hard": {"aces": 7.1, "return_1st": 0.36}, "Clay": {"aces": 4.0, "return_1st": 0.33}, "Grass": {"aces": 9.5, "return_1st": 0.35}},
    "Alexander Zverev": {"Hard": {"aces": 10.4, "return_1st": 0.30}, "Clay": {"aces": 6.5, "return_1st": 0.28}, "Grass": {"aces": 11.8, "return_1st": 0.29}},
    "Felix Auger-Aliassime": {"Hard": {"aces": 13.5, "return_1st": 0.27}, "Clay": {"aces": 7.0, "return_1st": 0.25}, "Grass": {"aces": 15.0, "return_1st": 0.26}},
    "Novak Djokovic": {"Hard": {"aces": 9.8, "return_1st": 0.38}, "Clay": {"aces": 5.0, "return_1st": 0.36}, "Grass": {"aces": 10.5, "return_1st": 0.37}},
    "Alex de Minaur": {"Hard": {"aces": 5.5, "return_1st": 0.35}, "Clay": {"aces": 3.0, "return_1st": 0.33}, "Grass": {"aces": 6.8, "return_1st": 0.34}},
    "Daniil Medvedev": {"Hard": {"aces": 10.7, "return_1st": 0.33}, "Clay": {"aces": 4.5, "return_1st": 0.30}, "Grass": {"aces": 11.0, "return_1st": 0.32}},
    "Ben Shelton": {"Hard": {"aces": 14.1, "return_1st": 0.27}, "Clay": {"aces": 7.5, "return_1st": 0.25}, "Grass": {"aces": 16.0, "return_1st": 0.26}},
    "Taylor Fritz": {"Hard": {"aces": 15.4, "return_1st": 0.27}, "Clay": {"aces": 8.0, "return_1st": 0.25}, "Grass": {"aces": 16.5, "return_1st": 0.26}},
    "Flavio Cobolli": {"Hard": {"aces": 4.8, "return_1st": 0.30}, "Clay": {"aces": 3.5, "return_1st": 0.31}, "Grass": {"aces": 5.5, "return_1st": 0.28}},
    
    # Joueurs classés de 11 à 50
    "Alexander Bublik": {"Hard": {"aces": 13.9, "return_1st": 0.29}, "Clay": {"aces": 7.5, "return_1st": 0.26}, "Grass": {"aces": 15.5, "return_1st": 0.28}},
    "Jiri Lehecka": {"Hard": {"aces": 10.3, "return_1st": 0.32}, "Clay": {"aces": 4.5, "return_1st": 0.28}, "Grass": {"aces": 11.5, "return_1st": 0.30}},
    "Lorenzo Musetti": {"Hard": {"aces": 5.1, "return_1st": 0.31}, "Clay": {"aces": 3.8, "return_1st": 0.32}, "Grass": {"aces": 6.5, "return_1st": 0.29}},
    "Casper Ruud": {"Hard": {"aces": 6.2, "return_1st": 0.32}, "Clay": {"aces": 4.5, "return_1st": 0.34}, "Grass": {"aces": 7.0, "return_1st": 0.30}},
    "Andrey Rublev": {"Hard": {"aces": 9.2, "return_1st": 0.31}, "Clay": {"aces": 5.5, "return_1st": 0.29}, "Grass": {"aces": 10.5, "return_1st": 0.30}},
    "Arthur Fils": {"Hard": {"aces": 8.5, "return_1st": 0.30}, "Clay": {"aces": 4.2, "return_1st": 0.28}, "Grass": {"aces": 9.8, "return_1st": 0.29}},
    "Frances Tiafoe": {"Hard": {"aces": 9.0, "return_1st": 0.31}, "Clay": {"aces": 4.8, "return_1st": 0.29}, "Grass": {"aces": 10.2, "return_1st": 0.30}},
    "Tommy Paul": {"Hard": {"aces": 7.2, "return_1st": 0.34}, "Clay": {"aces": 3.8, "return_1st": 0.32}, "Grass": {"aces": 8.0, "return_1st": 0.33}},
    "Francisco Cerundolo": {"Hard": {"aces": 5.0, "return_1st": 0.30}, "Clay": {"aces": 4.0, "return_1st": 0.32}, "Grass": {"aces": 5.8, "return_1st": 0.28}},
    "Alejandro Tabilo": {"Hard": {"aces": 6.1, "return_1st": 0.29}, "Clay": {"aces": 5.2, "return_1st": 0.33}, "Grass": {"aces": 7.0, "return_1st": 0.27}},
    "Ugo Humbert": {"Hard": {"aces": 11.5, "return_1st": 0.30}, "Clay": {"aces": 5.5, "return_1st": 0.27}, "Grass": {"aces": 13.0, "return_1st": 0.29}},
    "Alexander Blockx": {"Hard": {"aces": 7.52, "return_1st": 0.31}, "Clay": {"aces": 3.10, "return_1st": 0.26}, "Grass": {"aces": 8.90, "return_1st": 0.29}},
    "Matteo Arnaldi": {"Hard": {"aces": 6.0, "return_1st": 0.30}, "Clay": {"aces": 3.9, "return_1st": 0.29}, "Grass": {"aces": 7.2, "return_1st": 0.28}},
    "Cameron Norrie": {"Hard": {"aces": 5.8, "return_1st": 0.33}, "Clay": {"aces": 3.5, "return_1st": 0.32}, "Grass": {"aces": 6.9, "return_1st": 0.31}},
    "Karen Khachanov": {"Hard": {"aces": 10.8, "return_1st": 0.30}, "Clay": {"aces": 6.0, "return_1st": 0.28}, "Grass": {"aces": 12.0, "return_1st": 0.29}},
    "Matteo Berrettini": {"Hard": {"aces": 14.5, "return_1st": 0.26}, "Clay": {"aces": 8.5, "return_1st": 0.24}, "Grass": {"aces": 16.8, "return_1st": 0.25}},
    "Jan-Lennard Struff": {"Hard": {"aces": 13.2, "return_1st": 0.27}, "Clay": {"aces": 7.8, "return_1st": 0.25}, "Grass": {"aces": 14.8, "return_1st": 0.26}},
    "Denis Shapovalov": {"Hard": {"aces": 11.0, "return_1st": 0.29}, "Clay": {"aces": 5.8, "return_1st": 0.27}, "Grass": {"aces": 12.5, "return_1st": 0.28}},
    "Stefanos Tsitsipas": {"Hard": {"aces": 8.2, "return_1st": 0.32}, "Clay": {"aces": 5.5, "return_1st": 0.30}, "Grass": {"aces": 9.5, "return_1st": 0.31}},
    "Hubert Hurkacz": {"Hard": {"aces": 15.6, "return_1st": 0.26}, "Clay": {"aces": 9.0, "return_1st": 0.24}, "Grass": {"aces": 18.0, "return_1st": 0.25}},
    
    # Joueurs classés de 51 à 100 & Spécialistes
    "Sebastian Baez": {"Hard": {"aces": 3.2, "return_1st": 0.34}, "Clay": {"aces": 2.5, "return_1st": 0.36}, "Grass": {"aces": 4.0, "return_1st": 0.32}},
    "Tallon Griekspoor": {"Hard": {"aces": 10.0, "return_1st": 0.29}, "Clay": {"aces": 5.0, "return_1st": 0.27}, "Grass": {"aces": 11.2, "return_1st": 0.28}},
    "Tomas Machac": {"Hard": {"aces": 7.5, "return_1st": 0.31}, "Clay": {"aces": 4.1, "return_1st": 0.29}, "Grass": {"aces": 8.8, "return_1st": 0.30}},
    "Fabian Marozsan": {"Hard": {"aces": 6.8, "return_1st": 0.30}, "Clay": {"aces": 3.9, "return_1st": 0.28}, "Grass": {"aces": 7.9, "return_1st": 0.29}},
    "Sebastian Korda": {"Hard": {"aces": 8.8, "return_1st": 0.32}, "Clay": {"aces": 4.5, "return_1st": 0.30}, "Grass": {"aces": 10.0, "return_1st": 0.31}},
    "Miomir Kecmanovic": {"Hard": {"aces": 5.9, "return_1st": 0.31}, "Clay": {"aces": 3.8, "return_1st": 0.30}, "Grass": {"aces": 6.8, "return_1st": 0.29}},
    "Marin Cilic": {"Hard": {"aces": 12.8, "return_1st": 0.28}, "Clay": {"aces": 7.0, "return_1st": 0.26}, "Grass": {"aces": 14.5, "return_1st": 0.27}},
    "Giovanni Mpetshi Perricard": {"Hard": {"aces": 19.1, "return_1st": 0.22}, "Clay": {"aces": 11.0, "return_1st": 0.20}, "Grass": {"aces": 21.5, "return_1st": 0.21}},
    "Adolfo Daniel Vallejo": {"Hard": {"aces": 5.0, "return_1st": 0.32}, "Clay": {"aces": 3.0, "return_1st": 0.35}, "Grass": {"aces": 5.8, "return_1st": 0.30}},
    "Marco Trungelliti": {"Hard": {"aces": 3.5, "return_1st": 0.33}, "Clay": {"aces": 2.1, "return_1st": 0.35}, "Grass": {"aces": 4.0, "return_1st": 0.31}}
}

# Liste exhaustive indicative pour couvrir le Top 100 ATP officiel
FULL_TOP_100_LIST = sorted(list(set(list(ATP_PLAYER_DATABASE.keys()) + [
    "Rafael Jodar", "Learner Tien", "Jakub Mensik", "Valentin Vacherot", "Luciano Darderi",
    "Brandon Nakashima", "Joao Fonseca", "Alejandro Davidovich Fokina", "Arthur Rinderknech",
    "Tomas Martin Etcheverry", "Zizou Bergs", "Ignacio Buse", "Arthur Fery", "Raphael Collignon",
    "Daniel Merida", "Alex Michelsen", "Mariano Navone", "Terence Atmane", "Jaume Munar",
    "Nuno Borges", "Thiago Agustin Tirante", "Juan Manuel Cerundolo", "Adrian Mannarino",
    "Luca Van Assche", "Yannick Hanfmann", "Quentin Halys", "Ethan Quinn", "Botic Van De Zandschulp",
    "Corentin Moutet", "Roman Andres Burruchaga", "Daniel Altmaier", "Martin Landaluce",
    "Kamil Majchrzak", "Vit Kopriva", "Pablo Carreno Busta", "Hamad Medjedovic", "Jenson Brooksby",
    "Alex Molcan", "Camilo Ugo Carabelli", "Jan Choinski", "Valentin Royer", "Jaime Faria", "Mattia Bellucci", "Marton Fucsovics", "Marcos Giron"
])))

DEFAULT_STATS = {"aces": 6.0, "return_1st": 0.30}

# ==============================================================================
# 2. INTERFACE UTILISATEUR (Sidebar)
# ==============================================================================
st.sidebar.header("⚙️ Paramètres du Match (Top 100)")

player_a = st.sidebar.selectbox("Joueur 1 (Serveur A)", FULL_TOP_100_LIST, index=FULL_TOP_100_LIST.index("Alexander Blockx") if "Alexander Blockx" in FULL_TOP_100_LIST else 0)
player_b = st.sidebar.selectbox("Joueur 2 (Serveur B)", FULL_TOP_100_LIST, index=FULL_TOP_100_LIST.index("Flavio Cobolli") if "Flavio Cobolli" in FULL_TOP_100_LIST else 1)

surface = st.sidebar.selectbox("Surface", ["Hard", "Clay", "Grass"])
multiplier = st.sidebar.slider("Multiplicateur de Vitesse du Tournoi", 0.5, 1.5, 1.18, 0.01)

line_book = st.sidebar.number_input("Ligne Bookmaker (Total Aces)", min_value=0.5, max_value=40.0, value=12.5, step=0.5)

# ==============================================================================
# 3. MOTEUR DE CALCUL PRÉDICTIF
# ==============================================================================
def get_stats(player, surf):
    if player in ATP_PLAYER_DATABASE and surf in ATP_PLAYER_DATABASE[player]:
        return ATP_PLAYER_DATABASE[player][surf]
    # Fallback intelligent pour les joueurs du Top 100 sans stats custom
    return DEFAULT_STATS

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
# 4. AFFICHAGE DES RÉSULTATS
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
    st.success(f"💡 **Recommandation du modèle :** Value potentielle détectée sur l'**Over {line_book}**.")
elif prob_under > 55.0:
    st.warning(f"💡 **Recommandation du modèle :** Value potentielle détectée sur l'**Under {line_book}**.")
else:
    st.info("💡 Match équilibré, la ligne du bookmaker est alignée avec les probabilités statistiques.")
