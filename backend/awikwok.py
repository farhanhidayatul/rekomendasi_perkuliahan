import mysql.connector
import pandas as pd
import numpy as np

# =====================
# 1. Load CSV
# =====================

file_path_parsing_grade = '../backend/data/passing_grade.csv'
data_parsing_grade = pd.read_csv(file_path_parsing_grade)
data_parsing_grade = data_parsing_grade[["nama_prodi", "name_university", "type","rataan","min_val", "max_val"]]

# Hapus kolom Unnamed (jika ada)
for df in [data_parsing_grade]:
    df.drop(columns=[col for col in df.columns if "Unnamed" in col], inplace=True, errors="ignore")

# =====================
# 2. Konversi NaN ke None
# =====================
data_parsing_grade = data_parsing_grade.replace({np.nan: None})

# Helper untuk konversi numpy → python native
def to_python(val):
    return val.item() if hasattr(val, "item") else val

# =====================
# 3. Koneksi ke MySQL
# =====================
try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Astagfirullah123#",  # ganti password sesuai MySQL
        database="rekomendasi_perkuliahan"
    )
    cursor = conn.cursor()


    # --- Insert Passing Grade ---
    for _, row in data_parsing_grade.iterrows():
        cursor.execute("""
            INSERT INTO passing_grade (
                nama_prodi, name_university, type, rataan, min_val, max_val
            ) VALUES (%s,%s,%s,%s,%s,%s)
        """, (
            to_python(row["nama_prodi"]),
            to_python(row["name_university"]),
            to_python(row["type"]),
            to_python(row["rataan"]),
            to_python(row["min_val"]),
            to_python(row["max_val"]),
        ))

    # Commit perubahan
    conn.commit()
    print("✅ Semua data berhasil dimasukkan ke MySQL!")

except Exception as e:
    print("❌ Error:", e)

finally:
    if conn.is_connected():
        cursor.close()
        conn.close()