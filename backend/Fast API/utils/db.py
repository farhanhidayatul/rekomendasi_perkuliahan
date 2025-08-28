# backend/utils/db.py
import pymysql

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Astagfirullah123#",
    "database": "rekomendasi_perkuliahan",
    "port": 3306,
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor
}

def get_connection():
    """Membuat koneksi ke database MySQL"""
    return pymysql.connect(**DB_CONFIG)