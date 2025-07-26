from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
import os

os.makedirs("outputs", exist_ok=True)

class TopPlayerFinder(ABC):
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.filtered_df = None

    def filter_by_minutes(self, df: pd.DataFrame, minute_column: str = 'playing_time_min') -> pd.DataFrame:
        """Filter out players who played less than the median playing time."""
        threshold = df[minute_column].median()
        return df[df[minute_column] >= threshold].copy()

    @abstractmethod
    def filter_players(self): # Filter players by position
        pass

    @abstractmethod
    def prepare_features(self): # Select fields and standardize
        pass

    @abstractmethod
    def compute_score(self): # Assign weights and calculate total score
        pass

    def normalize(self, series: pd.Series) -> pd.Series:
        """Min-max normalization."""
        return (series - series.min()) / (series.max() - series.min())

    def log_scaling(self, series: pd.Series) -> pd.Series:
        """Apply log transformation to reduce the impact of outliers."""
        series = series.clip(lower=0).fillna(0)
        return self.normalize(np.log1p(series))

    def smart_scale(self, df: pd.DataFrame, column: str, factor: float = 1.5) -> pd.DataFrame:
        """
        Automatically apply normalization or log scaling depending on outlier presence.

        This method uses the IQR (Interquartile Range) rule to detect outliers.
        If outliers are detected, log transformation is applied; otherwise, min-max normalization is used.
        """
        q1 = df[column].quantile(0.25)
        q3 = df[column].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - factor * iqr
        upper = q3 + factor * iqr
        has_outlier = ((df[column] < lower) | (df[column] > upper)).any()

        if has_outlier:
            df[f'{column}_norm'] = self.log_scaling(df[column])
        else:
            df[f'{column}_norm'] = self.normalize(df[column])
        return df

    def compute_weighted_score(self, df: pd.DataFrame, weights: dict) -> pd.DataFrame:
        """Compute weighted total score from normalized metrics."""
        df['score'] = 0
        for col, weight in weights.items():
            df['score'] += df[col] * weight
        return df

    def top_n(self, n: int) -> pd.DataFrame:
        """Return top N players based on score."""
        return self.filtered_df.sort_values(by='score', ascending=False).head(n)

    def get_all_ranked(self, columns: list) -> pd.DataFrame:
        """Return all ranked players with selected columns, including 1-based rank."""
        ranked_df = self.filtered_df.sort_values(by="score", ascending=False)[columns].reset_index(drop=True)
        ranked_df.insert(0, "rank", ranked_df.index + 1)
        return ranked_df

# ---------------- Forward Scorer ----------------
class ForwardScorer(TopPlayerFinder):
    def filter_players(self):
        fw_df = self.df[self.df['main_pos'] == 'FW'].copy()
        fw_df = self.filter_by_minutes(fw_df)
        self.filtered_df = fw_df

    def prepare_features(self):
        fw_df = self.filtered_df
        columns_to_scale = [
            'gls_per90', 'g_minus_pkgls_per90', 'g_plus_agls_per90',
            'g_plus_a_minus_pkgls_per90', 'xggls_per90', 'xg_plus_xaggls_per90',
            'npxggls_per90', 'astgls_per90', 'xaggls_per90', 'sca_sca90',
            'take_ons_succ_pct', 'carries_prgdist', 'carries_prgc',
            'receiving_prgr', 'performance_off', 'teamsuccess_plus_minus90'
        ]
        for col in columns_to_scale:
            fw_df = self.smart_scale(fw_df, col)
        self.filtered_df = fw_df

    def compute_score(self):
        weights = {
            'gls_per90_norm': 0.15,
            'g_minus_pkgls_per90_norm': 0.10,
            'g_plus_agls_per90_norm': 0.05,
            'g_plus_a_minus_pkgls_per90_norm': 0.05,
            'xggls_per90_norm': 0.07,
            'xg_plus_xaggls_per90_norm': 0.07,
            'npxggls_per90_norm': 0.06,
            'astgls_per90_norm': 0.06,
            'xaggls_per90_norm': 0.06,
            'sca_sca90_norm': 0.03,
            'take_ons_succ_pct_norm': 0.05,
            'carries_prgdist_norm': 0.05,
            'carries_prgc_norm': 0.05,
            'receiving_prgr_norm': 0.05,
            'performance_off_norm': 0.05,
            'teamsuccess_plus_minus90_norm': 0.05
        }
        self.filtered_df = self.compute_weighted_score(self.filtered_df, weights)

