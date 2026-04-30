# backend/legacy_stats.py
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/api/mission_stats")
def calc_stats(data: dict):
    # Smell 1:
    try:
        t = data["type"]
        d = data["dist"]
        b = data["batt"]
        payload = data.get("payload_weight", 0)
    except KeyError:
        raise HTTPException(status_code=400, detail="Missing required data")

    score = 0
    status = "unknown"

    # Smell 2:
    if t == 1:
        status = "recon"
        if d > 0 and b > 0:
            score = (d * 10) / b
        else:
            score = 0

        # Smell 3: Duplicated capping logic
        if score > 100:
            score = 100

    elif t == 2:
        status = "transport"
        if d > 0 and b > 0:
            score = (d * 5) / b
            if payload > 50:
                score = score - (payload * 0.1)
        else:
            score = 0

        if score > 100:
            score = 100

    else:
        return {"status": "error", "msg": "invalid mission type"}

    # Smell 4:
    query = f"INSERT INTO stats (mission, score) VALUES ('{status}', {score})"
    print(f"[DB LOG] {query}")

    return {"status": "success", "mission": status, "final_score": round(score, 2)}
