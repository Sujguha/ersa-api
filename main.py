"""
ERSA API — FastAPI wrapper
---------------------------------------------------------------------------
Exposes ERSA (Enterprise Release Stability Agent) as a REST endpoint that
matches what the ServiceNow ERSAIntegration Script Include sends and expects
back. Real scoring logic lives in ersa_core.py (ERSAAgent), which calls
Claude via LangChain.

Requires ANTHROPIC_API_KEY to be set as an environment variable.
---------------------------------------------------------------------------
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

from ersa_core import ERSAAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ersa-api")

app = FastAPI(title="ERSA Risk API", version="1.0.0")

# Instantiated once at startup — raises immediately and loudly if
# ANTHROPIC_API_KEY isn't set, rather than failing silently on first request.
agent = ERSAAgent()


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
        risk_score, recommendation = agent.evaluate(payload.model_dump())
    except Exception as exc:
        logger.exception("ERSA assessment failed for %s", payload.change_id)
        raise HTTPException(status_code=500, detail=f"ERSA assessment failed: {exc}")

    return ERSAResponse(risk_score=risk_score, recommendation=recommendation)