# ---------------- Midfielder Scorer ----------------
class MidfielderScorer(TopPlayerFinder):
    def filter_players(self):
        mf_df = self.df[self.df['main_pos'] == 'MF'].copy()
        mf_df = self.filter_by_minutes(mf_df)
        self.filtered_df = mf_df

    def prepare_features(self):
        mf_df = self.filtered_df
        columns_to_scale = [
            'progression_prgp', 'progression_prgr', 'progression_prgc',
            'pass_types_live', 'carries_prgdist', 'xaggls_per90', 'astgls_per90',
            'sca_sca90', 'xg_plus_xaggls_per90', 'g_plus_agls_per90',
            'take_ons_succ_pct', 'receiving_prgr', 'touches_mid_3rd',
            'performance_int', 'teamsuccess_plus_minus90'
        ]
        for col in columns_to_scale:
            mf_df = self.smart_scale(mf_df, col)
        self.filtered_df = mf_df

    def compute_score(self):
        weights = {
            'progression_prgp_norm': 0.12,
            'progression_prgr_norm': 0.10,
            'progression_prgc_norm': 0.08,
            'pass_types_live_norm': 0.05,
            'carries_prgdist_norm': 0.05,
            'xaggls_per90_norm': 0.10,
            'astgls_per90_norm': 0.08,
            'sca_sca90_norm': 0.07,
            'xg_plus_xaggls_per90_norm': 0.05,
            'g_plus_agls_per90_norm': 0.05,
            'take_ons_succ_pct_norm': 0.05,
            'receiving_prgr_norm': 0.05,
            'touches_mid_3rd_norm': 0.05,
            'performance_int_norm': 0.05,
            'teamsuccess_plus_minus90_norm': 0.05
        }
        self.filtered_df = self.compute_weighted_score(self.filtered_df, weights)

# ---------------- Defender Scorer ----------------
class DefenderScorer(TopPlayerFinder):
    def filter_players(self):
        df = self.df[self.df['main_pos'] == 'DF'].copy()
        df = self.filter_by_minutes(df)
        self.filtered_df = df

    def prepare_features(self):
        df = self.filtered_df
        columns_to_scale = [
            'performance_int', 'performance_tklw', 'blocks_blocks',
            'aerialduels_won_pct', 'progression_prgp', 'progression_prgr', 'progression_prgc',
            'pass_types_live', 'touches_def_3rd', 'receiving_prgr', 'teamsuccess_plus_minus90',
            'take_ons_succ_pct', 'carries_prgdist', 'performance_crdy', 'performance_crdr',
            'err'
        ]
        for col in columns_to_scale:
            df = self.smart_scale(df, col)
        self.filtered_df = df

    def compute_score(self):
        weights = {
            'performance_int_norm': 0.12,
            'performance_tklw_norm': 0.12,
            'blocks_blocks_norm': 0.10,
            'aerialduels_won_pct_norm': 0.06,
            'progression_prgp_norm': 0.08,
            'progression_prgr_norm': 0.06,
            'progression_prgc_norm': 0.06,
            'pass_types_live_norm': 0.05,
            'touches_def_3rd_norm': 0.05,
            'receiving_prgr_norm': 0.05,
            'teamsuccess_plus_minus90_norm': 0.05,
            'take_ons_succ_pct_norm': 0.05,
            'carries_prgdist_norm': 0.05,
            'performance_crdy_norm': -0.03,
            'performance_crdr_norm': -0.03,
            'err_norm': -0.05
        }
        self.filtered_df = self.compute_weighted_score(self.filtered_df, weights)

# ---------------- Save to CSV ----------------
def save_top_players_to_csv(df: pd.DataFrame, output_dir: str = "outputs"):
    """Run scorer pipelines and save top 3 and full rankings for FW, MF, DF to CSV."""

    fw = ForwardScorer(df)
    fw.filter_players()
    fw.prepare_features()
    fw.compute_score()
    top_fw = fw.top_n(3)[[
        "player", "score",
        "g_minus_pkgls_per90_norm",
        "xggls_per90_norm",
        "xaggls_per90_norm",
        "take_ons_succ_pct_norm",
        "carries_prgc_norm",
        "receiving_prgr_norm"
    ]]
    top_fw.to_csv(os.path.join(output_dir, "top_fw_players.csv"), index=False)

    fw.get_all_ranked(top_fw.columns.tolist()).to_csv(
        os.path.join(output_dir, "all_fw_players.csv"), index=False
    )

    mf = MidfielderScorer(df)
    mf.filter_players()
    mf.prepare_features()
    mf.compute_score()
    top_mf = mf.top_n(3)[[
        "player", "score",
        "progression_prgp_norm",
        "progression_prgr_norm",
        "xaggls_per90_norm",
        "sca_sca90_norm",
        "touches_mid_3rd_norm",
        "performance_int_norm"
    ]]
    top_mf.to_csv(os.path.join(output_dir, "top_mf_players.csv"), index=False)

    mf.get_all_ranked(top_mf.columns.tolist()).to_csv(
        os.path.join(output_dir, "all_mf_players.csv"), index=False
    )

    df_sc = DefenderScorer(df)
    df_sc.filter_players()
    df_sc.prepare_features()
    df_sc.compute_score()
    top_df = df_sc.top_n(3)[[
        "player", "score",
        "performance_tklw_norm",
        "performance_int_norm",
        "blocks_blocks_norm",
        "aerialduels_won_pct_norm",
        "progression_prgp_norm",
        "err_norm"
    ]]
    top_df.to_csv(os.path.join(output_dir, "top_df_players.csv"), index=False)

    df_sc.get_all_ranked(top_df.columns.tolist()).to_csv(
        os.path.join(output_dir, "all_df_players.csv"), index=False
    )