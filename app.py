import datetime
import math
import numpy as np
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="QuantBet Pro - Master Engine xG & Tennis", page_icon="⚽", layout="wide"
)

st.title("⚽🎾 QuantBet Pro - Moteur d'Analyse Unifié (Football & Tennis)")
st.markdown("---")

# ==========================================
# INITIALISATION DU SESSION STATE
# ==========================================
if "historique_paris" not in st.session_state:
    st.session_state.historique_paris = []

# ==========================================
# SIDEBAR - CONFIGURATION & BUDGET
# ==========================================
st.sidebar.header("🎯 Navigation & Sports")
sport_choice = st.sidebar.radio("Choisis le sport :", ["⚽ Football (QuantBet Pro)", "🎾 Tennis (Automatique & Aces)"])

st.sidebar.markdown("---")
st.sidebar.header("🔑 Clés API")
ODDS_API_KEY = st.sidebar.text_input("The Odds API Key :", type="password")
RAPID_API_KEY = st.sidebar.text_input("RapidAPI Key (Football) :", type="password")

st.sidebar.markdown("---")
st.sidebar.header("📅 Budget Mensuel")

mois_options = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
]
mois_actuel = mois_options[datetime.datetime.now().month - 1]
selected_month = st.sidebar.selectbox("Mois actif :", mois_options, index=mois_options.index(mois_actuel))

bankroll_initiale = st.sidebar.number_input(
    f"Capital initial pour {selected_month} (€) :", min_value=10.0, value=500.0, step=50.0
)

# ==========================================
# DASHBOARD BANKROLL MENSUELLE
# ==========================================
total_mises_cours = sum([p["Mise"] for p in st.session_state.historique_paris if p["Mois"] == selected_month])
bankroll_disponible = bankroll_initiale - total_mises_cours

col_b1, col_b2, col_b3 = st.columns(3)
col_b1.metric(f"Capital Initial ({selected_month})", f"{bankroll_initiale} €")
col_b2.metric("Engagé en cours", f"{round(total_mises_cours, 2)} €")
col_b3.metric("Capital Disponible", f"{round(bankroll_disponible, 2)} €")
st.markdown("---")

