from config import ELO_SCALING, ELO_K_FACTOR

def win_probability(team_a_elo, team_b_elo, scaling=ELO_SCALING):
    """Team A against Team B"""
    return 1 / (1 + 10 ** ((team_b_elo - team_a_elo) / scaling))

def update_elo(team_a_elo, team_b_elo, result, k=ELO_K_FACTOR, scaling=ELO_SCALING):
    """
    Update Elo ratings after a match.
    Parameters:
        result --actual outcome for Team A (1 = win, 0.5 = draw, 0 = loss)
    """
    expected_a = win_probability(team_a_elo, team_b_elo, scaling)
    expected_b = 1 - expected_a

    new_elo_a = team_a_elo + k * (result - expected_a)
    new_elo_b = team_b_elo + k * ((1 - result) - expected_b)

    return new_elo_a, new_elo_b