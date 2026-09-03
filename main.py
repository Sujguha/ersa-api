"""
ERSA API — FastAPI wrapper
---------------------------------------------------------------------------
Exposes ERSA (Enterprise Release Stability Agent) as a REST endpoint that
matches what the ServiceNow ERSAIntegration Script Include sends and expects
back.

This file is a STUB for the scoring logic — replace the body of
`run_ersa_assessment()` with your actual ERSA / LangChain pipeline call.
Everything else (request schema, response schema, error handling, the route)
is wired to match the ServiceNow side exactly, so you shouldn't need to
touch ServiceNow again once you plug in the real logic here.
---------------------------------------------------------------------------
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ersa-api")

app = FastAPI(title="ERSA Risk API", version="1.0.0")


# ---------------------------------------------------------------------------
# Request / response schemas — must match the payload built in
# ERSAIntegration.js (ServiceNow Script Include) and its response parsing.
# ---------------------------------------------------------------------------

class ChangeRequestPayload(BaseModel):
    change_id: str
    sys_id: str
    short_description: Optional[str] = ""
    description: Optional[str] = ""
    type: Optional[str] = ""
    risk: Optional[str] = ""
    category: Optional[str] = ""
    planned_start_date: Optional[str] = ""
    planned_end_date: Optional[str] = ""
    cmdb_ci: Optional[str] = ""
    requested_by: Optional[str] = ""


class ERSAResponse(BaseModel):
    risk_score: int          # 0-100
    recommendation: str


@app.get("/")
def health_check():
    """Simple health check so Render/uptime monitors have something to ping."""
    return {"status": "ok", "service": "ERSA Risk API"}


@app.post("/api/v1/assess-change", response_model=ERSAResponse)
def assess_change(payload: ChangeRequestPayload):
    """
    Called by ServiceNow (via the ERSAIntegration Script Include) whenever a
    Change Request is created or its key fields change.
    """
    logger.info("Assessing change %s (%s)", payload.change_id, payload.sys_id)

    try:
        risk_score, recommendation = run_ersa_assessment(payload)
    except Exception as exc:
        logger.exception("ERSA assessment failed for %s", payload.change_id)
        raise HTTPException(status_code=500, detail=f"ERSA assessment failed: {exc}")

    return ERSAResponse(risk_score=risk_score, recommendation=recommendation)


def run_ersa_assessment(payload: ChangeRequestPayload) -> tuple[int, str]:
    """
    Replace this function body with your actual ERSA / LangChain logic.

    It receives the full Change Request payload and must return a tuple:
        (risk_score: int between 0-100, recommendation: str)

    Example of where your real pipeline plugs in:

        from ersa_core import ERSAAgent
        agent = ERSAAgent()
        result = agent.evaluate(
            description=payload.description,
            change_type=payload.type,
            ci=payload.cmdb_ci,
            ...
        )
        return result.risk_score, result.summary
    """
    # --- STUB LOGIC (delete once real ERSA pipeline is wired in) ----------
    text = f"{payload.short_description} {payload.description}".lower()
    score = 30
    reasons = []

    if payload.type and payload.type.lower() == "emergency":
        score += 30
        reasons.append("emergency change type")
    if "production" in text or "prod" in text:
        score += 20
        reasons.append("touches production")
    if not payload.planned_start_date or not payload.planned_end_date:
        score += 10
        reasons.append("missing planned window")

    score = min(score, 100)
    recommendation = (
        f"Stub assessment — score based on: {', '.join(reasons) or 'no risk signals found'}. "
        "Replace run_ersa_assessment() with the real ERSA pipeline."
    )
    return score, recommendation
    # ------------------------------------------------------------------------
