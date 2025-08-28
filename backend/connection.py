import mysql.connector
import pandas as pd
import numpy as np

# =====================
# 1. Load CSV
# =====================
file_path_humanities = '../backend/data/score_humanities.csv'
file_path_science = '../backend/data/score_science.csv'
file_path_major = '../backend/data/majors.csv'
file_path_universitas = '../backend/data/universities.csv'
file_path_parsing_grade = '../backend/data/passing-grade.csv'

data_humanities = pd.read_csv(file_path_humanities)
data_science = pd.read_csv(file_path_science)

data_major = pd.read_csv(file_path_major)
data_major = data_major[["id_university", "type", "major_name", "capacity"]]

data_universitas = pd.read_csv(file_path_universitas)

data_parsing_grade = pd.read_csv(file_path_parsing_grade)
data_parsing_grade = data_parsing_grade[["NAMA PRODI", "RATAAN", "type","MIN", "MAX"]]

# Hapus kolom Unnamed (jika ada)
for df in [data_humanities, data_science, data_major, data_universitas, data_parsing_grade]:
    df.drop(columns=[col for col in df.columns if "Unnamed" in col], inplace=True, errors="ignore")

# Penggabungan data antara major dengan universitas
data_major_univ = pd.merge(
    data_major,
    data_universitas,
    on="id_university",
    how="inner"
)

# =====================
# 2. Konversi NaN ke None
# =====================
data_humanities = data_humanities.replace({np.nan: None})
data_science = data_science.replace({np.nan: None})
data_major_univ = data_major_univ.replace({np.nan: None})
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

    # =====================
    # 4. Insert Data
    # =====================

    # --- Insert Humanities ---
    for _, row in data_humanities.iterrows():
        cursor.execute("""
            INSERT INTO humanities_scores (
                score_eko, score_geo, score_kmb, score_kpu, score_kua, 
                score_mat, score_ppu, score_sej, score_sos
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            to_python(row["score_eko"]),
            to_python(row["score_geo"]),
            to_python(row["score_kmb"]),
            to_python(row["score_kpu"]),
            to_python(row["score_kua"]),
            to_python(row["score_mat"]),
            to_python(row["score_ppu"]),
            to_python(row["score_sej"]),
            to_python(row["score_sos"]),
        ))

    # --- Insert Science ---
    for _, row in data_science.iterrows():
        cursor.execute("""
            INSERT INTO science_scores (
                score_bio, score_fis, score_kim, score_kmb, score_kpu,
                score_kua, score_mat, score_ppu
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            to_python(row["score_bio"]),
            to_python(row["score_fis"]),
            to_python(row["score_kim"]),
            to_python(row["score_kmb"]),
            to_python(row["score_kpu"]),
            to_python(row["score_kua"]),
            to_python(row["score_mat"]),
            to_python(row["score_ppu"]),
        ))

    # --- Insert Major + Universitas ---
    for _, row in data_major_univ.iterrows():
        cursor.execute("""
            INSERT INTO universitys (
                type, major_name, capacity, university_name
            ) VALUES (%s,%s,%s,%s)
        """, (
            to_python(row["type"]),
            to_python(row["major_name"]),
            to_python(row["capacity"]),
            to_python(row["university_name"]),
        ))

    # --- Insert Passing Grade ---
    for _, row in data_parsing_grade.iterrows():
        cursor.execute("""
            INSERT INTO passing_grade (
                nama_prodi, rataan, s_baku, min_val, max_val
            ) VALUES (%s,%s,%s,%s,%s)
        """, (
            to_python(row["NAMA PRODI"]),
            to_python(row["RATAAN"]),
            to_python(row["S.BAKU"]),
            to_python(row["MIN"]),
            to_python(row["MAX"]),
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

