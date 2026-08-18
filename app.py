import numpy as np
from scipy.stats import poisson

# ==============================================================================
# 1. BASE DE DONNÉES COMPLÈTE ATP (Joueurs, Surfaces, Aces & Retours)
# ==============================================================================
ATP_PLAYER_DATABASE = {
    # Top Joueurs & Cadres du Circuit
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
    
    # Joueurs du contexte actif (Blockx, Lehecka, Tabilo, Cobolli, Paul, Fils, etc.)
    "Alexander Blockx": {"Hard": {"aces": 7.52, "return_1st": 0.31}, "Clay": {"aces": 3.10, "return_1st": 0.26}, "Grass": {"aces": 8.90, "return_1st": 0.29}},
    "Jiri Lehecka": {"Hard": {"aces": 10.3, "return_1st": 0.32}, "Clay": {"aces": 4.5, "return_1st": 0.28}, "Grass": {"aces": 11.5, "return_1st": 0.30}},
    "Alejandro Tabilo": {"Hard": {"aces": 6.1, "return_1st": 0.29}, "Clay": {"aces": 5.2, "return_1st": 0.33}, "Grass": {"aces": 7.0, "return_1st": 0.27}},
    "Flavio Cobolli": {"Hard": {"aces": 4.8, "return_1st": 0.30}, "Clay": {"aces": 3.5, "return_1st": 0.31}, "Grass": {"aces": 5.5, "return_1st": 0.28}},
    "Arthur Fils": {"Hard": {"aces": 8.5, "return_1st": 0.30}, "Clay": {"aces": 4.2, "return_1st": 0.28}, "Grass": {"aces": 9.8, "return_1st": 0.29}},
    "Tommy Paul": {"Hard": {"aces": 7.2, "return_1st": 0.34}, "Clay": {"aces": 3.8, "return_1st": 0.32}, "Grass": {"aces": 8.0, "return_1st": 0.33}},
    "Adolfo Daniel Vallejo": {"Hard": {"aces": 5.0, "return_1st": 0.32}, "Clay": {"aces": 3.0, "return_1st": 0.35}, "Grass": {"aces": 5.8, "return_1st": 0.30}},
    "Marco Trungelliti": {"Hard": {"aces": 3.5, "return_1st": 0.33}, "Clay": {"aces": 2.1, "return_1st": 0.35}, "Grass": {"aces": 4.0, "return_1st": 0.31}}
}

# Valeur par défaut si un joueur n'est pas explicitement dans le dictionnaire
DEFAULT_PLAYER_STATS = {"aces": 6.0, "return_1st": 0.30}

# ==============================================================================
# 2. CALENDRIER ATP ET FACTEURS DE VITESSE DE SURFACE (Speed Ratings)
# ==============================================================================
ATP_TOURNAMENTS_CALENDAR = {
    "Grand Slams": {
        "Australian Open": {"surface": "Hard", "multiplier": 1.11},
        "Roland Garros": {"surface": "Clay", "multiplier": 0.65},
        "Wimbledon": {"surface": "Grass", "multiplier": 1.12},
        "US Open": {"surface": "Hard", "multiplier": 0.98}
    },
    "Masters 1000": {
        "Indian Wells": {"surface": "Hard", "multiplier": 1.16},
        "Miami": {"surface": "Hard", "multiplier": 1.18},
        "Monte-Carlo": {"surface": "Clay", "multiplier": 0.55},
        "Madrid": {"surface": "Clay", "multiplier": 0.88},
        "Rome": {"surface": "Clay", "multiplier": 0.65},
        "Montreal / Cincinnati": {"surface": "Hard", "multiplier": 1.18}, # Ex: Cincinnati
        "Shanghai": {"surface": "Hard", "multiplier": 1.11},
        "Paris Bercy": {"surface": "Hard", "multiplier": 0.94}
    },
    "ATP 500 & 250": {
        "Standard Hard Outdoor/Indoor": {"surface": "Hard", "multiplier": 1.05},
        "Standard Clay": {"surface": "Clay", "multiplier": 0.75},
        "Standard Grass": {"surface": "Grass", "multiplier": 1.15}
    }
}

# ==============================================================================
# 3. MOTEUR DE CALCUL PRÉDICTIF (Aces & Lignes Over/Under)
# ==============================================================================
def get_player_data(player_name, surface):
    if player_name in ATP_PLAYER_DATABASE and surface in ATP_PLAYER_DATABASE[player_name]:
        return ATP_PLAYER_DATABASE[player_name][surface]
    return DEFAULT_PLAYER_STATS

