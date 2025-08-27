from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import pandas as pd

from utils.loader import load_data
from services.cbf_service import CBFSystemNormalizedProximity
from services.cbr_service import get_cbr_recommendation
from services.hybrid_service import get_hybrid_recommendation
from services.save_temp_service import save_temp_recommendations_to_db, fetch_temp_recommendations
from scheduler import start_scheduler

app = FastAPI(title="Rekomendasi Perkuliahan API")

# ================= ENABLE CORS =================
origins = ["http://localhost:3000", "http://127.0.0.1:3000", "*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# # ================= SCHEDULER =================
# @app.on_event("startup")
# def startup_event():
#     start_scheduler()

# ================= Helper =================
def safe_to_list_of_dict(df_or_list):
    if hasattr(df_or_list, "to_dict"):
        return df_or_list.to_dict(orient="records")
    elif isinstance(df_or_list, list):
        result = []
        for row in df_or_list:
            if isinstance(row, dict):
                result.append(row)
        return result
    return []

# ================= CBF SINGLE USER =================
@app.get("/recommend/cbf/{user_id}")
def recommend_cbf_user(user_id: int, top_n: int = 20, save: bool = True, track: str = "science"):
    try:
        science_data, humanities_data, passing_data = load_data()

        # pilih dataset sesuai track
        df_scores = science_data if track == "science" else humanities_data
        df_scores_list = safe_to_list_of_dict(df_scores)
        df_pg = [row for row in safe_to_list_of_dict(passing_data) if row.get("type") == track]

        cbf = CBFSystemNormalizedProximity(df_scores_list, df_pg)
        sim_df = cbf.retrieve(user_id, top_n=top_n)
        recs = cbf.recommend_prodi(sim_df)
        recs_list = recs.to_dict(orient="records") if not recs.empty else []

        if save and recs_list:
            expired_at = datetime.now() + timedelta(hours=1)
            save_temp_recommendations_to_db(user_id, recs_list, "CBF", track, expired_at)

        return recs_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CBF Error: {str(e)}")


# ================= CBR SINGLE USER =================
@app.get("/recommend/cbr/{user_id}")
def recommend_cbr_user(user_id: int, top_n: int = 20, save: bool = True, track: str = "science"):
    try:
        science_data, humanities_data, passing_data = load_data()
        df_scores = science_data if track == "science" else humanities_data
        df_scores_list = safe_to_list_of_dict(df_scores)
        df_passing_list = safe_to_list_of_dict(passing_data)

        recs = get_cbr_recommendation(user_id, track, df_scores_list, df_passing_list, top_n=top_n)
        for r in recs:
            r["id_user"] = user_id

        if save and recs:
            expired_at = datetime.now() + timedelta(hours=1)
            save_temp_recommendations_to_db(user_id, recs, "CBR", track, expired_at)

        return recs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CBR Error: {str(e)}")


# ================= HYBRID SINGLE USER =================
@app.get("/recommend/hybrid/{user_id}")
def recommend_hybrid_user(
    user_id: int, top_n: int = 20,
    weight_cbf: float = 0.5, weight_cbr: float = 0.5,
    save: bool = True, track: str = "science"
):
    try:
        science_data, humanities_data, passing_data = load_data()
        df_scores = science_data if track == "science" else humanities_data
        df_scores_list = safe_to_list_of_dict(df_scores)
        df_passing_list = safe_to_list_of_dict(passing_data)

        recs = get_hybrid_recommendation(
            user_id, track, df_scores_list, df_passing_list,
            top_n=top_n, weight_cbf=weight_cbf, weight_cbr=weight_cbr
        )
        for r in recs:
            r["id_user"] = user_id

        if save and recs:
            expired_at = datetime.now() + timedelta(hours=1)
            save_temp_recommendations_to_db(user_id, recs, "HYBRID", track, expired_at)

        return recs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hybrid Error: {str(e)}")


# ================= TEMP RECOMMENDATION =================
@app.get("/recommend/temp/{user_id}")
def get_temp_recommendation(user_id: int, method: str = "HYBRID", track: str = "science"):
    recs = fetch_temp_recommendations(user_id, method, track)
    if not recs:
        raise HTTPException(status_code=404, detail="Rekomendasi sementara tidak ditemukan")
    return {
        "id_user": user_id,
        "method": method.upper(),
        "track": track.lower(),
        "data": recs
    }
