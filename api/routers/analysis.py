from fastapi import APIRouter

from database import fetch_all, fetch_one
from schemas.statistics import TrainTypeComparison
from utils import ensure_db

router = APIRouter()


@router.get("/api/analysis/train-types-comparison", response_model=list[TrainTypeComparison])
def compare_train_types():
    ensure_db()
    query = """
        SELECT
            CASE WHEN is_night THEN 'night' ELSE 'day' END AS train_type,
            COUNT(*) AS train_count,
            COALESCE(AVG(distance_km), 0.0) AS avg_distance_km,
            COALESCE(AVG(co2_emissions), 0.0) AS avg_co2_emissions
        FROM facts_night_trains
        GROUP BY is_night
        ORDER BY train_type DESC
    """
    rows = fetch_all(query)
    reference_co2 = 1.0
    output = []
    for row in rows:
        avg_co2 = float(row["avg_co2_emissions"])
        efficiency = min(100.0, (reference_co2 / avg_co2) * 100.0) if avg_co2 > 0 else 0.0
        output.append(
            {
                "train_type": row["train_type"],
                "train_count": int(row["train_count"]),
                "avg_distance_km": float(row["avg_distance_km"]),
                "avg_co2_emissions": avg_co2,
                "efficiency_score": round(efficiency, 2),
            }
        )
    return output


@router.get("/api/analysis/policy-recommendations")
def get_policy_recommendations():
    ensure_db()
    top_emitters = fetch_all(
        """
        SELECT country_name, country_code, avg_co2_per_passenger
        FROM dashboard_metrics
        ORDER BY avg_co2_per_passenger DESC, country_name
        LIMIT 5
        """
    )
    best_country = fetch_one(
        """
        SELECT
            c.country_name,
            c.country_code,
            COALESCE(dm.avg_co2_per_passenger, 0.0) AS avg_co2_per_passenger,
            COUNT(f.fact_id) AS train_count
        FROM dim_countries c
        JOIN dashboard_metrics dm ON c.country_code = dm.country_code
        LEFT JOIN facts_night_trains f ON c.country_id = f.country_id
        GROUP BY c.country_id, c.country_name, c.country_code, dm.avg_co2_per_passenger
        ORDER BY dm.avg_co2_per_passenger ASC, train_count DESC
        LIMIT 1
        """
    )

    recommendations = []
    if top_emitters:
        recommendations.append(
            {
                "title": "Pays prioritaires pour l'optimisation carbone",
                "description": "Ces pays presentent les ratios moyens CO2 les plus eleves.",
                "countries": top_emitters,
                "suggestion": "Prioriser le renouvellement du materiel roulant et la hausse des dessertes ferroviaires longues distances.",
            }
        )

    if best_country:
        recommendations.append(
            {
                "title": "Bonnes pratiques a reproduire",
                "description": (
                    f"{best_country['country_name']} combine un ratio CO2 moyen bas "
                    f"({float(best_country['avg_co2_per_passenger']):.3f}) et "
                    f"{int(best_country['train_count'])} trains references."
                ),
                "suggestion": "Etudier les choix d'exploitation de ce pays pour les reproduire sur les corridors les moins performants.",
            }
        )

    return {"recommendations": recommendations}
