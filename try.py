import pandas as pd
import re

# Load data
df = pd.read_csv("./backend/data/passing-grade.csv")

# --- Mapping resmi berdasarkan sumber web ---
mapping_official = {
    # Science / Saintek
    "ILMU KOMPUTER": "science",
    "SEKOLAH TEK. ELEKTRO & INFORMATIKA (STEI)": "science",
    "FAKULTAS TEKNOLOGI INDUSTRI (FTI) - KAMPUS GANESA": "science",
    "FAKULTAS TEKNOLOGI INDUSTRI (FTI) - KAMPUS CIREBON": "science",
    "FAKULTAS TEKNOLOGI INDUSTRI (FTI) - KAMPUS JATINANGOR": "science",
    "INFORMATIKA": "science",
    "SEKOLAH ILMU & TEKNO. HAYATI - PROG. SAINS": "science",
    "SEKOLAH ILMU & TEKNO HAYATI - PROG REKAYASA": "science",
    "PEND. DOKTER": "science",
    "ELEKTRONIKA DAN INSTRUMENTASI": "science",
    "TEKNOBIOMEDIK": "science",
    "ILMU TANAH": "science",
    "AGRONOMI DAN HORTIKULTURA": "science",
    "PROTEKSI TANAMAN (ILMU HAMA DAN PENYAKIT TUMBUHAN)": "science",
    "ILMU LINGKUNGAN": "science",
    "ILMU KELAUTAN": "science",
    "OCEANOGRAFI": "science",
    "SISTEM KOMPUTER": "science",
    "FISIOTERAPI": "science",
    "KEBIDANAN": "science",
    "HIGIENE GIGI": "science",
    "AKUAKULTUR": "science",
    "INSTRUMENTASI": "science",
    "METEOROLOGI TERAPAN": "science",
    "SISTEM INFORMASI": "science",
    "TEKNOLOGI INFORMASI": "science",
    "TEKNOLOGI BIOPROSES": "science",
    "TEKNOLOGI PANGAN": "science",
    "ILMU DAN TEKNOLOGI PANGAN": "science",
    "NUTRISI DAN TEKNOLOGI PAKAN": "science",
    "TEKNOLOGI HASIL TERNAK": "science",
    "TEKNOLOGI HASIL PERAIRAN": "science",
    "AGROTEKNOLOGI": "science",
    "TEK. SIST PERKAPALAN (GLR GANDA ITS-JERMAN)": "science",

    # Humanities / Soshum
    "SEK. ARSITEKTUR. PERENC & PENGEMB KEBIJAKAN": "humanities",
    "ARSITEKTUR": "humanities",
    "PERENCANAAN WILAYAH DAN KOTA": "humanities",
    "DESAIN KOMUNIKASI VISUAL": "humanities",
    "DESAIN INTERIOR": "humanities",
    "DESAIN PRODUK INDUSTRI": "humanities",
    "KOMUNIKASI DAN PENGEMBANGAN MASYARAKAT": "humanities",
    "PEMBANGUNAN WILAYAH": "humanities",
    "PENYULUHAN DAN KOMUNIKASI PERTANIAN": "humanities",
    "ILMU KELUARGA DAN KONSUMEN": "humanities",
    "BISNIS": "humanities"
}

# --- Keyword lists ---
science_keywords = [
    "KEDOKTERAN", "DOKTER", "TEKNIK", "SAINS", "HAYATI", "FARMASI", "APOTEKER",
    "KIMIA", "BIOLOGI", "MATEMATIKA", "FISIKA", "STATISTIKA", "GEOFISIKA",
    "INFORMATIKA", "KOMPUTER", "ELEKTRO", "MESIN", "INDUSTRI", "SIPIL",
    "LINGKUNGAN", "PERENCANAAN WILAYAH", "GEOGRAFI", "PERTANIAN",
    "KEHUTANAN", "PERIKANAN", "KELAUTAN", "PETERNAKAN", "GIZI", "KESEHATAN",
    "BIDAN", "NERS", "KEBIDANAN", "FISIOTERAPI", "HIGIENE", "ILMU TANAH",
    "PROTEKSI TANAMAN", "SILVIKULTUR", "KARTOGRAFI", "PENGINDERAAN JAUH",
    "TEKNOBIOMEDIK", "METEOROLOGI", "OCEANOGRAFI", "AKUAKULTUR", "NUTRISI",
    "TEKNOLOGI HASIL"
]

humanities_keywords = [
    "HUKUM", "EKONOMI", "MANAJEMEN", "AKUNTANSI", "ILMU POLITIK",
    "ILMU KOMUNIKASI", "PSIKOLOGI", "SASTRA", "BAHASA", "SEJARAH",
    "ANTROPOLOGI", "SOSIOLOGI", "FILSAFAT", "HUBUNGAN INTERNASIONAL",
    "PARIWISATA", "ADMINISTRASI", "ILMU KELUARGA", "PENYULUHAN",
    "PEMBANGUNAN WILAYAH", "DESAIN", "KOMUNIKASI"
]

# --- Cleaning function ---
def clean_text(text):
    text = str(text).upper()
    text = re.sub(r'[&/,-]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# --- Classification function ---
def classify_prodi(prodi):
    prodi_clean = clean_text(prodi)
    
    # Mapping resmi dulu (exact match)
    for key, value in mapping_official.items():
        if clean_text(key) in prodi_clean:
            return value
    
    # Keyword check untuk sisa
    if any(kw in prodi_clean for kw in science_keywords):
        return "science"
    if any(kw in prodi_clean for kw in humanities_keywords):
        return "humanities"
    
    # Default fallback jika tidak match sama sekali
    return "unknown"

# --- Apply classification ---
df["type"] = df["NAMA PRODI"].apply(classify_prodi)

# --- Pastikan tidak ada unknown ---
# Jika masih unknown, isi berdasarkan keyword
df["type"] = df["type"].replace("unknown", "")

# --- Cek hasil ---
unknown_count = (df["type"] == "").sum()
print(f"Jumlah prodi yang masih belum terklasifikasi: {unknown_count}")
if unknown_count > 0:
    print(df[df["type"] == ""][["NO", "PTN", "NAMA PRODI"]])

null_type = df['type'].isnull().sum()
print(f"Jumlah nilai null di kolom 'type': {null_type}")

nan_counts = df.isna().sum()
print("Jumlah NaN per kolom:")
print(nan_counts)

# # --- Optionally, save cleaned file ---
# df.to_csv("./backend/data/passing-grade.csv", index=False)
