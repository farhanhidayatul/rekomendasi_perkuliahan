# cbr_service.py
from typing import List, Dict
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import json

class CBRSystem:
    def __init__(self, scores_data: List[Dict], passing_data: List[Dict], tolerance: float = 0.1):
        """
        scores_data: [{"id_user":1, "math":80, "physics":70, ...}, ...]
        passing_data: [{"id_prodi":1, "nama_prodi":"Informatika", "rataan":75, "min_val":60, "max_val":85, "type":"science"}, ...]
        """
        self.df_scores = pd.DataFrame(scores_data)
        self.df_passing = pd.DataFrame(passing_data)
        self.tolerance = tolerance

        # pastikan kolom skor numerik
        self.score_cols = [c for c in self.df_scores.columns if c not in ("id_user", "name_user")]
        self.df_scores[self.score_cols] = self.df_scores[self.score_cols].apply(pd.to_numeric, errors="coerce").fillna(0)
        self.df_scores["avg_score"] = self.df_scores[self.score_cols].mean(axis=1)
        self.feature_matrix = self.df_scores[self.score_cols].to_numpy(dtype=float)

        # pastikan kolom passing grade numerik
        for col in ["rataan", "min_val", "max_val"]:
            if col in self.df_passing.columns:
                self.df_passing[col] = pd.to_numeric(self.df_passing[col], errors="coerce").fillna(0)

    def retrieve(self, user_id: int, top_n: int) -> pd.DataFrame:
        """Cari top_n user paling mirip dengan user_id berdasarkan cosine similarity."""
        if user_id not in self.df_scores["id_user"].values:
            return pd.DataFrame()

        idx = self.df_scores.index[self.df_scores["id_user"] == user_id][0]
        user_vector = self.feature_matrix[idx].reshape(1, -1)
        similarities = cosine_similarity(user_vector, self.feature_matrix).flatten()
        similarities[idx] = -1  # hindari dirinya sendiri
        similarities = np.clip(similarities, 0, 1)  # penting, biar tidak ada nilai negatif

        top_indices = similarities.argsort()[::-1][:top_n]
        sim_df = self.df_scores.loc[top_indices, ["id_user", "avg_score"]].copy()
        sim_df["similarity"] = similarities[top_indices]
        sim_df["query_user_id"] = user_id

        return sim_df

    def recommend_prodi(self, sim_df: pd.DataFrame) -> pd.DataFrame:
        """Rekomendasi prodi untuk satu user berdasarkan similarity dan passing grade."""
        if sim_df is None or sim_df.empty:
            return pd.DataFrame()

        merged = sim_df.assign(key=1).merge(self.df_passing.assign(key=1), on="key").drop("key", axis=1)

        # Filter: avg_score >= min_val
        merged = merged[merged["avg_score"] >= merged["min_val"]].copy()

        # Filter tolerance: rataan ± tolerance
        merged = merged[
            (merged["avg_score"] >= merged["rataan"] * (1 - self.tolerance)) &
            (merged["avg_score"] <= merged["rataan"] * (1 + self.tolerance))
        ].copy()

        if merged.empty:
            return pd.DataFrame()

        # Normalisasi relatif terhadap min-max passing grade
        merged["score_rel"] = (merged["avg_score"] - merged["min_val"]) / (merged["max_val"] - merged["min_val"])
        merged["score_rel"] = merged["score_rel"].clip(0, 1)

        # Skor akhir
        merged["score"] = merged["similarity"] * merged["rataan"] * merged["score_rel"]

        # Normalisasi ke 0–100
        max_score = merged["score"].max()
        merged["recommendation_score"] = (merged["score"] / max_score * 100).round(2) if max_score > 0 else 0

        merged = merged.sort_values(by="recommendation_score", ascending=False).reset_index(drop=True)
        return merged


def get_cbr_recommendation(user_id: int, track: str, scores: List[Dict], passing: List[Dict], top_n: int):
    # --- pastikan passing list, parse JSON jika string ---
    if isinstance(passing, str):
        try:
            passing = json.loads(passing)
        except json.JSONDecodeError:
            passing = []

    # --- filter by track ---
    df_pg = [p for p in passing if isinstance(p, dict) and p.get("type") == track]

    cbr = CBRSystem(scores, df_pg)
    sim_df = cbr.retrieve(user_id, top_n)
    recs = cbr.recommend_prodi(sim_df)
    return recs.to_dict(orient="records") if not recs.empty else []