def calculate_match_aces(player_a, player_b, surface, tournament_name, category="Masters 1000"):
    """
    Calcule l'espérance mathématique d'aces pour chaque joueur et le total combiné.
    """
    # Recherche du multiplicateur de tournoi
    multiplier = 1.0
    if category in ATP_TOURNAMENTS_CALENDAR:
        if tournament_name in ATP_TOURNAMENTS_CALENDAR[category]:
            multiplier = ATP_TOURNAMENTS_CALENDAR[category][tournament_name]["multiplier"]
        else:
            # Valeur par défaut selon la surface
            multiplier = 1.05 if surface == "Hard" else (1.15 if surface == "Grass" else 0.75)

    stats_a = get_player_data(player_a, surface)
    stats_b = get_player_data(player_b, surface)

    # Ajustement croisé : la capacité d'un joueur à mettre des aces 
    # dépend de la faiblesse de relance de l'adversaire (1 - return_1st)
    vulnerability_b = 1.0 - stats_b["return_1st"]
    vulnerability_a = 1.0 - stats_a["return_1st"]

    expected_a = stats_a["aces"] * vulnerability_b * multiplier
    expected_b = stats_b["aces"] * vulnerability_a * multiplier
    total_expected = expected_a + expected_b

    return {
        "Player A": player_a,
        "Expected A": round(expected_a, 2),
        "Player B": player_b,
        "Expected B": round(expected_b, 2),
        "Total Match Aces": round(total_expected, 2)
    }

def evaluate_over_under(expected_total, line):
    """
    Utilise la loi de Poisson pour estimer la probabilité de l'Over ou de l'Under.
    """
    # P(X > line) = 1 - CDF(line)
    prob_over = 1 - poisson.cdf(line, expected_total)
    prob_under = 1 - prob_over

    return {
        "Line": line,
        "Prob Over (%)": round(prob_over * 100, 1),
        "Prob Under (%)": round(prob_under * 100, 1)
    }

def evaluate_aces_parlay(selections):
    """
    Calcule la probabilité conjointe et la cote théorique d'un pari combiné d'aces.
    selections = [{'match': str, 'prob_success': float, 'odds': float}, ...]
    """
    combined_prob = 1.0
    total_odds = 1.0

    for sel in selections:
        combined_prob *= (sel['prob_success'] / 100.0)
        total_odds *= sel['odds']

    true_parlay_odds = 1.0 / combined_prob if combined_prob > 0 else 0
    edge = total_odds - true_parlay_odds

    return {
        "Probabilité Combinée Réelle (%)": round(combined_prob * 100, 2),
        "Cote Totale Bookmaker": round(total_odds, 2),
        "Valeur / Edge": round(edge, 2)
    }

# ==============================================================================
# 4. EXEMPLE D'EXÉCUTION DU SCRIPT
# ==============================================================================
if __name__ == "__main__":
    print("=== TEST DE L'ALGORITHME ATP ACES ==-\n")
    
    # Simulation du match Alexander Blockx vs Flavio Cobolli à Cincinnati (Hard)
    match_sim = calculate_match_aces(
        player_a="Alexander Blockx",
        player_b="Flavio Cobolli",
        surface="Hard",
        tournament_name="Montreal / Cincinnati",
        category="Masters 1000"
    )
    
    print(f"Match : {match_sim['Player A']} vs {match_sim['Player B']}")
    print(f"-> Espérance d'aces {match_sim['Player A']} : {match_sim['Expected A']}")
    print(f"-> Espérance d'aces {match_sim['Player B']} : {match_sim['Expected B']}")
    print(f"-> Total estimé d'aces combinés : {match_sim['Total Match Aces']}\n")
    
    # Test d'une ligne de bookmaker fixée à 12.5 aces
    ou_test = evaluate_over_under(match_sim['Total Match Aces'], line=12.5)
    print(f"Analyse de la ligne Over/Under 12.5 : {ou_test}\n")
    
    # Test d'un combiné d'aces
    my_parlay = [
        {"match": "Blockx - Cobolli (Over 12.5 Aces)", "prob_success": 58.5, "odds": 1.80},
        {"match": "Autre match prop ace", "prob_success": 65.0, "odds": 1.66}
    ]
    parlay_res = evaluate_aces_parlay(my_parlay)
    print("=== ANALYSE DU COMBINÉ ===")
    for k, v in parlay_res.items():
        print(f"{k} : {v}")
      