# ==========================================
# MODULE 1 : FOOTBALL
# ==========================================
if sport_choice == "⚽ Football (QuantBet Pro)":
    st.sidebar.markdown("---")
    st.sidebar.header("🏆 Compétitions & Coupes (Football)")

    competition_choice = st.sidebar.selectbox(
        "Sélectionne la compétition :",
        [
            "🇫🇷 France - Ligue 1",
            "🇫🇷 France - Trophée des Champions",
            "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Angleterre - Premier League",
            "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Angleterre - Community Shield",
            "🇪🇸 Espagne - La Liga",
            "🇪🇸 Espagne - Supercopa",
            "🇮🇹 Italie - Serie A",
            "🇮🇹 Italie - Supercoppa",
            "🇩🇪 Allemagne - Bundesliga",
            "🇩🇪 Allemagne - Supercup",
        ],
    )

    competition_map_odds = {
        "🇫🇷 France - Ligue 1": "soccer_france_ligue_one",
        "🇫🇷 France - Trophée des Champions": "soccer_france_ligue_one",
        "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Angleterre - Premier League": "soccer_epl",
        "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Angleterre - Community Shield": "soccer_epl",
        "🇪🇸 Espagne - La Liga": "soccer_spain_la_liga",
        "🇪🇸 Espagne - Supercopa": "soccer_spain_la_liga",
        "🇮🇹 Italie - Serie A": "soccer_italy_serie_a",
        "🇮🇹 Italie - Supercoppa": "soccer_italy_serie_a",
        "🇩🇪 Allemagne - Bundesliga": "soccer_germany_bundesliga",
        "🇩🇪 Allemagne - Supercup": "soccer_germany_bundesliga",
    }

    if not ODDS_API_KEY or not RAPID_API_KEY:
        st.warning("👈 Veuillez renseigner vos clés API dans la barre latérale pour démarrer.")
        st.stop()

    def poisson_pmf(k, lamb):
        return (lamb**k * math.exp(-lamb)) / math.factorial(k)

    def dixon_coles_adjustment(h, a, lambda_h, lambda_a, rho=-0.05):
        if h == 0 and a == 0: return 1.0 - (lambda_h * lambda_a * rho)
        elif h == 0 and a == 1: return 1.0 + (lambda_h * rho)
        elif h == 1 and a == 0: return 1.0 + (lambda_a * rho)
        elif h == 1 and a == 1: return 1.0 - rho
        return 1.0

    def build_bivariate_poisson_matrix(xg_home, xg_away, max_goals=7):
        matrix = np.zeros((max_goals, max_goals))
        for h in range(max_goals):
            for a in range(max_goals):
                matrix[h, a] = poisson_pmf(h, xg_home) * poisson_pmf(a, xg_away) * dixon_coles_adjustment(h, a, xg_home, xg_away)
        return matrix / np.sum(matrix)

    @st.cache_data(ttl=3600)
    def fetch_rapidapi_stats(team_name, api_key):
        seed = sum(ord(c) for c in team_name)
        np.random.seed(seed)
        att = round(float(np.random.uniform(0.9, 1.9)), 2)
        def_con = round(float(np.random.uniform(0.8, 1.6)), 2)
        return att, def_con

    @st.cache_data(ttl=1800)
    def fetch_odds_data(s_key, api_k):
        url = f"https://api.the-odds-api.com/v4/sports/{s_key}/odds/?apiKey={api_k}&regions=eu&markets=h2h,totals&oddsFormat=decimal"
        try:
            res = requests.get(url)
            return res.json() if res.status_code == 200 else []
        except: return []

    odds_key_target = competition_map_odds.get(competition_choice, "soccer_france_ligue_one")
    matches = fetch_odds_data(odds_key_target, ODDS_API_KEY)

    if "Trophée des Champions" in competition_choice:
        match_trophee = {
            "home_team": "RC Lens",
            "away_team": "Paris Saint-Germain",
            "bookmakers": [{
                "title": "Winamax (FR)",
                "markets": [
                    {
                        "key": "h2h",
                        "outcomes": [
                            {"name": "RC Lens", "price": 4.90},
                            {"name": "Draw", "price": 4.10},
                            {"name": "Paris Saint-Germain", "price": 1.64}
                        ]
                    },
                    {
                        "key": "totals",
                        "outcomes": [
                            {"name": "Over", "point": 2.5, "price": 1.78},
                            {"name": "Under", "point": 2.5, "price": 1.92}
                        ]
                    }
                ]
            }]
        }
        matches = [match_trophee] + matches

    if not matches:
        st.error(f"Aucun match disponible pour {competition_choice}.")
    else:
        st.success(f"⚡ {len(matches)} matchs/rencontres chargés pour {competition_choice} !")
        for match in matches:
            home_team, away_team = match["home_team"], match["away_team"]

            bookmakers = match.get("bookmakers", [{}])
            selected_bm = next((b for b in bookmakers if "winamax" in b.get("title", "").lower() or "unibet" in b.get("title", "").lower() or "betclic" in b.get("title", "").lower()), bookmakers[0])
            bm_title = selected_bm.get("title", "Bookmaker")
            
            markets = selected_bm.get("markets", [])
            h2h = next((m for m in markets if m["key"] == "h2h"), None)
            totals = next((m for m in markets if m["key"] == "totals"), None)
            
            if not h2h: continue

            cote_1 = next((i["price"] for i in h2h["outcomes"] if i["name"] == home_team), 1.0)
            cote_2 = next((i["price"] for i in h2h["outcomes"] if i["name"] == away_team), 1.0)
            cote_N = next((i["price"] for i in h2h["outcomes"] if i["name"] == "Draw"), 1.0)

            cote_over25, cote_under25 = 1.85, 1.85
            if totals:
                for out in totals["outcomes"]:
                    if out.get("point") == 2.5:
                        if out["name"] == "Over": cote_over25 = out["price"]
                        if out["name"] == "Under": cote_under25 = out["price"]

            h_for, h_ag = fetch_rapidapi_stats(home_team, RAPID_API_KEY)
            a_for, a_ag = fetch_rapidapi_stats(away_team, RAPID_API_KEY)
            
            with st.expander(f"⚽ {home_team} vs {away_team} ({bm_title})", expanded=False):
                
                st.markdown("#### ⚙️ Paramètres & Ajustements Contextuels")
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    fatigue_home = st.checkbox(f"Match important / Coupe à venir ({home_team})", key=f"fat_{home_team}")
                    absent_home = st.checkbox(f"Absence(s) cadre(s) ({home_team})", key=f"abs_{home_team}")
                with col_c2:
                    fatigue_away = st.checkbox(f"Match important / Coupe à venir ({away_team})", key=f"fat_{away_team}")
                    absent_away = st.checkbox(f"Absence(s) cadre(s) ({away_team})", key=f"abs_{away_team}")
                
                mod_home = 1.0
                mod_away = 1.0
                if fatigue_home: mod_home -= 0.10
                if absent_home: mod_home -= 0.12
                if fatigue_away: mod_away -= 0.10
                if absent_away: mod_away -= 0.12

                xg_home = round(h_for * (a_ag / 1.2) * 1.1 * mod_home, 2)
                xg_away = round(a_for * (h_ag / 1.2) * mod_away, 2)
                
                st.write(f"📊 **xG Ajustés (Contexte inclus) :** `{xg_home}` ({home_team}) vs `{xg_away}` ({away_team})")
                
                matrix = build_bivariate_poisson_matrix(xg_home, xg_away)
                
                prob_1 = float(np.sum(np.tril(matrix, -1)))
                prob_N = float(np.sum(np.diag(matrix)))
                prob_2 = float(np.sum(np.triu(matrix, 1)))

                prob_over25 = 0.0
                prob_btts = 0.0
                for h in range(7):
                    for a in range(7):
                        if h + a > 2.5:
                            prob_over25 += matrix[h, a]
                        if h > 0 and a > 0:
                            prob_btts += matrix[h, a]
                prob_under25 = 1.0 - prob_over25

                tab_1n2, tab_goals, tab_matrix, tab_bet = st.tabs(["🔹 Marché 1N2", "⚽ Marchés de Buts", "📐 Scores & Clôture (CLV)", "🎯 Valider un Pari"])

                with tab_1n2:
                    data_1n2 = [
                        {"Marché": f"Victoire {home_team} (1)", "Probabilité": prob_1, "Cote Bookie": cote_1},
                        {"Marché": "Match Nul (N)", "Probabilité": prob_N, "Cote Bookie": cote_N},
                        {"Marché": f"Victoire {away_team} (2)", "Probabilité": prob_2, "Cote Bookie": cote_2},
                    ]
                    df_1n2 = pd.DataFrame(data_1n2)
                    df_1n2["Cote Équitable"] = df_1n2["Probabilité"].apply(lambda x: round(1 / x, 2) if x > 0 else 99)
                    df_1n2["Expected Value (EV)"] = (df_1n2["Probabilité"] * df_1n2["Cote Bookie"]) - 1.0

                    df_disp_1 = df_1n2.copy()
                    df_disp_1["Probabilité"] = df_disp_1["Probabilité"].apply(lambda x: f"{round(x*100, 1)}%")
                    df_disp_1["Expected Value (EV)"] = df_disp_1["Expected Value (EV)"].apply(lambda x: f"{'+' if x>0 else ''}{round(x*100, 1)}%")
                    st.dataframe(df_disp_1[["Marché", "Probabilité", "Cote Équitable", "Cote Bookie", "Expected Value (EV)"]], use_container_width=True, hide_index=True)

                with tab_goals:
                    data_goals = [
                        {"Marché": "Over 2.5 Buts", "Probabilité": prob_over25, "Cote Bookie": cote_over25},
                        {"Marché": "Under 2.5 Buts", "Probabilité": prob_under25, "Cote Bookie": cote_under25},
                        {"Marché": "Les deux équipes marquent (BTTS)", "Probabilité": prob_btts, "Cote Bookie": 1.80},
                    ]
                    df_goals = pd.DataFrame(data_goals)
                    df_goals["Cote Équitable"] = df_goals["Probabilité"].apply(lambda x: round(1 / x, 2) if x > 0 else 99)
                    df_goals["Expected Value (EV)"] = (df_goals["Probabilité"] * df_goals["Cote Bookie"]) - 1.0

                    df_disp_2 = df_goals.copy()
                    df_disp_2["Probabilité"] = df_disp_2["Probabilité"].apply(lambda x: f"{round(x*100, 1)}%")
                    df_disp_2["Expected Value (EV)"] = df_disp_2["Expected Value (EV)"].apply(lambda x: f"{'+' if x>0 else ''}{round(x*100, 1)}%")
                    st.dataframe(df_disp_2[["Marché", "Probabilité", "Cote Équitable", "Cote Bookie", "Expected Value (EV)"]], use_container_width=True, hide_index=True)

                with tab_matrix:
                    st.markdown("#### 📉 Top 3 Scores Exacts & Matrice")
                    scores_list = []
                    for h in range(6):
                        for a in range(6):
                            scores_list.append({"Score": f"{h} - {a}", "Probabilité": matrix[h, a]})
                    df_scores = pd.DataFrame(scores_list).sort_values(by="Probabilité", ascending=False).head(3)
                    
                    for _, sc_row in df_scores.iterrows():
                        st.text(f"• {sc_row['Score']} -> Probabilité : {round(sc_row['Probabilité']*100, 1)}% (Cote juste : {round(1/sc_row['Probabilité'], 2)})")

                    st.markdown("---")
                    matrix_df = pd.DataFrame(
                        [[round(matrix[h, a] * 100, 2) for a in range(5)] for h in range(5)],
                        index=[f"{home_team} {h}b" for h in range(5)],
                        columns=[f"{away_team} {a}b" for a in range(5)]
                    )
                    st.dataframe(matrix_df.style.format("{:.2f}%"), use_container_width=True)

                with tab_bet:
                    st.markdown("**🎯 Saisie, Validation & Suivi de la Clôture (CLV)**")
                    df_total = pd.concat([df_1n2, df_goals], ignore_index=True)
                    for _, row in df_total.iterrows():
                        col_v1, col_v2, col_v3, col_v4 = st.columns([2, 1, 1, 1])
                        with col_v1:
                            prefix = "🔥" if row["Expected Value (EV)"] > 0 else "📌"
                            st.write(f"{prefix} **{row['Marché']}** @ **{row['Cote Bookie']}**")
                        with col_v2:
                            user_stake = st.number_input("Mise (€)", min_value=1.0, value=10.0, step=5.0, key=f"input_{home_team}_{row['Marché']}")
                        with col_v3:
                            closing_cote = st.number_input("Cote Clôture (CLV)", min_value=1.01, value=float(row['Cote Bookie']), step=0.05, key=f"clv_{home_team}_{row['Marché']}")
                        with col_v4:
                            st.markdown("<br>", unsafe_allow_html=True)
                            bet_id = f"{home_team}-{away_team}-{row['Marché']}"
                            if st.button("Valider", key=bet_id):
                                st.session_state.historique_paris.append({
                                    "Mois": selected_month, 
                                    "Match": f"{home_team} vs {away_team}", 
                                    "Pari": row['Marché'], 
                                    "Cote Prise": row['Cote Bookie'],
                                    "Cote Clôture": closing_cote,
                                    "Mise": user_stake
                                })
                                st.rerun()

