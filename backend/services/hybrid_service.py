# hybrid_service.py
from typing import List, Dict
from services.cbf_service import CBFSystemNormalizedProximity
from services.cbr_service import get_cbr_recommendation

def get_hybrid_recommendation(user_id: int,
                              track: str,
                              scores: List[Dict],
                              passing: List[Dict],
                              top_n: int = 5,
                              weight_cbf: float = 0.5,
                              weight_cbr: float = 0.5) -> List[Dict]:
    """
    Hybrid ensemble: gabungan skor dari CBF + CBR (per user).
    """

    # --- CBF ---
    cbf = CBFSystemNormalizedProximity(scores, passing)
    cbf_sim = cbf.retrieve(user_id, top_n=top_n)
    cbf_recs = cbf.recommend_prodi(cbf_sim)
    cbf_map = {r["nama_prodi"]: r for r in cbf_recs.to_dict(orient="records")}

    # --- CBR ---
    cbr_recs = get_cbr_recommendation(user_id, track, scores, passing, top_n=top_n)
    cbr_map = {r["nama_prodi"]: r for r in cbr_recs}

    # --- Merge ---
    merged = {}
    for name, row in cbf_map.items():
        merged[name] = {
            **row,
            "cbf_score": float(row.get("recommendation_score", 0) or 0),
            "cbr_score": 0.0
        }

    for name, row in cbr_map.items():
        if name not in merged:
            merged[name] = {**row, "cbf_score": 0.0}
        merged[name]["cbr_score"] = float(row.get("recommendation_score", 0) or 0)

    # --- Hitung Hybrid Score ---
    results = []
    for name, row in merged.items():
        cbf_score = row.get("cbf_score", 0)
        cbr_score = row.get("cbr_score", 0)
        hybrid_score = round(weight_cbf * cbf_score + weight_cbr * cbr_score, 2)

        results.append({
            **row,
            "cbf_score": round(cbf_score, 2),
            "cbr_score": round(cbr_score, 2),
            "hybrid_score": hybrid_score,
            "source": ("CBF+CBR" if cbf_score and cbr_score else
                       "CBF only" if cbf_score else
                       "CBR only")
        })

    # Urutkan berdasarkan hybrid_score
    results = sorted(results, key=lambda x: x["hybrid_score"], reverse=True)[:top_n]
    return results


