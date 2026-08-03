import time
from typing import List, Optional
from .scraper_base import ScraperBase
from .output_schema import Job
from logging_monitor.logger import get_logger

logger = get_logger("jobber")


class NaukriScraper(ScraperBase):
    """Scrape jobs from Naukri.com (Indian job portal)."""

    def __init__(self):
        super().__init__("naukri")
        self.base_url = "https://www.naukri.com/search"

    def scrape(self, query: str, location: str = "", limit: int = 10) -> List[Job]:
        """Scrape jobs from Naukri using Playwright for JS rendering."""
        jobs = []

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.error("Playwright not installed. Install with: pip install playwright")
            logger.info("Falling back to mock scraper")
            return []

        try:
            logger.info(f"Starting Naukri scrape for: {query} (limit: {limit})")

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                url = f"{self.base_url}?k={query}"
                if location:
                    url += f"&l={location}"

                logger.info(f"Navigating to: {url}")
                page.goto(url, wait_until="networkidle", timeout=30000)

                time.sleep(2)

                job_cards = page.locator("div.jobsCard").all()
                logger.info(f"Found {len(job_cards)} job cards")

                for idx, card in enumerate(job_cards[:limit]):
                    try:
                        title_elem = card.locator("a.title").first
                        title = title_elem.text_content() if title_elem else "Unknown"

                        company_elem = card.locator("a.companyName").first
                        company = company_elem.text_content() if company_elem else "Unknown"

                        link_elem = card.locator("a.title").first
                        job_url = link_elem.get_attribute("href") if link_elem else ""

                        if not job_url:
                            continue

                        if not job_url.startswith("http"):
                            job_url = f"https://www.naukri.com{job_url}"

                        exp_elem = card.locator("span.expwdth").first
                        experience = exp_elem.text_content() if exp_elem else ""

                        salary_elem = card.locator("span.sal").first
                        salary = salary_elem.text_content() if salary_elem else ""

                        job_desc = f"Experience: {experience} | Salary: {salary}"

                        job = Job(
                            title=title.strip(),
                            company=company.strip(),
                            url=job_url,
                            job_description=job_desc,
                            required_skills="",
                            app_type="form",
                            source="naukri"
                        )

                        jobs.append(job)
                        logger.debug(f"Scraped job {idx+1}: {title} at {company}")

                    except Exception as e:
                        logger.warning(f"Error parsing job card {idx}: {str(e)}")
                        continue

                browser.close()

        except Exception as e:
            logger.error(f"Naukri scrape failed: {str(e)}")

        logger.info(f"Scraped {len(jobs)} jobs from Naukri")
        return jobs
