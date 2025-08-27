import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class CBFSystemNormalizedProximity:
    def __init__(self, df_scores: pd.DataFrame, df_passing: pd.DataFrame, tolerance: float = 0.1):
        self.df_scores = df_scores.copy()
        self.df_passing = df_passing.copy()
        self.tolerance = tolerance  
        self.score_cols = [c for c in self.df_scores.columns if c != "id_user"]
        self.df_scores["avg_score"] = self.df_scores[self.score_cols].mean(axis=1)
        self.feature_matrix = self.df_scores[self.score_cols].to_numpy(dtype=float)

    def retrieve(self, user_id: int, top_n: int = 5):
        if user_id not in self.df_scores["id_user"].values:
            return None
        idx = self.df_scores.index[self.df_scores["id_user"] == user_id][0]
        user_vector = self.feature_matrix[idx].reshape(1, -1)
        
        similarities = cosine_similarity(user_vector, self.feature_matrix).flatten()
        similarities[idx] = -1  
        similarities = np.clip(similarities, 0, 1)
        
        top_indices = similarities.argsort()[::-1][:top_n]
        sim_df = self.df_scores.loc[top_indices, ["id_user","avg_score"]].copy()
        sim_df["similarity"] = similarities[top_indices]
        return sim_df

    def recommend_prodi(self, sim_df: pd.DataFrame):
        if sim_df is None or sim_df.empty:
            return None

        merged = sim_df.merge(self.df_passing, how="cross")
        merged = merged[merged["avg_score"] >= merged["min_val"]].copy()

        merged = merged[
            (merged["avg_score"] >= merged["rataan"] * (1 - self.tolerance)) &
            (merged["avg_score"] <= merged["rataan"] * (1 + self.tolerance))
        ].copy()

        merged["score_rel"] = (merged["avg_score"] - merged["min_val"]) / (merged["max_val"] - merged["min_val"])
        merged["score_rel"] = merged["score_rel"].clip(0, 1)

        merged["score"] = merged["similarity"] * merged["rataan"] * merged["score_rel"]

        max_score = merged["score"].max()
        if max_score > 0:
            merged["recommendation_score"] = (merged["score"] / max_score * 100).round(2)
        else:
            merged["recommendation_score"] = 0

        merged = merged.sort_values(by="recommendation_score", ascending=False).reset_index(drop=True)
        return merged
