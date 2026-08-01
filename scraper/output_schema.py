from typing import Dict, Any, Optional
from datetime import datetime


class Job:
    def __init__(self, title: str, company: str, url: str, job_description: str,
                 required_skills: Optional[str] = None, app_type: str = "form",
                 source: str = "unknown"):
        self.title = title
        self.company = company
        self.url = url
        self.job_description = job_description
        self.required_skills = required_skills or ""
        self.app_type = app_type
        self.source = source
        self.scraped_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "company": self.company,
            "url": self.url,
            "job_description": self.job_description,
            "required_skills": self.required_skills,
            "app_type": self.app_type,
            "source": self.source,
            "scraped_at": self.scraped_at.isoformat()
        }

    def __repr__(self):
        return f"Job(title='{self.title}', company='{self.company}', source='{self.source}')"
