import pandas as pd
import os
from config import INITIAL_ELO, HOME_ADVANTAGE
from utils import update_elo, win_probability

os.makedirs("outputs", exist_ok=True)

# ------------- Elo analysis for a single team --------------
def analyze_team(team_df: pd.DataFrame, team_name: str) -> pd.DataFrame:
    mask = (team_df['home_team'] == team_name) | (team_df['away_team'] == team_name)
    target_team = team_df[mask].copy()
    target_team.sort_values(by='round', inplace=True)

    team_elos = {}
    elo_history = []

    for _, row in target_team.iterrows():
        home = row['home_team']
        away = row['away_team']
        home_score = row['home_score']
        away_score = row['away_score']
        round_num = row['round']

        # Initialize Elo
        if home not in team_elos:
            team_elos[home] = INITIAL_ELO
        if away not in team_elos:
            team_elos[away] = INITIAL_ELO

        # Add home advantage
        home_elo = team_elos[home] + HOME_ADVANTAGE
        away_elo = team_elos[away]

        # Compute match result
        if home_score > away_score:
            result = 1
        elif home_score == away_score:
            result = 0.5
        else:
            result = 0

        # Update Elo ratings
        new_home_elo, new_away_elo = update_elo(home_elo, away_elo, result)
        team_elos[home] = new_home_elo - HOME_ADVANTAGE
        team_elos[away] = new_away_elo

        # Record Elo for this team
        team_elo = team_elos[team_name]
        elo_history.append({
            'round': round_num,
            'elo_score': team_elo,
            'is_forecast': False
        })

    return pd.DataFrame(elo_history)

# -------------- Elo Analysis for All Teams ----------------
def analyze_all_teams(team_df: pd.DataFrame) -> pd.DataFrame:
    all_teams = sorted(set(team_df['home_team']) | set(team_df['away_team']))
    all_records = []

    for team in all_teams:
        elo_df = analyze_team(team_df, team)
        elo_df['team'] = team
        all_records.append(elo_df)

    full_df = pd.concat(all_records, ignore_index=True)
    full_df.to_csv("outputs/elo_history_all.csv", index=False)

    return full_df

# ------------- Single-Team Forecast Class -------------------
class WinRateForecast:
    """This class does not compute Elo; it assumes current Elo ratings are preloaded."""
    def __init__(self, schedule_df: pd.DataFrame, team_elos: dict):
        self.schedule_df = schedule_df
        self.team_elos = team_elos.copy()

    def forecast(self, team_name: str) -> pd.DataFrame:
        """Forecast next two rounds for a given team."""
        future_matches = self.schedule_df[
            (self.schedule_df['home_team'] == team_name) |
            (self.schedule_df['away_team'] == team_name)
        ].sort_values(by='round')

        if future_matches.empty:
            return pd.DataFrame()

        current_round = future_matches['round'].min()
        target_rounds = [current_round, current_round + 1]
        future_matches = future_matches[future_matches['round'].isin(target_rounds)]

        forecast_rows = []

        for _, row in future_matches.iterrows():
            home = row['home_team']
            away = row['away_team']
            round_num = row['round']

            home_elo = self.team_elos[home] + HOME_ADVANTAGE
            away_elo = self.team_elos[away]

            prob = win_probability(home_elo, away_elo)

            if team_name == home:
                target_prob = round(prob * 100)
                opponent = away
            else:
                target_prob = round((1 - prob) * 100)
                opponent = home

            forecast_rows.append({
                'round': round_num,
                'team': team_name,
                'opponent': opponent,
                'win_probability': f"{target_prob}%",
                'opponent_win_probability': f"{100 - target_prob}%"
            })

        return pd.DataFrame(forecast_rows)

# ------------- Forecast All Matches ---------------
def forecast_all_matches(schedule_df: pd.DataFrame, elo_history_df: pd.DataFrame) -> pd.DataFrame:
    """Forecast next two rounds for all matches."""
    teams_in_schedule = sorted(set(schedule_df['home_team']) | set(schedule_df['away_team']))

    # Get most recent Elo for each team
    team_elos = {}
    for team in teams_in_schedule:
        team_df = elo_history_df[
            (elo_history_df['team'] == team) &
            (elo_history_df['is_forecast'] == False)
        ]
        if not team_df.empty:
            last_round = team_df['round'].max()
            last_elo = team_df[team_df['round'] == last_round]['elo_score'].values[0]
            team_elos[team] = last_elo
        else:
            # For teams without Elo history (e.g., newly promoted clubs), use INITIAL_ELO as fallback
            team_elos[team] = INITIAL_ELO

    # Forecast matches in next two rounds
    current_round = schedule_df['round'].min()
    target_rounds = [current_round, current_round + 1]
    matches = schedule_df[schedule_df['round'].isin(target_rounds)].copy()
    matches.sort_values(by=['round', 'date'], inplace=True)

    rows = []
    for _, row in matches.iterrows():
        home = row['home_team']
        away = row['away_team']
        round_num = row['round']
        date = row['date']

        home_elo = team_elos.get(home, INITIAL_ELO) + HOME_ADVANTAGE
        away_elo = team_elos.get(away, INITIAL_ELO)

        prob_home = round(win_probability(home_elo, away_elo) * 100)
        prob_away = 100 - prob_home

        for team in [home, away]:
            opponent = away if team == home else home
            win_prob = prob_home if team == home else prob_away
            lose_prob = 100 - win_prob

            rows.append({
                'date': date,
                'round': round_num,
                'home_team': home,
                'away_team': away,
                'home_win_probability': f"{prob_home}%",
                'away_win_probability': f"{prob_away}%",
                'team': team,
                'opponent': opponent,
                'win_probability': f"{win_prob}%",
                'opponent_win_probability': f"{lose_prob}%"
            })

    forecast_df = pd.DataFrame(rows)
    forecast_df.to_csv("outputs/win_probability_forecast.csv", index=False)

    return forecast_df