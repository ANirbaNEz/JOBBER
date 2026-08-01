import requests
from bs4 import BeautifulSoup
from typing import List
from .scraper_base import ScraperBase
from .output_schema import Job
from logging_monitor.logger import get_logger
import time

logger = get_logger("jobber")


class IndeedScraper(ScraperBase):
    def __init__(self):
        super().__init__("indeed")
        self.base_url = "https://www.indeed.com/jobs"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def scrape(self, query: str, location: str = "", limit: int = 10) -> List[Job]:
        """Scrape jobs from Indeed."""
        jobs = []
        logger.info(f"Starting Indeed scrape for: {query} (limit: {limit})")

        try:
            params = {
                "q": query,
                "l": location,
                "start": 0,
                "limit": limit
            }

            url = f"{self.base_url}?q={query}"
            if location:
                url += f"&l={location}"

            logger.info(f"Fetching: {url}")
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            job_cards = soup.find_all("div", class_="job_seen_beacon")
            logger.info(f"Found {len(job_cards)} job cards")

            for idx, card in enumerate(job_cards[:limit]):
                try:
                    job_link = card.find("a", class_="jcs-JobTitle")
                    if not job_link:
                        continue

                    title = job_link.get_text(strip=True)
                    job_url = job_link.get("href")

                    if not job_url:
                        continue

                    if not job_url.startswith("http"):
                        job_url = f"https://www.indeed.com{job_url}"

                    company_elem = card.find("span", class_="companyName")
                    company = company_elem.get_text(strip=True) if company_elem else "Unknown"

                    location_elem = card.find("div", class_="companyLocation")
                    location = location_elem.get_text(strip=True) if location_elem else ""

                    snippet_elem = card.find("div", class_="job-snippet")
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                    job = Job(
                        title=title,
                        company=company,
                        url=job_url,
                        job_description=snippet,
                        required_skills="",
                        app_type="form",
                        source="indeed"
                    )

                    jobs.append(job)
                    logger.debug(f"Scraped job {idx+1}: {title} at {company}")

                except Exception as e:
                    logger.error(f"Error parsing job card {idx}: {str(e)}")
                    continue

                time.sleep(0.1)

        except requests.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Scrape failed: {str(e)}")

        logger.info(f"Scraped {len(jobs)} jobs from Indeed")
        return jobs
