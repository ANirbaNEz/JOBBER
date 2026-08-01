import time
from typing import Optional
from .executor_base import ExecutorBase
from logging_monitor.logger import get_logger

logger = get_logger("jobber")


class BrowserExecutor(ExecutorBase):
    """Execute form filling and submission using Playwright."""

    def __init__(self, headless: bool = True, timeout: int = 30):
        super().__init__("browser")
        self.headless = headless
        self.timeout = timeout
        self.browser = None
        self.page = None

    def execute(self, job_url: str, field_mapping: dict, pdf_path: str = None) -> bool:
        """Fill form and submit application."""
        try:
            logger.info(f"Browser executor: starting for {job_url}")

            playwright = self._import_playwright()
            if not playwright:
                self.error_message = "Playwright not installed"
                return False

            self._init_browser(playwright)

            self.page.goto(job_url, wait_until="load", timeout=self.timeout * 1000)
            logger.info(f"Loaded page: {job_url}")

            if self._detect_captcha():
                logger.warning("CAPTCHA detected. Pausing for user to solve.")
                self.error_message = "CAPTCHA_REQUIRES_USER_INTERVENTION"
                self._close_browser()
                return False

            filled_count = self._fill_form(field_mapping, pdf_path)
            logger.info(f"Filled {filled_count} fields")

            submitted = self._submit_form()

            if submitted:
                time.sleep(2)
                current_url = self.page.url
                logger.info(f"Submitted successfully. Current URL: {current_url}")
                self.success = True
                self._close_browser()
                return True
            else:
                self.error_message = "Failed to find submit button"
                self._close_browser()
                return False

        except Exception as e:
            logger.error(f"Browser execution failed: {str(e)}")
            self.error_message = str(e)
            self._close_browser()
            return False

    def _import_playwright(self) -> Optional[object]:
        """Try to import playwright."""
        try:
            from playwright.sync_api import sync_playwright
            return sync_playwright()
        except ImportError:
            logger.error("Playwright not installed. Install with: pip install playwright")
            return None

    def _init_browser(self, playwright):
        """Initialize browser context."""
        try:
            p = playwright.start()
            self.browser = p.chromium.launch(headless=self.headless)
            context = self.browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            self.page = context.new_page()
            logger.info("Browser initialized")
        except Exception as e:
            logger.error(f"Failed to init browser: {str(e)}")
            raise

    def _close_browser(self):
        """Close browser."""
        try:
            if self.page:
                self.page.close()
            if self.browser:
                self.browser.close()
            logger.info("Browser closed")
        except:
            pass

    def _detect_captcha(self) -> bool:
        """Detect CAPTCHA on page."""
        try:
            captcha_keywords = ["recaptcha", "captcha", "hcaptcha", "bot", "verify"]
            page_text = self.page.content().lower()

            for keyword in captcha_keywords:
                if keyword in page_text:
                    logger.warning(f"CAPTCHA detected: {keyword}")
                    return True

            return False
        except:
            return False

    def _fill_form(self, field_mapping: dict, pdf_path: str = None) -> int:
        """Fill form fields."""
        filled = 0

        for field_name, value in field_mapping.items():
            if not value:
                continue

            try:
                if field_name == "resume" and pdf_path:
                    selector = f"input[name='{field_name}'], input[type='file']"
                    if self.page.query_selector(selector):
                        self.page.fill(selector, pdf_path)
                        logger.debug(f"Uploaded file: {pdf_path}")
                        filled += 1
                else:
                    selector = f"input[name='{field_name}'], textarea[name='{field_name}'], select[name='{field_name}']"
                    if self.page.query_selector(selector):
                        self.page.fill(selector, str(value))
                        logger.debug(f"Filled '{field_name}' with '{str(value)[:50]}'")
                        filled += 1

            except Exception as e:
                logger.warning(f"Failed to fill field '{field_name}': {str(e)}")

        return filled

    def _submit_form(self) -> bool:
        """Find and click submit button."""
        try:
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:has-text('Submit')",
                "button:has-text('Apply')",
                "button:has-text('Send')"
            ]

            for selector in submit_selectors:
                try:
                    if self.page.query_selector(selector):
                        self.page.click(selector)
                        logger.info(f"Clicked submit button: {selector}")
                        return True
                except:
                    continue

            logger.error("No submit button found")
            return False

        except Exception as e:
            logger.error(f"Failed to submit form: {str(e)}")
            return False
