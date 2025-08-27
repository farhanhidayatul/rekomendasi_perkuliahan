// backend/routes/dataRoutes.js
const express = require("express");
const router = express.Router();

// 🔹 Pastikan koneksi db sudah di-require dari index.js atau db.js

// Ambil data dari tiap tabel
router.get("/humanities", async (req, res) => {
    try {
        const [rows] = await db.execute("SELECT * FROM humanities_scores");
        res.json(rows);
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: "DB Error" });
    }
});

router.get("/science", async (req, res) => {
    try {
        const [rows] = await db.execute("SELECT * FROM science_scores");
        res.json(rows);
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: "DB Error" });
    }
});

router.get("/universities", async (req, res) => {
    try {
        const [rows] = await db.execute("SELECT * FROM universitys");
        res.json(rows);
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: "DB Error" });
    }
});

router.get("/grades", async (req, res) => {
    try {
        const [rows] = await db.execute("SELECT * FROM parsing_grade");
        res.json(rows);
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: "DB Error" });
    }
});

module.exports = router;

