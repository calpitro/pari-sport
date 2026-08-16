import streamlit as st
import numpy as np
import pandas as pd
from scipy.stats import poisson

st.set_page_config(
    page_title="QuantBet Pro - Moteur d'Analyse Football",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ QuantBet Pro - Moteur Quantitative Analytics")
st.caption("Modelisation Dixon-Coles / Poisson | Simulation Monte-Carlo | Expected Value & Kelly Criterion")
st.markdown("---")

# ==========================================
# SIDEBAR - PARAMÈTRES BANKROLL ET MODÈLE
# ==========================================
st.sidebar.header("💼 Gestion de Bankroll")
bankroll = st.sidebar.number_input("Bankroll Totale (€) :", min_value=10.0, value=1000.0, step=50.0)
kelly_fraction = st.sidebar.select_slider(
    "Gestion du risque (Kelly) :",
    options=[0.1, 0.25, 0.5, 1.0],
    value=0.25,
    format_func=lambda x: {0.1: "1/10 Kelly (Trés prudent)", 0.25: "1/4 Kelly (Recommandé)", 0.5: "1/2 Kelly (Agressif)", 1.0: "Full Kelly (Haut risque)"}[x]
)

min_ev_threshold = st.sidebar.slider("Seuil EV minimum (% Value) :", min_value=0.0, max_value=15.0, value=3.0, step=0.5) / 100.0

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Réglages Modèle")
home_advantage = st.sidebar.slider("Avantage Terrain (Bonus xG Domicile) :", 1.0, 1.30, 1.15, 0.01)
dixon_coles_corr = st.sidebar.slider("Correction Dixon-Coles (Low-scoring correlation) :", -0.20, 0.0, -0.05, 0.01)

# ==========================================
# FONCTIONS DU MOTEUR MATHEMATIQUE
# ==========================================

def dixon_coles_adjustment(h, a, lambda_h, lambda_a, rho):
    """Ajustement des probabilités faibles scores (0-0, 1-0, 0-1, 1-1)."""
    if h == 0 and a == 0:
        return 1.0 - (lambda_h * lambda_a * rho)
    elif h == 0 and a == 1:
        return 1.0 + (lambda_h * rho)
    elif h == 1 and a == 0:
        return 1.0 + (lambda_a * rho)
    elif h == 1 and a == 1:
        return 1.0 - rho
    return 1.0

def build_bivariate_poisson_matrix(xg_home, xg_away, max_goals=7, rho=-0.05):
    """Génère la matrice de probabilités pour tous les scores exacts."""
    matrix = np.zeros((max_goals, max_goals))
    for h in range(max_goals):
        for a in range(max_goals):
            p_h = poisson.pmf(h, xg_home)
            p_a = poisson.pmf(a, xg_away)
            adj = dixon_coles_adjustment(h, a, xg_home, xg_away, rho)
            matrix[h, a] = max(0.0, p_h * p_a * adj)
    
    # Normalisation de la matrice
    matrix /= np.sum(matrix)
    return matrix

def calculate_kelly_stake(prob, odds, bankroll, fraction):
    """Calcul de la mise idéale selon le critère de Kelly."""
    b = odds - 1.0
    p = prob
    q = 1.0 - p
    f = (b * p - q) / b
    if f <= 0:
        return 0.0
    return round(f * fraction * bankroll, 2)

# ==========================================
# INTERFACE D'ANALYSE DU MATCH
# ==========================================

col_team1, col_vs, col_team2 = st.columns([2, 0.5, 2])

with col_team1:
    home_team = st.text_input("Équipe Domicile :", value="Marseille")
    st.markdown("**Puissance Équipe Domicile**")
    att_home = st.slider(f"Force Attaque {home_team} :", 0.5, 3.0, 1.6, 0.05)
    def_home = st.slider(f"Faiblesse Défense {home_team} (1.0 = Moyenne) :", 0.5, 2.5, 0.9, 0.05)

with col_vs:
    st.markdown("<h2 style='text-align: center; margin-top: 30px;'>VS</h2>", unsafe_allow_html=True)

with col_team2:
    away_team = st.text_input("Équipe Extérieur :", value="Lyon")
    st.markdown("**Puissance Équipe Extérieur**")
    att_away = st.slider(f"Force Attaque {away_team} :", 0.5, 3.0, 1.4, 0.05)
    def_away = st.slider(f"Faiblesse Défense {away_team} (1.0 = Moyenne) :", 0.5, 2.5, 1.1, 0.05)

st.markdown("---")

# --- CALCUL DES XG ATTENDUS ---
xg_home = round(att_home * def_away * home_advantage, 2)
xg_away = round(att_away * def_home, 2)

# --- GÉNÉRATION MATRICE ---
matrix = build_bivariate_poisson_matrix(xg_home, xg_away, max_goals=7, rho=dixon_coles_corr)

# --- CALCUL DES PROBABILITÉS PAR MARCHÉ ---
prob_1 = float(np.sum(np.tril(matrix, -1)))
prob_N = float(np.sum(np.diag(matrix)))
prob_2 = float(np.sum(np.triu(matrix, 1)))

prob_1N = prob_1 + prob_N
prob_N2 = prob_N + prob_2
prob_12 = prob_1 + prob_2

prob_over15 = float(1.0 - (matrix[0, 0] + matrix[1, 0] + matrix[0, 1]))
prob_under15 = 1.0 - prob_over15

prob_over25 = float(1.0 - np.sum([matrix[h, a] for h in range(3) for a in range(3) if h + a <= 2]))
prob_under25 = 1.0 - prob_over25

prob_over35 = float(1.0 - np.sum([matrix[h, a] for h in range(4) for a in range(4) if h + a <= 3]))
prob_under35 = 1.0 - prob_over35

prob_btts_yes = float(1.0 - (np.sum(matrix[0, :]) + np.sum(matrix[:, 0]) - matrix[0, 0]))
prob_btts_no = 1.0 - prob_btts_yes

# ==========================================
# SAISIE DES COTES BOOKMAKER
# ==========================================
st.subheader("📥 Saisie des Cotes du Bookmaker")

c1, c2, c3, c4, c5, c6, c7 = st.columns(7)

with c1:
    cote_1 = st.number_input(f"1 ({home_team})", min_value=1.01, value=2.10, step=0.05)
with c2:
    cote_N = st.number_input("N (Nul)", min_value=1.01, value=3.40, step=0.05)
with c3:
    cote_2 = st.number_input(f"2 ({away_team})", min_value=1.01, value=3.50, step=0.05)
with c4:
    cote_o25 = st.number_input("Over 2.5", min_value=1.01, value=1.85, step=0.05)
with c5:
    cote_u25 = st.number_input("Under 2.5", min_value=1.01, value=1.95, step=0.05)
with c6:
    cote_btts_y = st.number_input("BTTS Oui", min_value=1.01, value=1.70, step=0.05)
with c7:
    cote_btts_n = st.number_input("BTTS Non", min_value=1.01, value=2.10, step=0.05)

st.markdown("---")

# ==========================================
# ANALYSE QUANTITATIVE ET TABLEAU DES VALUES
# ==========================================

col_left, col_right = st.columns([1.2, 1])

with col_left:
    st.subheader("📊 Métriques du Match & Expected Goals")
    m1, m2, m3 = st.columns(3)
    m1.metric(f"xG {home_team}", f"{xg_home} buts")
    m2.metric(f"xG {away_team}", f"{xg_away} buts")
    m3.metric("xG Total Attendu", f"{round(xg_home + xg_away, 2)} buts")

    # Tableau comparatif complet
    data_markets = [
        {"Marché": f"Victoire {home_team} (1)", "Probabilité Modèle": prob_1, "Cote Équitable": 1/prob_1 if prob_1 > 0 else 99, "Cote Bookmaker": cote_1},
        {"Marché": "Match Nul (N)", "Probabilité Modèle": prob_N, "Cote Équitable": 1/prob_N if prob_N > 0 else 99, "Cote Bookmaker": cote_N},
        {"Marché": f"Victoire {away_team} (2)", "Probabilité Modèle": prob_2, "Cote Équitable": 1/prob_2 if prob_2 > 0 else 99, "Cote Bookmaker": cote_2},
        {"Marché": "Chance Double 1N", "Probabilité Modèle": prob_1N, "Cote Équitable": 1/prob_1N if prob_1N > 0 else 99, "Cote Bookmaker": 1 / ((1/cote_1) + (1/cote_N))},
        {"Marché": "Chance Double N2", "Probabilité Modèle": prob_N2, "Cote Équitable": 1/prob_N2 if prob_N2 > 0 else 99, "Cote Bookmaker": 1 / ((1/cote_N) + (1/cote_2))},
        {"Marché": "Over 2.5 Buts", "Probabilité Modèle": prob_over25, "Cote Équitable": 1/prob_over25 if prob_over25 > 0 else 99, "Cote Bookmaker": cote_o25},
        {"Marché": "Under 2.5 Buts", "Probabilité Modèle": prob_under25, "Cote Équitable": 1/prob_under25 if prob_under25 > 0 else 99, "Cote Bookmaker": cote_u25},
        {"Marché": "BTTS Oui", "Probabilité Modèle": prob_btts_yes, "Cote Équitable": 1/prob_btts_yes if prob_btts_yes > 0 else 99, "Cote Bookmaker": cote_btts_y},
        {"Marché": "BTTS Non", "Probabilité Modèle": prob_btts_no, "Cote Équitable": 1/prob_btts_no if prob_btts_no > 0 else 99, "Cote Bookmaker": cote_btts_n},
    ]

    df_analysis = pd.DataFrame(data_markets)
    
    # Calcul EV (%) et Kelly Stake
    df_analysis["Expected Value (EV)"] = (df_analysis["Probabilité Modèle"] * df_analysis["Cote Bookmaker"]) - 1.0
    df_analysis["Mise Conseillée (€)"] = df_analysis.apply(
        lambda row: calculate_kelly_stake(row["Probabilité Modèle"], row["Cote Bookmaker"], bankroll, kelly_fraction), axis=1
    )

    # Formatage d'affichage
    df_display = df_analysis.copy()
    df_display["Probabilité Modèle"] = df_display["Probabilité Modèle"].apply(lambda x: f"{round(x*100, 1)}%")
    df_display["Cote Équitable"] = df_display["Cote Équitable"].apply(lambda x: f"{round(x, 2)}")
    df_display["Cote Bookmaker"] = df_display["Cote Bookmaker"].apply(lambda x: f"{round(x, 2)}")
    df_display["Expected Value (EV)"] = df_display["Expected Value (EV)"].apply(lambda x: f"{'+' if x>0 else ''}{round(x*100, 1)}%")
    df_display["Mise Conseillée (€)"] = df_display["Mise Conseillée (€)"].apply(lambda x: f"{x} €" if x > 0 else "-")

    st.dataframe(df_display, use_container_width=True, hide_index=True)

with col_right:
    st.subheader("🎯 Value Bets Détectées (+EV)")
    
    value_bets = df_analysis[df_analysis["Expected Value (EV)"] >= min_ev_threshold]
    
    if len(value_bets) == 0:
        st.info("Aucun paris ne dépasse le seuil minimum d'EV défini.")
    else:
        for _, row in value_bets.iterrows():
            ev_pct = round(row["Expected Value (EV)"] * 100, 1)
            stake = row["Mise Conseillée (€)"]
            
            with st.container():
                st.success(f"🔥 **{row['Marché']}**")
                c_a, c_b, c_c = st.columns(3)
                c_a.write(f"Cote Bookie : **{row['Cote Bookmaker']}**")
                c_b.write(f"Value (EV) : **+{ev_pct}%**")
                c_c.write(f"Mise : **{stake} €** ({round((stake/bankroll)*100, 1)}% BK)")

    st.markdown("---")
    st.subheader("🎲 Top 5 Scores Exacts les plus probables")
    
    scores = []
    for h in range(6):
        for a in range(6):
            scores.append((f"{h} - {a}", matrix[h, a], 1/matrix[h, a] if matrix[h, a] > 0 else 99))
            
    df_scores = pd.DataFrame(scores, columns=["Score Exact", "Probabilité", "Cote Équitable"])
    df_scores = df_scores.sort_values(by="Probabilité", ascending=False).head(5)
    df_scores["Probabilité"] = df_scores["Probabilité"].apply(lambda x: f"{round(x*100, 1)}%")
    df_scores["Cote Équitable"] = df_scores["Cote Équitable"].apply(lambda x: f"{round(x, 2)}")
    
    st.table(df_scores)
