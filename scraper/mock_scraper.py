from typing import List
from .scraper_base import ScraperBase
from .output_schema import Job
from logging_monitor.logger import get_logger

logger = get_logger("jobber")


class MockScraper(ScraperBase):
    """Mock scraper for testing. Returns hardcoded test jobs."""

    def __init__(self):
        super().__init__("mock")

    def scrape(self, query: str, location: str = "", limit: int = 10) -> List[Job]:
        """Return mock jobs for testing."""
        logger.info(f"Mock scraper: returning test jobs for '{query}'")

        test_jobs = [
            Job(
                title="Senior Python Engineer",
                company="TechCorp Inc",
                url="https://example.com/job/1",
                job_description="We're looking for a Senior Python Engineer with 5+ years experience. Must know Django, FastAPI, and PostgreSQL. Remote position.",
                required_skills="Python, Django, FastAPI, PostgreSQL, REST APIs",
                app_type="form",
                source="mock"
            ),
            Job(
                title="Full Stack Developer",
                company="StartupXYZ",
                url="https://example.com/job/2",
                job_description="Join our team as a Full Stack Developer. Required: React, Node.js, MongoDB. Experience with AWS is a plus.",
                required_skills="React, Node.js, MongoDB, JavaScript, CSS",
                app_type="form",
                source="mock"
            ),
            Job(
                title="DevOps Engineer",
                company="CloudSystems LLC",
                url="https://example.com/job/3",
                job_description="Looking for DevOps Engineer to manage CI/CD pipelines. Kubernetes, Docker, and AWS experience required.",
                required_skills="Kubernetes, Docker, AWS, CI/CD, Linux",
                app_type="email",
                source="mock"
            ),
            Job(
                title="Data Engineer",
                company="DataCorp",
                url="https://example.com/job/4",
                job_description="Build scalable data pipelines. Apache Spark, Kafka, and Python required. Work with large datasets.",
                required_skills="Python, Apache Spark, Kafka, SQL, AWS",
                app_type="form",
                source="mock"
            ),
            Job(
                title="Machine Learning Engineer",
                company="AI Innovations",
                url="https://example.com/job/5",
                job_description="Develop ML models and deploy them to production. TensorFlow, PyTorch, and scikit-learn experience needed.",
                required_skills="Python, TensorFlow, PyTorch, scikit-learn, ML",
                app_type="form",
                source="mock"
            ),
        ]

        return test_jobs[:limit]
