import sys
import os
import pandas as pd
from plotters import plot_elo_trend, plot_radar_chart, plot_all_radars
from team_analyzer import analyze_all_teams, forecast_all_matches
from player_analyzer import save_top_players_to_csv

# 20 Premier League teams (in alphabetical order)
teams = [
    "AFC Bournemouth", "Arsenal FC", "Aston Villa FC", "Brentford FC", "Brighton & Hove Albion FC",
    "Chelsea FC", "Crystal Palace FC", "Everton FC", "Fulham FC", "Ipswich Town FC",
    "Leicester City FC", "Liverpool FC", "Manchester City FC", "Manchester United FC",
    "Newcastle United FC", "Nottingham Forest FC", "Southampton FC", "Tottenham Hotspur FC",
    "West Ham United FC", "Wolverhampton Wanderers FC"
]

# Player position mapping
position_map = {
    "1": {
        "name": "Forward",
        "file": "top_fw_players.csv",
        "metrics": [
            "g_minus_pkgls_per90_norm", "xggls_per90_norm", "xaggls_per90_norm",
            "take_ons_succ_pct_norm", "carries_prgc_norm", "receiving_prgr_norm"
        ]
    },
    "2": {
        "name": "Midfielder",
        "file": "top_mf_players.csv",
        "metrics": [
            "progression_prgp_norm", "progression_prgr_norm", "xaggls_per90_norm",
            "sca_sca90_norm", "touches_mid_3rd_norm", "performance_int_norm"
        ]
    },
    "3": {
        "name": "Defender",
        "file": "top_df_players.csv",
        "metrics": [
            "performance_tklw_norm", "performance_int_norm", "blocks_blocks_norm",
            "aerialduels_won_pct_norm", "progression_prgp_norm", "err_norm"
        ]
    }
}

# -------------------- Auto Generation Section --------------------

def prepare_elo():
    print("\n📊 Generating Elo history data...")
    matches_path = os.path.join("data", "elo_matches_2425.csv")
    schedule_path = os.path.join("data", "epl_2025_schedule.csv")

    if not os.path.exists(matches_path) or not os.path.exists(schedule_path):
        print("❌ Missing raw data files required for Elo computation.")
        return

    matches_df = pd.read_csv(matches_path)
    schedule_df = pd.read_csv(schedule_path)
    elo_history_df = analyze_all_teams(matches_df)
    forecast_all_matches(schedule_df, elo_history_df)
    print("✔ Elo data successfully generated.")

def prepare_players():
    print("\n🧠 Ranking TOP 3 players (FW/MF/DF)...")
    raw_path = os.path.join("data", "merged_players_all.csv")
    if not os.path.exists(raw_path):
        print("❌ Missing raw player data for scoring.")
        return

    df = pd.read_csv(raw_path)
    save_top_players_to_csv(df)
    print("✔ Player ranking files successfully generated.")

# -------------------- Interactive Section --------------------
def choose_team():
    print("\nSelect a team to view Elo trend chart (or 0 to skip, 21 for all teams):")
    for idx, team in enumerate(teams, 1):
        print(f"{idx:>2}. {team}")
    print("21. Generate Elo charts for all 20 teams")

    choice = input("Enter team number (1–20), 21 for all, or 0 to skip: ").strip()

    if choice == "0":
        print("⏭ Skipped team chart generation.")
        return
    elif choice == "21":
        for team_name in teams:
            plot_elo_trend(team_name)
        return
    elif choice.isdigit() and 1 <= int(choice) <= 20:
        team_name = teams[int(choice) - 1]
        plot_elo_trend(team_name)
    else:
        print("❌ Invalid selection. Exiting program.")
        sys.exit(1)

def choose_position():
    print("\nSelect a player position to generate radar chart:")
    print("0. Skip radar chart generation.")
    print("1. Forward")
    print("2. Midfielder")
    print("3. Defender")
    print("4. Generate all radar charts")
    choice = input("Enter number (0–4): ").strip()

    if choice in position_map:
        info = position_map[choice]
        plot_radar_chart(info["file"], info["name"], info["metrics"])
    elif choice == "0":
        print("⏭ Skipping radar chart generation.")
    elif choice == "4":
        plot_all_radars()
    else:
        print("❌ Invalid selection. Exiting program.")
        sys.exit(1)

# -------------------- Main Entry Point --------------------
if __name__ == "__main__":
    print("⚽ Welcome to EPL Metrics Lab ⚽")

    prepare_elo()
    prepare_players()

    choose_team()
    choose_position()