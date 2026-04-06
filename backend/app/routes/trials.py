from fastapi import APIRouter, Depends
from app.auth.router import get_current_user
import httpx

router = APIRouter()


@router.get("/search")
async def search_trials(
    cancer_type: str = "",
    status: str = "RECRUITING",
    current_user: dict = Depends(get_current_user)
):
    """Search ClinicalTrials.gov API v2 for relevant clinical trials. Completely free."""
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(
                "https://clinicaltrials.gov/api/v2/studies",
                params={
                    "query.cond": f"cancer {cancer_type}",
                    "filter.overallStatus": status,
                    "fields": "NCTId,BriefTitle,Condition,Phase,LocationCountry,BriefSummary",
                    "pageSize": 10
                },
                timeout=15.0
            )
        except Exception:
            return {"trials": [], "error": "Could not reach ClinicalTrials.gov", "total": 0}

    if r.status_code != 200:
        return {"trials": [], "error": "ClinicalTrials.gov returned an error", "total": 0}

    data = r.json()
    trials = []
    for study in data.get("studies", []):
        p = study.get("protocolSection", {})
        trials.append({
            "id": p.get("identificationModule", {}).get("nctId"),
            "title": p.get("identificationModule", {}).get("briefTitle"),
            "phase": p.get("designModule", {}).get("phases", ["N/A"]),
            "summary": p.get("descriptionModule", {}).get("briefSummary", "")[:300],
            "countries": p.get("contactsLocationsModule", {}).get("locations", []),
        })

    return {"trials": trials, "total": data.get("totalCount", 0)}
