from multiprocessing import Pool, cpu_count
from datetime import datetime, timedelta
from utils.loader import load_data
from services.cbf_service import CBFSystemNormalizedProximity
from services.cbr_service import get_cbr_recommendation
from services.hybrid_service import get_hybrid_recommendation
from services.save_temp_service import save_temp_recommendations_to_db
from apscheduler.schedulers.background import BackgroundScheduler

def generate_for_user(user, df_scores_list, df_passing_list, top_n, expired_at):
    user_id = user["id_user"]
    track = user.get("track", "science")

    # --- CBR ---
    recs_cbr = get_cbr_recommendation(user_id, track, df_scores_list, df_passing_list, top_n)
    if recs_cbr:  # hanya simpan jika ada rekomendasi
        save_temp_recommendations_to_db(user_id, recs_cbr, "CBR", track, expired_at)

    # --- Hybrid ---
    recs_hybrid = get_hybrid_recommendation(user_id, track, df_scores_list, df_passing_list, top_n)
    if recs_hybrid:  # hanya simpan jika ada rekomendasi
        save_temp_recommendations_to_db(user_id, recs_hybrid, "HYBRID", track, expired_at)

def generate_all_recommendations(top_n=10):
    print(f"[Scheduler] Start generating recommendations at {datetime.now()}")
    science_data, humanities_data, passing_data = load_data()
    expired_at = datetime.now() + timedelta(hours=1)

    tracks = {"science": science_data, "humanities": humanities_data}

    # --- CBF per user (filter sudah termasuk di CBFService) ---
    for track_name, scores_df in tracks.items():
        df_scores_list = scores_df.to_dict(orient="records")
        cbf = CBFSystemNormalizedProximity(df_scores_list, passing_data)

        for user in df_scores_list:
            user_id = user["id_user"]
            sim_df = cbf.retrieve(user_id, top_n)
            recs_cbf = cbf.recommend_prodi(sim_df)

            if not recs_cbf.empty:  # hanya simpan jika ada rekomendasi
                save_temp_recommendations_to_db(user_id, recs_cbf.to_dict(orient="records"), "CBF", track_name, expired_at)

    # --- CBR & Hybrid per user ---
    tasks = []
    for track_name, scores_df in tracks.items():
        df_scores_list = scores_df.to_dict(orient="records")
        for user in df_scores_list:
            user["track"] = track_name
            tasks.append((user, df_scores_list, passing_data, top_n, expired_at))

    # Gunakan multiprocessing
    with Pool(cpu_count()) as pool:
        pool.starmap(generate_for_user, tasks)

    print(f"[Scheduler] Finished generating recommendations at {datetime.now()}")

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(generate_all_recommendations, 'interval', hours=1)
    scheduler.start()
    print("[Scheduler] APScheduler started. Recommendations auto-generate setiap 1 jam")

    # langsung jalankan sekali saat startup
    generate_all_recommendations()

