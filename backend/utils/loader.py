# backend/utils/loader.py
import pandas as pd
from utils.db import get_connection

def load_data():
    conn = get_connection()
    cursor = conn.cursor()

    def fetch_df(query: str):
        cursor.execute(query)
        rows = cursor.fetchall()
        return pd.DataFrame(rows)

    df_science = fetch_df("SELECT * FROM science_scores")
    df_humanities = fetch_df("SELECT * FROM humanities_scores")
    df_passing = fetch_df("SELECT * FROM passing_grade")

    cursor.close()
    conn.close()
    return df_science, df_humanities, df_passing


