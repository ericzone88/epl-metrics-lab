import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from math import pi
from config import FIGURE_DPI, FIGURE_STYLE, FONT_FAMILY

os.makedirs("outputs", exist_ok=True)
plt.style.use(FIGURE_STYLE)
plt.rcParams["font.family"] = FONT_FAMILY

# ---------------- Elo History + Trend Line + Forecast Text ----------------
def plot_elo_trend(team_name: str):
    # Teams relegated at the end of the 2024/25 Premier League season.
    relegated_teams = {
        "Leicester City FC",
        "Ipswich Town FC",
        "Southampton FC"
    }

    try:
        elo_df = pd.read_csv("outputs/elo_history_all.csv")
        forecast_df = pd.read_csv("outputs/win_probability_forecast.csv")
    except FileNotFoundError:
        print("❌ Required data files not found in 'outputs/' directory.")
        return

    team_elo = elo_df[elo_df["team"] == team_name]
    if team_elo.empty:
        print(f"❌ No Elo data found for '{team_name}'. Please check the team name.")
        return

    forecast_team = forecast_df[forecast_df["team"] == team_name]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(team_elo["round"], team_elo["elo_score"], marker="o", color="darkblue", linewidth=2, label=team_name)

    # Add trend line
    z = np.polyfit(team_elo["round"], team_elo["elo_score"], 1)
    p = np.poly1d(z)
    ax.plot(team_elo["round"], p(team_elo["round"]), linestyle="--", color="gray", label="Trend")

    ax.set_title(f"{team_name} Elo Rating Trend", fontsize=14, pad=15)
    ax.set_xlabel("2024/25 Matchweek")
    ax.set_ylabel("Elo Score")
    ax.legend()
    ax.grid(True)

    # Build forecast text, including relegation note if needed
    forecast_lines = ["Win Probability Forecast — Rounds 1 & 2 of the 2025/26 Season", ""]
    if team_name in relegated_teams:
        forecast_lines.append(f"{team_name} was relegated to the Championship after the 2024/25 season.")
        forecast_lines.append("")

    for _, row in forecast_team.iterrows():
        date = row["date"]
        rnd = int(row["round"])
        home = row["home_team"]
        away = row["away_team"]
        home_prob = row["home_win_probability"]
        away_prob = row["away_win_probability"]

        forecast_lines.append(
            f"{date} Round {rnd} — {home} (Home): {home_prob} vs {away} (Away): {away_prob}"
        )

    forecast_text = "\n".join(forecast_lines)
    plt.figtext(
        0.5, -0.1,
        forecast_text,
        ha="center", fontsize=11, color="#6A5ACD", wrap=True
    )

    output_path = os.path.join("outputs", f"{team_name.replace(' ', '_')}_elo_trend.png")
    fig.tight_layout(pad=3.0)
    plt.savefig(output_path, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close()
    print(f"✔ Elo trend plot saved to {output_path}")

# -------------------- Radar Chart --------------------
def radar_factory(num_vars):
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]
    return angles

readable_names = {
    # Forward
    "g_minus_pkgls_per90_norm": "Non-PK Goals",
    "xggls_per90_norm": "xG per 90",
    "xaggls_per90_norm": "xA per 90",
    "take_ons_succ_pct_norm": "Dribble Success",
    "carries_prgc_norm": "Ball Carries",
    "receiving_prgr_norm": "Runs Received",
    # Midfielder
    "progression_prgp_norm": "Forward Passes",
    "progression_prgr_norm": "Forward Receives",
    "sca_sca90_norm": "Shot Creation",
    "touches_mid_3rd_norm": "Midfield Touches",
    "performance_int_norm": "Interceptions",
    # Defender
    "performance_tklw_norm": "Tackles Won",
    "blocks_blocks_norm": "Blocks",
    "aerialduels_won_pct_norm": "Aerial Win",
    "err_norm": "No Errors"
}

def plot_radar_chart(csv_filename, position_name, metrics):
    path = os.path.join("outputs", csv_filename)
    if not os.path.exists(path):
        print(f"❌ File not found: {csv_filename}")
        return

    try:
        df = pd.read_csv(path).head(3) # in case future files contain more
        angles = radar_factory(len(metrics))

        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
        ax.set_position([0.1, 0.05, 0.7, 0.7])

        for idx, (_, row) in enumerate(df.iterrows()):
            values = [row[m] for m in metrics]
            values += values[:1]
            ax.plot(angles, values, label=f"TOP {idx+1} {row['player']}")
            ax.fill(angles, values, alpha=0.1)

        label_names = [readable_names.get(m, m) for m in metrics]
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(label_names, fontsize=10)

        ax.set_title(f"Top 3 {position_name}s Radar Chart", fontsize=22, fontweight='bold', pad=80)
        ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.18), fontsize=14, frameon=False)

        output_path = os.path.join("outputs", f"radar_{position_name.lower()}.png")
        plt.savefig(output_path, dpi=FIGURE_DPI)
        plt.close()
        print(f"✔ Radar chart for {position_name} saved to {output_path}")

    except KeyError as e:
        print(f"❌ Missing expected metric column in {csv_filename}: {e}")
    except Exception as e:
        print(f"❌ Failed to plot radar chart for {position_name}: {e}")

def plot_all_radars():
    plot_radar_chart(
        "top_fw_players.csv",
        "Forward",
        [
            "g_minus_pkgls_per90_norm",
            "xggls_per90_norm",
            "xaggls_per90_norm",
            "take_ons_succ_pct_norm",
            "carries_prgc_norm",
            "receiving_prgr_norm"
        ]
    )

    plot_radar_chart(
        "top_mf_players.csv",
        "Midfielder",
        [
            "progression_prgp_norm",
            "progression_prgr_norm",
            "xaggls_per90_norm",
            "sca_sca90_norm",
            "touches_mid_3rd_norm",
            "performance_int_norm"
        ]
    )

    plot_radar_chart(
        "top_df_players.csv",
        "Defender",
        [
            "performance_tklw_norm",
            "performance_int_norm",
            "blocks_blocks_norm",
            "aerialduels_won_pct_norm",
            "progression_prgp_norm",
            "err_norm"
        ]
    )