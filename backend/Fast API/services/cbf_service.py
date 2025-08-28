import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Union


class CBFSystemNormalizedProximity:
    def __init__(
        self,
        scores_data: Union[pd.DataFrame, List[Dict]],
        passing_data: Union[pd.DataFrame, List[Dict]],
        tolerance: float = 0.1,
    ):
        # Konversi ke DataFrame
        self.df_scores = (
            pd.DataFrame(scores_data)
            if not isinstance(scores_data, pd.DataFrame)
            else scores_data.copy()
        )
        self.df_passing = (
            pd.DataFrame(passing_data)
            if not isinstance(passing_data, pd.DataFrame)
            else passing_data.copy()
        )
        self.tolerance = tolerance

        # Pastikan kolom nilai numerik
        self.score_cols = [c for c in self.df_scores.columns if c != "id_user"]
        self.df_scores[self.score_cols] = self.df_scores[self.score_cols].apply(
            pd.to_numeric, errors="coerce"
        ).fillna(0)

        # Hitung rata-rata skor user
        self.df_scores["avg_score"] = self.df_scores[self.score_cols].mean(axis=1)
        self.feature_matrix = self.df_scores[self.score_cols].to_numpy(dtype=float)

        # Konversi kolom passing grade ke numerik
        for col in ["rataan", "min_val", "max_val"]:
            if col in self.df_passing.columns:
                self.df_passing[col] = pd.to_numeric(
                    self.df_passing[col], errors="coerce"
                ).fillna(0)

    def recommend(
        self,
        user_id: int,
        top_n_user: int = 5,
        top_n_prodi: int = 10,
        weight_tps: float = 0.3,
        weight_mapel: float = 0.7,
    ) -> pd.DataFrame:

        if user_id not in self.df_scores["id_user"].values:
            return pd.DataFrame()

        idx = self.df_scores.index[self.df_scores["id_user"] == user_id][0]
        user_vector = self.feature_matrix[idx].reshape(1, -1)

        similarities = cosine_similarity(user_vector, self.feature_matrix).flatten()
        similarities[idx] = -1
        similarities = np.clip(similarities, 0, 1)

        top_indices = similarities.argsort()[::-1][:top_n_user]
        sim_df = self.df_scores.loc[top_indices, ["id_user", "avg_score"]].copy()
        sim_df["similarity"] = similarities[top_indices]
        sim_df["query_user_id"] = user_id

        if sim_df.empty:
            return pd.DataFrame()

        # Ambil nilai user untuk bobot TPS & Mapel
        user_row = self.df_scores.iloc[idx]
        tps_cols = [c for c in self.score_cols if c in ["score_kmb", "score_kpu", "score_kua", "score_ppu"]]
        mapel_cols = [c for c in self.score_cols if c not in tps_cols]

        tps_score = user_row[tps_cols].mean() if tps_cols else 0
        mapel_score = user_row[mapel_cols].mean() if mapel_cols else 0
        user_avg_weighted = (weight_tps * tps_score) + (weight_mapel * mapel_score)

        # Gabungkan dengan passing grade
        merged = sim_df.merge(self.df_passing, how="cross")

        # Filter kandidat minimal
        filtered = merged[merged["avg_score"] >= merged["min_val"]]

        # Jika semua gagal memenuhi syarat min_val → fallback
        if filtered.empty:
            fallback = self.df_passing.copy()
            fallback["id_user"] = user_id
            fallback["avg_score"] = user_row["avg_score"]
            fallback["similarity"] = 0
            fallback["name_university"] = "Rekomendasi Masuk Ke SWASTA dengan Akreditasi minimal B"

            fallback["score_rel"] = 0
            fallback["score"] = 0
            fallback["recommendation_score"] = 0
            fallback["acceptance_probability"] = 0

            return fallback.head(top_n_prodi)[
                ["id_user", "avg_score", "similarity", "nama_prodi", "name_university",
                 "rataan", "min_val", "max_val", "score_rel", "score", 
                 "recommendation_score", "acceptance_probability"]
            ]

        # Filter sesuai tolerance rataan (prioritaskan >= rataan)
        filtered = filtered[filtered["avg_score"] >= filtered["rataan"] * (1 - self.tolerance)]

        if filtered.empty:
            return pd.DataFrame()

        # Hitung skor normalisasi
        filtered["user_avg_score"] = user_avg_weighted
        filtered["score_rel"] = (filtered["avg_score"] - filtered["min_val"]) / (filtered["max_val"] - filtered["min_val"])
        filtered["score_rel"] = filtered["score_rel"].clip(0, 1)

        filtered["score"] = filtered["similarity"] * filtered["rataan"] * filtered["score_rel"]

        max_score = filtered["score"].max()
        filtered["recommendation_score"] = (
            (filtered["score"] / max_score * 100).round(2) if max_score > 0 else 0
        )

        filtered["acceptance_probability"] = (
            1 / (1 + np.exp(-0.1 * (filtered["recommendation_score"] - 50)))
        ).round(4)
        filtered["acceptance_probability"] = (filtered["acceptance_probability"] * 100).round(2)

        filtered = filtered.sort_values(by="recommendation_score", ascending=False).reset_index(drop=True)

        return filtered.head(top_n_prodi)[
            ["id_user", "avg_score", "similarity", "nama_prodi", "name_university",
             "rataan", "min_val", "max_val", "score_rel", "score", 
             "recommendation_score", "acceptance_probability"]
        ]
