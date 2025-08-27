from flask import Blueprint, request, jsonify
import numpy as np

bp = Blueprint("recommendations", __name__)

all_results = None
all_results_idx = None

def init_routes(results):
    global all_results, all_results_idx
    all_results = results
    if "id_user_input" in all_results.columns:
        all_results_idx = all_results.set_index("id_user_input")
    else:
        all_results_idx = all_results.copy()
        all_results_idx["id_user_input"] = all_results_idx.get("id_user_input", np.nan)
        all_results_idx = all_results_idx.set_index("id_user_input")

@bp.route("/recommendations", methods=["GET"])
def recommendations():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))
    df = all_results

    track = request.args.get("track")
    if track:
        df = df[df["track"] == track]

    min_sim = request.args.get("min_sim")
    if min_sim is not None and "similarity" in df.columns:
        try:
            thr = float(min_sim)
            df = df[df["similarity"] >= thr]
        except ValueError:
            pass

    total = len(df)
    start = (page - 1) * per_page
    end = start + per_page
    data_slice = df.iloc[start:end]

    return jsonify({
        "total": int(total),
        "page": int(page),
        "per_page": int(per_page),
        "data": data_slice.to_dict(orient="records"),
    })

@bp.route("/recommendations/<int:user_id>", methods=["GET"])
def recommendations_by_user(user_id: int):
    if user_id not in all_results_idx.index:
        return jsonify({"message": "User ID tidak ditemukan"}), 404
    user_df = all_results_idx.loc[[user_id]].reset_index()
    return jsonify(user_df.to_dict(orient="records"))
