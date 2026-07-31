import json
import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv


class Resume(BaseModel):
    name: str
    email: str
    phone: str
    skills: list[str]
    experience: list[dict]
    education: list[dict]
    summary: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "+1-555-1234",
                "skills": ["Python", "JavaScript", "SQL"],
                "experience": [
                    {
                        "title": "Senior Engineer",
                        "company": "TechCorp",
                        "duration": "2020-2024",
                        "description": "Led team of 5 engineers"
                    }
                ],
                "education": [
                    {
                        "degree": "BS Computer Science",
                        "school": "MIT",
                        "year": 2020
                    }
                ],
                "summary": "Experienced full-stack engineer with 5+ years in SaaS"
            }
        }


class AppConfig(BaseModel):
    gemini_api_key: str
    smtp_server: str
    smtp_port: int
    smtp_email: str
    smtp_password: str
    db_path: str
    generated_resumes_dir: str
    master_resume_path: str
    scraper_delay: int
    max_daily_applications: int
    headless: bool
    browser_timeout: int


def load_env():
    load_dotenv()
    env_path = Path(".env")
    if not env_path.exists():
        raise FileNotFoundError(".env file not found. Copy .env.template to .env and fill in your values.")


def get_config() -> AppConfig:
    load_env()
    return AppConfig(
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        smtp_server=os.getenv("SMTP_SERVER", "smtp.gmail.com"),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_email=os.getenv("SMTP_EMAIL", ""),
        smtp_password=os.getenv("SMTP_PASSWORD", ""),
        db_path=os.getenv("DB_PATH", "./jobber.db"),
        generated_resumes_dir=os.getenv("GENERATED_RESUMES_DIR", "./generated_resumes"),
        master_resume_path=os.getenv("MASTER_RESUME_PATH", "./config/master_resume.json"),
        scraper_delay=int(os.getenv("SCRAPER_DELAY", "2")),
        max_daily_applications=int(os.getenv("MAX_DAILY_APPLICATIONS", "5")),
        headless=os.getenv("HEADLESS", "true").lower() == "true",
        browser_timeout=int(os.getenv("BROWSER_TIMEOUT", "30"))
    )


def load_master_resume(path: str) -> Resume:
    with open(path, 'r') as f:
        data = json.load(f)
    return Resume(**data)


def validate_master_resume(resume: Resume) -> bool:
    if not resume.name or not resume.email or not resume.phone:
        return False
    if not resume.skills or len(resume.skills) == 0:
        return False
    if not resume.experience or len(resume.experience) == 0:
        return False
    if not resume.education or len(resume.education) == 0:
        return False
    return True
