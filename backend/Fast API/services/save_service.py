# backend/services/save_service.py
import json
from datetime import datetime
from typing import List, Dict
from utils.db import get_connection

def save_recommendations_to_db(
    user_id: int,
    recommendations: List[Dict],
    method: str,
    track: str,
    permanent: bool = False,
    expired_at: datetime = None
):
    """
    Simpan hasil rekomendasi ke DB.
    - permanent=False -> simpan ke temp_recommendations
    - permanent=True  -> simpan ke recommendations
    """
    conn = get_connection()
    cursor = conn.cursor()

    table = "recommendations" if permanent else "temp_recommendations"
    now = datetime.now()

    if permanent:
        for rec in recommendations:
            cursor.execute(f"""
                INSERT INTO {table} 
                (id_user, nama_prodi, track, avg_score, similarity, rataan, score_rel, recommendation_score, method, created_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                user_id,
                rec.get("nama_prodi"),
                track,
                rec.get("avg_score"),
                rec.get("similarity"),
                rec.get("rataan"),
                rec.get("score_rel"),
                rec.get("recommendation_score"),
                method.upper(),
                now
            ))
    else:
        recommendations_json = json.dumps(recommendations, default=str)
        cursor.execute(f"""
            INSERT INTO {table} 
            (id_user, method, track, recommendations, created_at, expired_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                recommendations = VALUES(recommendations),
                created_at = VALUES(created_at),
                expired_at = VALUES(expired_at)
        """, (
            user_id,
            method.upper(),
            track.lower(),
            recommendations_json,
            now,
            expired_at
        ))

    conn.commit()
    cursor.close()
    conn.close()

