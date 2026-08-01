import json
from typing import Dict, List, Optional
from config.config import Resume
from .llm_client import GeminiClient
from logging_monitor.logger import get_logger

logger = get_logger("jobber")


class ResumeTailor:
    def __init__(self, llm_client: GeminiClient):
        self.llm = llm_client

    def tailor(self, master_resume: Resume, job_description: str) -> Optional[Dict]:
        """Tailor master resume to job description.

        Returns JSON with tailored resume (subset/reordered skills only, NO hallucination).
        """
        prompt = f"""You are a resume optimization expert. Your task is to tailor a resume to a job description.

CRITICAL CONSTRAINT: Only reorder or subset skills from the master resume. NEVER add skills not in the master resume. This prevents hallucination.

MASTER RESUME (Source of Truth):
Name: {master_resume.name}
Email: {master_resume.email}
Phone: {master_resume.phone}
Summary: {master_resume.summary}

Skills (all available):
{', '.join(master_resume.skills)}

Experience:
{json.dumps(master_resume.experience, indent=2)}

Education:
{json.dumps(master_resume.education, indent=2)}

JOB DESCRIPTION:
{job_description}

TASK:
1. Extract top 10-15 skills from the master resume that match the job description
2. Reorder experience to highlight most relevant roles
3. Keep summary professional and job-focused
4. IMPORTANT: Only use skills and experience from master resume. Do NOT invent or add new items.

Return a JSON object with this exact structure (no markdown):
{{
  "name": "{master_resume.name}",
  "email": "{master_resume.email}",
  "phone": "{master_resume.phone}",
  "summary": "Tailored summary focusing on relevant experience (2-3 sentences)",
  "skills": ["skill1", "skill2", ...],  // ONLY from master resume skills
  "experience": [// Reordered to highlight most relevant
    {{"title": "...", "company": "...", "duration": "...", "description": "..."}}
  ],
  "education": [{{"degree": "...", "school": "...", "year": ...}}]
}}

Return ONLY valid JSON, no extra text."""

        response = self.llm.generate_json(prompt)

        if response:
            tailored = self._validate_tailored_resume(response, master_resume)
            if tailored:
                logger.info(f"Resume tailored: {len(tailored.get('skills', []))} skills selected")
                return tailored

        return None

    def _validate_tailored_resume(self, tailored: Dict, master: Resume) -> Optional[Dict]:
        """Validate that tailored resume only contains master resume content."""
        master_skills = set(s.lower() for s in master.skills)

        tailored_skills = tailored.get("skills", [])
        for skill in tailored_skills:
            if skill.lower() not in master_skills:
                logger.warning(f"Hallucinated skill detected: {skill}. Removing.")
                tailored_skills = [s for s in tailored_skills if s.lower() in master_skills]

        if not tailored_skills:
            logger.error("No valid skills after validation. Tailor failed.")
            return None

        tailored["skills"] = tailored_skills
        logger.info(f"Resume validation passed: {len(tailored_skills)} valid skills")
        return tailored
