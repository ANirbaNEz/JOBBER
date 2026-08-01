from abc import ABC, abstractmethod
from typing import List
from .output_schema import Job
from logging_monitor.logger import get_logger

logger = get_logger("jobber")


class ScraperBase(ABC):
    def __init__(self, source: str):
        self.source = source
        self.jobs: List[Job] = []

    @abstractmethod
    def scrape(self, query: str, limit: int = 10) -> List[Job]:
        """Scrape jobs from the source. Must be implemented by subclasses."""
        pass

    def filter_by_keywords(self, jobs: List[Job], negative_keywords: List[str]) -> List[Job]:
        """Filter out jobs containing negative keywords."""
        filtered = []
        for job in jobs:
            skip = False
            for keyword in negative_keywords:
                if keyword.lower() in job.title.lower() or keyword.lower() in job.job_description.lower():
                    skip = True
                    logger.info(f"Filtered out: {job.title} (contains '{keyword}')")
                    break
            if not skip:
                filtered.append(job)
        return filtered

    def log_scrape_result(self, count: int, dedups: int, errors: int):
        logger.info(f"Scrape complete: {count} jobs found, {dedups} dedups, {errors} errors")
