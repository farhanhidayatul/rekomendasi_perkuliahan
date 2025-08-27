import mysql.connector
from typing import List, Dict

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Astagfirullah123#",
        database="rekomendasi_perkuliahan"
    )

def save_recommendations_to_db(user_id: int, recommendations: List[Dict], method: str, permanent: bool = False):
    """
    Simpan hasil rekomendasi ke DB.
    Jika permanent=False -> simpan ke recommendations_temp
    Jika permanent=True -> simpan ke recommendations
    """
    conn = get_connection()
    cursor = conn.cursor()

    table = "recommendations" if permanent else "recommendations_temp"

    # Insert satu per satu
    for rec in recommendations:
        cursor.execute(f"""
            INSERT INTO {table} 
            (id_user, nama_prodi, avg_score, similarity, rataan, score_rel, recommendation_score, method)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            user_id,
            rec.get("nama_prodi"),
            rec.get("avg_score"),
            rec.get("similarity"),
            rec.get("rataan"),
            rec.get("score_rel"),
            rec.get("recommendation_score"),
            method
        ))

    conn.commit()
    cursor.close()
    conn.close()
