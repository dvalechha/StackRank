"""Score resumes against job description using AI."""

import json
import logging
from dataclasses import dataclass
from typing import Any

from stackrank.model_client import ModelClient
from stackrank.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


@dataclass
class CandidateResult:
    """Result of scoring a candidate against a job description."""
    candidate_name: str
    file_name: str
    total_score: int
    recommendation: str
    summary: str
    dimensions: dict[str, Any]
    parse_error: bool = False


class Scorer:
    """Scores candidates against job descriptions using AI."""

    def __init__(self, model_client: ModelClient):
        """Initialize scorer with a model client.

        Args:
            model_client: Configured model client for AI calls
        """
        self.model_client = model_client

    def score(self, jd_text: str, resume_data: dict[str, Any], file_name: str) -> CandidateResult:
        """Score a single resume against the job description.

        Args:
            jd_text: Job description text
            resume_data: Dict with 'candidate_name' and 'text' keys
            file_name: Original filename for reference

        Returns:
            CandidateResult dataclass with scores and assessments
        """
        candidate_name = resume_data["candidate_name"]
        resume_text = resume_data["text"]

        user_prompt = USER_PROMPT_TEMPLATE.format(
            jd_text=jd_text,
            resume_text=resume_text
        )

        # First attempt
        result = self._call_model(candidate_name, SYSTEM_PROMPT, user_prompt, file_name)

        if result.parse_error:
            # Retry once
            logger.info(f"Retrying score for {candidate_name} after parse error")
            result = self._call_model(candidate_name, SYSTEM_PROMPT, user_prompt, file_name)

        return result

    def _call_model(
        self,
        candidate_name: str,
        system_prompt: str,
        user_prompt: str,
        file_name: str
    ) -> CandidateResult:
        """Call the model and parse the response."""
        try:
            response = self.model_client.complete(system_prompt, user_prompt)
            return self._parse_response(response, candidate_name, file_name)
        except Exception as e:
            logger.error(f"Error calling model for {candidate_name}: {e}")
            return CandidateResult(
                candidate_name=candidate_name,
                file_name=file_name,
                total_score=0,
                recommendation="NO",
                summary=f"Error during evaluation: {str(e)}",
                dimensions={},
                parse_error=True
            )

    def _parse_response(self, response: str, candidate_name: str, file_name: str) -> CandidateResult:
        """Parse JSON response from the model."""
        try:
            # Try to find JSON in the response (in case model adds preamble)
            json_start = response.find("{")
            json_end = response.rfind("}") + 1

            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")

            json_str = response[json_start:json_end]
            data = json.loads(json_str)

            return CandidateResult(
                candidate_name=data.get("candidate_name", candidate_name),
                file_name=file_name,
                total_score=int(data.get("total_score", 0)),
                recommendation=data.get("recommendation", "MAYBE"),
                summary=data.get("summary", ""),
                dimensions=data.get("dimensions", {}),
                parse_error=False
            )

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse response for {candidate_name}: {e}")
            return CandidateResult(
                candidate_name=candidate_name,
                file_name=file_name,
                total_score=0,
                recommendation="NO",
                summary=f"Failed to parse model response: {str(e)}",
                dimensions={},
                parse_error=True
            )