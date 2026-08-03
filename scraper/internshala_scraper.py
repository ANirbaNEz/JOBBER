import time
from typing import List
from .scraper_base import ScraperBase
from .output_schema import Job
from logging_monitor.logger import get_logger

logger = get_logger("jobber")


class InternShalaScraper(ScraperBase):
    """Scrape jobs from Internshala.com (Indian internship/job portal)."""

    def __init__(self):
        super().__init__("internshala")
        self.base_url = "https://internshala.com/jobs"

    def scrape(self, query: str, location: str = "", limit: int = 10) -> List[Job]:
        """Scrape jobs from Internshala using Playwright."""
        jobs = []

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.error("Playwright not installed. Install with: pip install playwright")
            return []

        try:
            logger.info(f"Starting Internshala scrape for: {query} (limit: {limit})")

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                url = f"{self.base_url}?q={query}"
                if location:
                    url += f"&location={location}"

                logger.info(f"Navigating to: {url}")
                page.goto(url, wait_until="networkidle", timeout=30000)

                time.sleep(2)

                # Internshala job listing structure
                job_cards = page.locator("div.job-card, div.internship_card").all()
                logger.info(f"Found {len(job_cards)} job cards")

                for idx, card in enumerate(job_cards[:limit]):
                    try:
                        # Extract title
                        title_elem = card.locator("h3.heading_3_5, span.job-title").first
                        title = title_elem.text_content() if title_elem else "Unknown"

                        # Extract company
                        company_elem = card.locator("p.company, span.company-name").first
                        company = company_elem.text_content() if company_elem else "Unknown"

                        # Extract URL
                        link_elem = card.locator("a").first
                        job_url = link_elem.get_attribute("href") if link_elem else ""

                        if not job_url:
                            continue

                        if not job_url.startswith("http"):
                            job_url = f"https://internshala.com{job_url}"

                        # Extract details
                        details = []
                        detail_elems = card.locator("p.detail").all()
                        for detail_elem in detail_elems[:3]:
                            detail_text = detail_elem.text_content()
                            if detail_text:
                                details.append(detail_text.strip())

                        job_desc = " | ".join(details) if details else query

                        job = Job(
                            title=title.strip(),
                            company=company.strip(),
                            url=job_url,
                            job_description=job_desc,
                            required_skills="",
                            app_type="form",
                            source="internshala"
                        )

                        jobs.append(job)
                        logger.debug(f"Scraped job {idx+1}: {title} at {company}")

                    except Exception as e:
                        logger.warning(f"Error parsing job card {idx}: {str(e)}")
                        continue

                browser.close()

        except Exception as e:
            logger.error(f"Internshala scrape failed: {str(e)}")

        logger.info(f"Scraped {len(jobs)} jobs from Internshala")
        return jobs
