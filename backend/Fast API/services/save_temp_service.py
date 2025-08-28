# backend/services/save_temp_service.py
import json
from datetime import datetime
from utils.db import get_connection

def save_temp_recommendations_to_db(user_id: int, recommendations: list, method: str, track: str, expired_at: datetime):
    """
    Simpan rekomendasi sementara ke table temp_recommendations.
    """
    conn = get_connection()
    cursor = conn.cursor()

    recommendations_json = json.dumps(recommendations, default=str)

    query = """
        INSERT INTO temp_recommendations (id_user, method, track, recommendations, created_at, expired_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            recommendations = VALUES(recommendations),
            created_at = VALUES(created_at),
            expired_at = VALUES(expired_at)
    """

    now = datetime.now()
    cursor.execute(query, (
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
    print(f"[Temp Save] User {user_id}, Method {method}, Track {track}, {len(recommendations)} recommendations saved.")


def fetch_temp_recommendations(user_id: int, method: str, track: str):
    """
    Ambil rekomendasi sementara dari table temp_recommendations.
    Hanya mengembalikan rekomendasi yang belum expired.
    """
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now()

    query = """
        SELECT recommendations
        FROM temp_recommendations
        WHERE id_user = %s AND method = %s AND track = %s AND (expired_at IS NULL OR expired_at > %s)
        LIMIT 1
    """

    cursor.execute(query, (user_id, method.upper(), track.lower(), now))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row and row[0]:
        try:
            return json.loads(row[0])
        except json.JSONDecodeError:
            return []
    return []

