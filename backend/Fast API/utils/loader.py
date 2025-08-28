# backend/utils/loader.py
import pandas as pd
from utils.db import get_connection

def fetch_df(query: str) -> pd.DataFrame:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    columns = cursor.column_names  # ambil nama kolom
    cursor.close()
    conn.close()
    return pd.DataFrame(rows, columns=columns)

def load_science_scores() -> pd.DataFrame:
    return fetch_df("SELECT * FROM science_scores")

def load_humanities_scores() -> pd.DataFrame:
    return fetch_df("SELECT * FROM humanities_scores")

def load_passing_data() -> pd.DataFrame:
    return fetch_df("SELECT * FROM passing_grade")

# jika mau langsung semua sekaligus
def load_all():
    return load_science_scores(), load_humanities_scores(), load_passing_data()
