import json
from typing import List, Dict, Optional
from .llm_client import GeminiClient
from logging_monitor.logger import get_logger

logger = get_logger("jobber")


class QAGenerator:
    def __init__(self, llm_client: GeminiClient):
        self.llm = llm_client

    def generate(self, job_description: str, candidate_summary: str) -> Optional[List[Dict]]:
        """Generate Q&A responses for common application questions."""
        prompt = f"""You are an expert at answering job application questions. Generate Q&A responses for a job application.

CANDIDATE BACKGROUND:
{candidate_summary}

JOB DESCRIPTION:
{job_description}

TASK:
Generate 3-4 likely application questions and provide professional answers (2-3 sentences each).

Common questions:
- Why are you interested in this position/company?
- What relevant experience do you have?
- Describe a challenging project you worked on
- Where do you see yourself in 5 years?
- Why should we hire you?

Return ONLY a valid JSON array with this structure (no markdown):
[
  {{"question": "Why are you interested in this position?", "answer": "..."}},
  {{"question": "What relevant experience do you have?", "answer": "..."}},
  ...
]

Return ONLY valid JSON, no extra text."""

        response = self.llm.generate_json(prompt)

        if isinstance(response, list):
            logger.info(f"Generated {len(response)} Q&A pairs")
            return response

        logger.error("Q&A generation failed: invalid response format")
        return None
