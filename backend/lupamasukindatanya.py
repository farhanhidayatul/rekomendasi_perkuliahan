import pandas as pd
from sqlalchemy import create_engine, text

# 1. Load CSV
passing_grade = pd.read_csv("./data/passing-grade.csv")

# 2. Rename PTN -> name_university
pg_filtered = passing_grade.rename(columns={"PTN": "name_university"})

# 3. Koneksi database
engine = create_engine("mysql+pymysql://root:Astagfirullah123#@localhost:3306/rekomendasi_perkuliahan")

# 4. Update kolom name_university berdasarkan id_prodi
with engine.begin() as conn:
    for idx, val in enumerate(pg_filtered["name_university"], start=1):
        conn.execute(
            text("UPDATE passing_grade SET name_university = :val WHERE id_prodi = :id"),
            {"val": val, "id": idx}
        )

print("✅ Kolom name_university berhasil diupdate sesuai urutan id_prodi")
