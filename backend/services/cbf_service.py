import pandas as pd
from typing import List, Dict

class CBFSystemNormalizedProximity:
    def __init__(self, scores: List[Dict], passing: List[Dict]):
        self.df_scores = pd.DataFrame(scores)
        self.df_passing = pd.DataFrame(passing)

    def retrieve(self, user_id: int, top_n: int = 10) -> pd.DataFrame:
        """Hitung similarity sederhana (contoh)."""
        if user_id not in self.df_scores["id_user"].values:
            return pd.DataFrame()
        user_row = self.df_scores[self.df_scores["id_user"] == user_id].iloc[0]

        # Contoh: skor random (disesuaikan nanti dgn logika proximity sebenarnya)
        self.df_passing["recommendation_score"] = (
            self.df_passing.index.to_series().rank(pct=True).values[::-1]
        )

        return self.df_passing.sort_values("recommendation_score", ascending=False).head(top_n)

    def recommend_prodi(self, user_id: int, top_n: int = 10) -> List[Dict]:
        sim_df = self.retrieve(user_id, top_n=top_n)
        return sim_df.to_dict(orient="records") if not sim_df.empty else []
