import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv


class Resume:
    def __init__(self, data: Dict[str, Any]):
        self.name = data.get('name')
        self.email = data.get('email')
        self.phone = data.get('phone')
        self.skills = data.get('skills', [])
        self.experience = data.get('experience', [])
        self.education = data.get('education', [])
        self.summary = data.get('summary')


class AppConfig:
    def __init__(self, **kwargs):
        self.gemini_api_key = kwargs.get('gemini_api_key', '')
        self.smtp_server = kwargs.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = int(kwargs.get('smtp_port', '587'))
        self.smtp_email = kwargs.get('smtp_email', '')
        self.smtp_password = kwargs.get('smtp_password', '')
        self.db_path = kwargs.get('db_path', './jobber.db')
        self.generated_resumes_dir = kwargs.get('generated_resumes_dir', './generated_resumes')
        self.master_resume_path = kwargs.get('master_resume_path', './config/master_resume.json')
        self.scraper_delay = int(kwargs.get('scraper_delay', '2'))
        self.max_daily_applications = int(kwargs.get('max_daily_applications', '5'))
        self.headless = kwargs.get('headless', 'true').lower() == 'true'
        self.browser_timeout = int(kwargs.get('browser_timeout', '30'))


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
        smtp_port=os.getenv("SMTP_PORT", "587"),
        smtp_email=os.getenv("SMTP_EMAIL", ""),
        smtp_password=os.getenv("SMTP_PASSWORD", ""),
        db_path=os.getenv("DB_PATH", "./jobber.db"),
        generated_resumes_dir=os.getenv("GENERATED_RESUMES_DIR", "./generated_resumes"),
        master_resume_path=os.getenv("MASTER_RESUME_PATH", "./config/master_resume.json"),
        scraper_delay=os.getenv("SCRAPER_DELAY", "2"),
        max_daily_applications=os.getenv("MAX_DAILY_APPLICATIONS", "5"),
        headless=os.getenv("HEADLESS", "true"),
        browser_timeout=os.getenv("BROWSER_TIMEOUT", "30")
    )


def load_master_resume(path: str) -> Resume:
    with open(path, 'r') as f:
        data = json.load(f)
    return Resume(data)


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
