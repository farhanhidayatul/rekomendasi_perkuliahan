// index.js
const express = require("express");
const cors = require("cors");
const mysql = require("mysql2/promise");
const axios = require("axios");

const app = express();
app.use(cors());
app.use(express.json());

// =========================================================
// 🔹 Koneksi MySQL
// =========================================================
const dbConfig = {
  host: "localhost",
  user: "root",
  password: "Astagfirullah123#",
  database: "rekomendasi_perkuliahan",
};

async function getConnection() {
  return mysql.createConnection(dbConfig);
}

// =========================================================
// 1. Ambil data mentah (humanities, science, passing grade)
// =========================================================
app.get("/api/humanities", async (req, res) => {
  try {
    const conn = await getConnection();
    const [rows] = await conn.execute("SELECT * FROM humanities_scores");
    await conn.end();
    res.json(rows);
  } catch (err) {
    console.error("❌ Error /api/humanities:", err);
    res.status(500).json({ error: "DB Error" });
  }
});

app.get("/api/science", async (req, res) => {
  try {
    const conn = await getConnection();
    const [rows] = await conn.execute("SELECT * FROM science_scores");
    await conn.end();
    res.json(rows);
  } catch (err) {
    console.error("❌ Error /api/science:", err);
    res.status(500).json({ error: "DB Error" });
  }
});

app.get("/api/passing-grade", async (req, res) => {
  try {
    const conn = await getConnection();
    const [rows] = await conn.execute("SELECT * FROM passing_grade");
    await conn.end();
    res.json(rows);
  } catch (err) {
    console.error("❌ Error /api/passing-grade:", err);
    res.status(500).json({ error: "DB Error" });
  }
});

// =========================================================
// 2. Ambil rekomendasi (cache dari DB + pagination)
// =========================================================
app.get("/api/recommendations/:user_id", async (req, res) => {
  const { user_id } = req.params;
  const { method = "cbf", track = "science", page = 1, size = 20 } = req.query;
  const offset = (page - 1) * size;

  try {
    const conn = await getConnection();
    const [rows] = await conn.execute(
      `SELECT recommendations, created_at, expired_at
       FROM temp_recommendations
       WHERE id_user = ? AND method = ? AND track = ?
       ORDER BY created_at DESC
       LIMIT 1`,
      [user_id, method.toLowerCase(), track.toLowerCase()]
    );
    await conn.end();

    if (!rows.length) {
      return res.json({ id_user, recommendations: [] });
    }

    const expiredAt = rows[0].expired_at ? new Date(rows[0].expired_at) : null;
    if (expiredAt && new Date() > expiredAt) {
      return res.json({ id_user, recommendations: [] });
    }

    let recommendations = [];
    try {
      recommendations = JSON.parse(rows[0].recommendations || "[]");
    } catch (e) {
      recommendations = [];
    }

    const totalPages = Math.ceil(recommendations.length / size);
    const paginated = recommendations.slice(offset, offset + Number(size));

    res.json({
      id_user,
      method: method.toLowerCase(),
      track: track.toLowerCase(),
      page: Number(page),
      size: Number(size),
      total_pages: totalPages,
      recommendations: paginated,
    });
  } catch (err) {
    console.error("❌ Error /api/recommendations:", err);
    res.status(500).json({ error: "Gagal ambil rekomendasi" });
  }
});

// =========================================================
// 3. Proxy ke FastAPI untuk generate rekomendasi
// =========================================================
app.post("/recommendations", async (req, res) => {
  try {
    const response = await axios.post("http://127.0.0.1:8000/recommendations", req.body, {
      headers: { "Content-Type": "application/json" },
    });
    res.json(response.data);
  } catch (err) {
    console.error("❌ FastAPI Error:", err.message);
    res.status(500).json({
      error: "FastAPI Error",
      detail: err.response?.data || err.message,
    });
  }
});

// =========================================================
// 4. Refresh cache di FastAPI
// =========================================================
app.post("/api/refresh", async (req, res) => {
  try {
    const response = await axios.post("http://127.0.0.1:8000/refresh");
    res.json(response.data);
  } catch (err) {
    console.error("❌ FastAPI Refresh Error:", err.message);
    res.status(500).json({
      error: "FastAPI Refresh Error",
      detail: err.response?.data || err.message,
    });
  }
});

// =========================================================
// 5. Hitung ulang rekomendasi manual via FastAPI
// =========================================================
app.get("/api/recommendations/refresh/:user_id", async (req, res) => {
  const { user_id } = req.params;
  const { method, track, top_n} = req.query;

  try {
    const url = `http://127.0.0.1:8000/recommend/temp/${user_id}?method=${method}&track=${track}&top_n=${top_n}`;
    const response = await axios.get(url);
    res.json(response.data);
  } catch (err) {
    console.error("❌ Error refresh rekomendasi:", err.message);
    res.status(500).json({ error: "Gagal hitung ulang rekomendasi" });
  }
});

// =========================================================
// 6. Simpan permanen rekomendasi dari cache → DB
// =========================================================
app.post("/api/recommendations/save-permanent", async (req, res) => {
  const { id_user, track, method = "cbf" } = req.body;
  if (!id_user || !track) {
    return res.status(400).json({ error: "id_user dan track wajib diisi" });
  }

  try {
    const conn = await getConnection();
    const [rows] = await conn.execute(
      `SELECT recommendations 
       FROM temp_recommendations
       WHERE id_user = ? AND track = ? AND method = ?
       ORDER BY created_at DESC LIMIT 1`,
      [id_user, track.toLowerCase(), method.toLowerCase()]
    );

    if (!rows.length) {
      return res.status(404).json({ error: "Tidak ada rekomendasi sementara" });
    }

    let recommendations = [];
    try {
      recommendations = JSON.parse(rows[0].recommendations || "[]");
    } catch (e) {
      recommendations = [];
    }

    for (const rec of recommendations) {
      await conn.execute(
        `INSERT INTO recommendations 
         (id_user, track, nama_prodi, avg_score, similarity, rataan, score_rel, recommendation_score)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
        [
          id_user,
          track.toLowerCase(),
          rec.nama_prodi || "",
          rec.avg_score || 0,
          rec.similarity || 0,
          rec.rataan || 0,
          rec.score_rel || 0,
          rec.recommendation_score || 0,
        ]
      );
    }

    await conn.end();
    res.json({ success: true, message: "Rekomendasi berhasil disimpan permanen" });
  } catch (err) {
    console.error("❌ Error save permanent:", err);
    res.status(500).json({ error: "Gagal menyimpan permanen" });
  }
});

// =========================================================
// 7. Auto-clean cache setiap 60 menit
// =========================================================
setInterval(async () => {
  try {
    const conn = await getConnection();
    const [result] = await conn.execute(
      `DELETE FROM temp_recommendations
       WHERE expired_at IS NOT NULL AND expired_at < NOW()`
    );
    await conn.end();
    if (result.affectedRows > 0) {
      console.log(`🧹 Cache dibersihkan: ${result.affectedRows} baris`);
    }
  } catch (err) {
    console.error("❌ Error cleaning cache:", err.message);
  }
}, 60 * 60 * 1000);

// =========================================================
// Jalankan server
// =========================================================
app.listen(5000, () => console.log("🚀 Node.js backend running on port 5000"));

