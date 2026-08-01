from typing import Dict, List, Any, Optional
from logging_monitor.logger import get_logger

logger = get_logger("jobber")


class FormField:
    def __init__(self, name: str, field_type: str, label: str = "", required: bool = False, options: List[str] = None):
        self.name = name
        self.field_type = field_type  # text, textarea, email, select, radio, checkbox, file
        self.label = label
        self.required = required
        self.options = options or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.field_type,
            "label": self.label,
            "required": self.required,
            "options": self.options
        }


class FormParser:
    """Parse job application forms from HTML."""

    def __init__(self):
        pass

    def parse_form_html(self, html_content: str, form_id: str = "") -> Optional[Dict[str, Any]]:
        """Parse form fields from HTML content.

        Returns dict with form fields and metadata.
        """
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html_content, "html.parser")

            form = None
            if form_id:
                form = soup.find("form", {"id": form_id})
            else:
                form = soup.find("form")

            if not form:
                logger.warning("No form found in HTML")
                return None

            fields = self._extract_fields(form)

            captcha_detected = self._detect_captcha(soup)

            result = {
                "fields": [f.to_dict() for f in fields],
                "captcha_detected": captcha_detected,
                "field_count": len(fields),
                "required_count": sum(1 for f in fields if f.required)
            }

            logger.info(f"Parsed {len(fields)} form fields (captcha: {captcha_detected})")
            return result

        except Exception as e:
            logger.error(f"Form parsing failed: {str(e)}")
            return None

    def _extract_fields(self, form) -> List[FormField]:
        """Extract all form fields from form element."""
        fields = []

        inputs = form.find_all("input")
        for inp in inputs:
            field_type = inp.get("type", "text").lower()
            if field_type == "submit" or field_type == "button" or field_type == "hidden":
                continue

            name = inp.get("name", "")
            if not name:
                continue

            label = self._find_label(form, name)
            required = inp.has_attr("required")

            fields.append(FormField(name, field_type, label, required))

        textareas = form.find_all("textarea")
        for textarea in textareas:
            name = textarea.get("name", "")
            if not name:
                continue

            label = self._find_label(form, name)
            required = textarea.has_attr("required")

            fields.append(FormField(name, "textarea", label, required))

        selects = form.find_all("select")
        for select in selects:
            name = select.get("name", "")
            if not name:
                continue

            label = self._find_label(form, name)
            required = select.has_attr("required")

            options = [opt.get_text(strip=True) for opt in select.find_all("option")]

            fields.append(FormField(name, "select", label, required, options))

        return fields

    def _find_label(self, form, field_name: str) -> str:
        """Find label text for a form field."""
        try:
            label = form.find("label", {"for": field_name})
            if label:
                return label.get_text(strip=True)

            label = form.find("label", string=lambda s: s and field_name.lower() in s.lower())
            if label:
                return label.get_text(strip=True)
        except:
            pass

        return field_name.replace("_", " ").title()

    def _detect_captcha(self, soup) -> bool:
        """Detect if form has CAPTCHA."""
        captcha_keywords = ["recaptcha", "captcha", "hcaptcha", "bot-check", "verify"]
        html_str = str(soup).lower()

        for keyword in captcha_keywords:
            if keyword in html_str:
                return True

        return False

    def parse_form_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Parse form from URL (requires requests library)."""
        try:
            import requests

            logger.info(f"Fetching form from: {url}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            return self.parse_form_html(response.content.decode(), "")

        except Exception as e:
            logger.error(f"Failed to fetch form from URL: {str(e)}")
            return None