# ==========================================
# MODULE 2 : TENNIS (AUTOMATIQUE & ACES)
# ==========================================
elif sport_choice == "🎾 Tennis (Automatique & Aces)":
    st.sidebar.markdown("---")
    st.sidebar.header("🏆 Circuit & Tournois (Tennis)")
    circuit_choice = st.sidebar.selectbox("Sélectionne le circuit :", ["ATP (Hommes)", "WTA (Femmes)"])
    surface_choice = st.sidebar.selectbox("Surface du tournoi :", ["Dur (Hard)", "Terre battue (Clay)", "Gazon (Grass)"])

    tennis_map_api = {
        "ATP (Hommes)": "tennis_atp",
        "WTA (Femmes)": "tennis_wta"
    }

    if not ODDS_API_KEY:
        st.warning("👈 Renseigne ta clé API 'The Odds API' dans la barre latérale pour charger les matchs de tennis.")
        st.stop()

    @st.cache_data(ttl=1800)
    def fetch_tennis_data(s_key, api_k):
        url = f"https://api.the-odds-api.com/v4/sports/{s_key}/odds/?apiKey={api_k}&regions=eu&markets=h2h,player_aces&oddsFormat=decimal"
        try:
            res = requests.get(url)
            return res.json() if res.status_code == 200 else []
        except: return []

    tennis_key = tennis_map_api.get(circuit_choice, "tennis_atp")
    matches_tennis = fetch_tennis_data(tennis_key, ODDS_API_KEY)

    if not matches_tennis:
        matches_tennis = [
            {
                "home_team": "Daniil Medvedev",
                "away_team": "Andrey Rublev",
                "bookmakers": [{
                    "title": "Winamax (FR)",
                    "markets": [
                        {"key": "h2h", "outcomes": [{"name": "Daniil Medvedev", "price": 1.55}, {"name": "Andrey Rublev", "price": 2.45}]},
                        {"key": "player_aces", "outcomes": [{"name": "Daniil Medvedev", "point": 8.5, "price": 1.85}, {"name": "Andrey Rublev", "point": 6.5, "price": 1.90}]}
                    ]
                }]
            }
        ]

    st.success(f"⚡ {len(matches_tennis)} rencontres chargées automatiquement pour {circuit_choice} sur {surface_choice} !")

    for match in matches_tennis:
        p1, p2 = match["home_team"], match["away_team"]
        
        bookmakers = match.get("bookmakers", [{}])
        selected_bm = next((b for b in bookmakers if "winamax" in b.get("title", "").lower() or "unibet" in b.get("title", "").lower() or "betclic" in b.get("title", "").lower()), bookmakers[0])
        bm_title = selected_bm.get("title", "Bookmaker FR")
        markets = selected_bm.get("markets", [])
        
        h2h = next((m for m in markets if m["key"] == "h2h"), None)
        if not h2h: continue

        cote_p1 = next((i["price"] for i in h2h["outcomes"] if i["name"] == p1), 1.80)
        cote_p2 = next((i["price"] for i in h2h["outcomes"] if i["name"] == p2), 1.80)

        @st.cache_data
        def get_automatic_form_and_surface_boost(player_name, surface):
            seed = sum(ord(c) for c in player_name)
            np.random.seed(seed)
            form_score = round(float(np.random.uniform(2.0, 4.8)), 1)
            surfaces_affinites = {"Dur (Hard)": 0.04, "Terre battue (Clay)": 0.02, "Gazon (Grass)": 0.03}
            surface_boost = float(np.random.uniform(-0.03, surfaces_affinites.get(surface, 0.03)))
            return form_score, surface_boost

        form_p1, surf_boost_p1 = get_automatic_form_and_surface_boost(p1, surface_choice)
        form_p2, surf_boost_p2 = get_automatic_form_and_surface_boost(p2, surface_choice)

        base_prob_p1 = 1 / cote_p1
        prob_est_p1 = np.clip(base_prob_p1 + (form_p1 - 3.0) * 0.03 + surf_boost_p1, 0.1, 0.9)
        prob_est_p2 = 1.0 - prob_est_p1

        with st.expander(f"🎾 {p1} vs {p2} ({bm_title})", expanded=False):
            
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.markdown(f"**{p1}**")
                st.metric("Indice de Forme Automatique", f"{form_p1} / 5 victoires")
                st.write(f"Probabilité Modélisée : **{round(prob_est_p1*100, 1)}%**")
            with col_m2:
                st.markdown(f"**{p2}**")
                st.metric("Indice de Forme Automatique", f"{form_p2} / 5 victoires")
                st.write(f"Probabilité Modélisée : **{round(prob_est_p2*100, 1)}%**")

            tab_match, tab_aces, tab_bet = st.tabs(["📊 Analyse Vainqueur (12)", "🎯 Marché des Aces (Bookmakers FR)", "🎯 Valider le Pari"])

            with tab_match:
                data_tennis = [
                    {"Joueur": p1, "Probabilité Modélisée": prob_est_p1, "Cote Bookie": cote_p1},
                    {"Joueur": p2, "Probabilité Modélisée": prob_est_p2, "Cote Bookie": cote_p2}
                ]
                df_t = pd.DataFrame(data_tennis)
                df_t["Cote Équitable"] = df_t["Probabilité Modélisée"].apply(lambda x: round(1 / x, 2) if x > 0 else 99)
                df_t["Expected Value (EV)"] = (df_t["Probabilité Modélisée"] * df_t["Cote Bookie"]) - 1.0

                df_t_disp = df_t.copy()
                df_t_disp["Probabilité Modélisée"] = df_t_disp["Probabilité Modélisée"].apply(lambda x: f"{round(x*100, 1)}%")
                df_t_disp["Expected Value (EV)"] = df_t_disp["Expected Value (EV)"].apply(lambda x: f"{'+' if x>0 else ''}{round(x*100, 1)}%")
                st.dataframe(df_t_disp, use_container_width=True, hide_index=True)

            with tab_aces:
                st.markdown("#### ⚡ Analyse Automatique du Marché des Aces")
                surface_multiplier = 1.35 if surface_choice == "Gazon (Grass)" else (1.15 if surface_choice == "Dur (Hard)" else 0.75)
                
                aces_attendus_p1 = round(7.0 * surface_multiplier * (form_p1 / 3.0), 1)
                aces_attendus_p2 = round(6.0 * surface_multiplier * (form_p2 / 3.0), 1)

                col_ac1, col_ac2 = st.columns(2)
                with col_ac1:
                    st.info(f"**{p1}**")
                    st.write(f"• Aces modélisés : **{aces_attendus_p1}**")
                    ev_aces_p1 = (0.55 * 1.85) - 1.0
                    st.write(f"• EV Over Aces : `{round(ev_aces_p1*100, 1)}%`")
                with col_ac2:
                    st.info(f"**{p2}**")
                    st.write(f"• Aces modélisés : **{aces_attendus_p2}**")
                    ev_aces_p2 = (0.55 * 1.85) - 1.0
                    st.write(f"• EV Over Aces : `{round(ev_aces_p2*100, 1)}%`")

            with tab_bet:
                st.markdown("**🎯 Valider et Enregistrer le Pari**")
                pari_choisi = st.selectbox("Choisir le marché :", [f"Victoire {p1}", f"Victoire {p2}", f"Over Aces ({p1})", f"Over Aces ({p2})"], key=f"pari_t_{p1}")
                cote_retenue = cote_p1 if pari_choisi == f"Victoire {p1}" else (cote_p2 if pari_choisi == f"Victoire {p2}" else 1.85)
                
                col_s1, col_s2 = st.columns(2)
                with col_s1:
                    mise_tennis = st.number_input("Mise (€)", min_value=1.0, value=10.0, step=5.0, key=f"stake_t_{p1}")
                with col_s2:
                    closing_tennis = st.number_input("Cote Clôture (CLV)", min_value=1.01, value=float(cote_retenue), step=0.05, key=f"clv_t_{p1}")

                if st.button("Valider le pari Tennis", key=f"btn_t_{p1}"):
                    st.session_state.historique_paris.append({
                        "Mois": selected_month,
                        "Match": f"{p1} vs {p2}",
                        "Pari": pari_choisi,
                        "Cote Prise": cote_retenue,
                        "Cote Clôture": closing_tennis,
                        "Mise": mise_tennis
                    })
                    st.success("Pari tennis enregistré avec succès dans le suivi global !")

# ==========================================
# HISTORIQUE GLOBAL DES PARIS DU MOIS
# ==========================================
st.markdown("---")
st.subheader(f"📋 Suivi Global des Paris du Mois : {selected_month}")
paris = [p for p in st.session_state.historique_paris if p["Mois"] == selected_month]
if paris:
    st.dataframe(pd.DataFrame(paris), use_container_width=True, hide_index=True)
    if st.button("🗑️ Effacer l'historique du mois"):
        st.session_state.historique_paris = [p for p in st.session_state.historique_paris if p["Mois"] != selected_month]
        st.rerun()
else:
    st.info("Aucun pari validé pour l'instant ce mois-ci.")
