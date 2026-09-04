"""
ERSA core — LangChain agent using Claude for release-risk assessment.
---------------------------------------------------------------------------
Analyzes a Change Request's own fields (description, type, CI, planned
dates) and returns a risk score (0-100) plus a short recommendation.

Requires the ANTHROPIC_API_KEY environment variable to be set (on Render:
Environment tab > Add Environment Variable).
---------------------------------------------------------------------------
"""

import json
import logging
import os
from typing import Tuple

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger("ersa-core")

SYSTEM_PROMPT = """You are ERSA (Enterprise Release Stability Agent), a release-risk \
assessment agent for enterprise IT change management. You evaluate a single \
ServiceNow Change Request and produce a risk score and a short, actionable \
recommendation for the release manager reviewing it.

Score from 0 (negligible risk) to 100 (severe risk), weighing:
- Change type (emergency changes carry inherently higher risk than standard/normal)
- Whether the description indicates production, customer-facing, or \
  multi-system impact
- Whether a planned start/end window is defined (missing windows raise risk)
- Vagueness or missing detail in the description (an unclear change is a \
  risk in itself, since impact can't be assessed)
- Category and configuration item, where relevant to blast radius

Respond with ONLY a JSON object, no other text, in this exact shape:
{"risk_score": <integer 0-100>, "recommendation": "<one to three sentences, \
specific and actionable, aimed at a release manager deciding whether to \
approve this change as-is>"}
"""


class ERSAAgent:
    def __init__(self, model: str = "claude-sonnet-5", temperature: float = 0.0):
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY environment variable is not set. "
                "Add it under Render > your service > Environment."
            )
        self.llm = ChatAnthropic(model=model, temperature=temperature, api_key=api_key)

    def evaluate(self, change_fields: dict) -> Tuple[int, str]:
        """
        change_fields: dict with keys like change_id, short_description,
        description, type, category, planned_start_date, planned_end_date,
        cmdb_ci (matches the payload shape sent by the ServiceNow Script Include).

        Returns (risk_score: int, recommendation: str).
        """
        user_content = (
            "Change Request to assess:\n\n"
            f"{json.dumps(change_fields, indent=2)}"
        )

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_content),
        ]

        response = self.llm.invoke(messages)
        raw_text = response.content if isinstance(response.content, str) else str(response.content)

        return self._parse_response(raw_text)

    def _parse_response(self, raw_text: str) -> Tuple[int, str]:
        text = raw_text.strip()
        # Claude occasionally wraps JSON in a code fence despite instructions — strip it.
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()

        try:
            parsed = json.loads(text)
            risk_score = int(parsed["risk_score"])
            risk_score = max(0, min(100, risk_score))
            recommendation = str(parsed["recommendation"])
            return risk_score, recommendation
        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as exc:
            logger.error("Failed to parse ERSA response: %s | raw: %s", exc, raw_text)
            # Fail safe rather than fail silent — surface a mid-range score with
            # the raw model output so the caller can see something went wrong
            # with parsing rather than getting a confidently wrong number.
            return 50, f"ERSA response could not be parsed as JSON. Raw output: {raw_text[:500]}"
