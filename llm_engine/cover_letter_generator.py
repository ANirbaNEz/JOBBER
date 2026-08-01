from typing import Optional
from config.config import Resume
from .llm_client import GeminiClient
from logging_monitor.logger import get_logger

logger = get_logger("jobber")


class CoverLetterGenerator:
    def __init__(self, llm_client: GeminiClient):
        self.llm = llm_client

    def generate(self, master_resume: Resume, job_description: str, company: str) -> Optional[str]:
        """Generate a personalized cover letter."""
        prompt = f"""You are an expert cover letter writer. Write a professional, compelling cover letter.

CANDIDATE PROFILE:
Name: {master_resume.name}
Email: {master_resume.email}
Phone: {master_resume.phone}
Summary: {master_resume.summary}
Key Skills: {', '.join(master_resume.skills[:5])}

COMPANY & JOB DESCRIPTION:
Company: {company}
Job Description:
{job_description}

TASK:
Write a professional cover letter (3-4 paragraphs, 150-200 words) that:
1. Shows genuine interest in the company
2. Highlights 2-3 most relevant skills from the candidate's profile
3. Explains why the candidate is a great fit
4. Uses a professional but warm tone
5. Ends with a strong call to action

Format:
[opening paragraph]

[skills/experience match paragraph]

[enthusiasm/culture fit paragraph]

[closing with call to action]

Write ONLY the cover letter content, no salutation like "Dear Hiring Manager" - we'll add that separately."""

        response = self.llm.generate(prompt, max_tokens=500)

        if response:
            logger.info(f"Cover letter generated: {len(response)} chars")
            return response.strip()

        return None
