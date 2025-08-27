import pandas as pd
import mysql.connector
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# --- Koneksi ke MySQL ---
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Astagfirullah123#",
    database="rekomendasi_perkuliahan"
)

df_science = pd.read_sql("SELECT * FROM science_scores", conn)
df_passing_grade = pd.read_sql("SELECT * FROM passing_grade", conn)
conn.close()

class CBFSystemNormalizedProximity:
    def __init__(self, df_scores: pd.DataFrame, df_passing: pd.DataFrame, tolerance: float = 0.1):
        self.df_scores = df_scores.copy()
        self.df_passing = df_passing.copy()
        self.tolerance = tolerance  # toleransi ±10% default
        self.score_cols = [c for c in self.df_scores.columns if c != "id_user"]
        self.df_scores["avg_score"] = self.df_scores[self.score_cols].mean(axis=1)
        self.feature_matrix = self.df_scores[self.score_cols].to_numpy(dtype=float)

    def retrieve(self, user_id: int, top_n: int = 5):
        if user_id not in self.df_scores["id_user"].values:
            return None
        idx = self.df_scores.index[self.df_scores["id_user"] == user_id][0]
        user_vector = self.feature_matrix[idx].reshape(1, -1)
        
        similarities = cosine_similarity(user_vector, self.feature_matrix).flatten()
        similarities[idx] = -1  # hindari dirinya sendiri
        similarities = np.clip(similarities, 0, 1)
        
        top_indices = similarities.argsort()[::-1][:top_n]
        sim_df = self.df_scores.loc[top_indices, ["id_user","avg_score"]].copy()
        sim_df["similarity"] = similarities[top_indices]
        return sim_df

    def recommend_prodi(self, sim_df: pd.DataFrame):
        if sim_df is None or sim_df.empty:
            return None

        merged = sim_df.merge(self.df_passing, how="cross")

        # Filter: avg_score minimal min_val
        merged = merged[merged["avg_score"] >= merged["min_val"]].copy()

        # Filter: avg_score harus mendekati rataan ±tolerance
        merged = merged[
            (merged["avg_score"] >= merged["rataan"] * (1 - self.tolerance)) &
            (merged["avg_score"] <= merged["rataan"] * (1 + self.tolerance))
        ].copy()

        # Normalisasi min-max: avg_score relatif terhadap min_val-max_val prodi
        merged["score_rel"] = (merged["avg_score"] - merged["min_val"]) / (merged["max_val"] - merged["min_val"])
        merged["score_rel"] = merged["score_rel"].clip(0, 1)

        # Hitung skor akhir
        merged["score"] = merged["similarity"] * merged["rataan"] * merged["score_rel"]

        # Normalisasi ke skor rekomendasi relatif (0–100)
        max_score = merged["score"].max()
        if max_score > 0:
            merged["recommendation_score"] = (merged["score"] / max_score * 100).round(2)
        else:
            merged["recommendation_score"] = 0

        # Urutkan berdasarkan skor rekomendasi
        merged = merged.sort_values(by="recommendation_score", ascending=False).reset_index(drop=True)

        return merged

# --- Contoh penggunaan ---
cbf_science_prox = CBFSystemNormalizedProximity(
    df_science, 
    df_passing_grade[df_passing_grade["type"]=="science"]
)

result_sci = cbf_science_prox.retrieve(user_id=1, top_n=5)
recommend_sci = cbf_science_prox.recommend_prodi(result_sci)

print(
    recommend_sci[
        ["id_user","avg_score","similarity","nama_prodi","rataan","min_val","max_val","score_rel","score","recommendation_score"]
    ].head(10)
)












