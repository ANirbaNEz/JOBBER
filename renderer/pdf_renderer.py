import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from .html_template import generate_resume_html
from logging_monitor.logger import get_logger

logger = get_logger("jobber")


class PDFRenderer:
    def __init__(self, output_dir: str = "./generated_resumes"):
        self.output_dir = output_dir
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    def render(self, tailored_resume: Dict[str, Any], company: str, job_title: str) -> Optional[str]:
        """Render tailored resume to PDF.

        Returns path to generated PDF, or None if failed.
        """
        try:
            html_content = generate_resume_html(tailored_resume)

            filename = self._generate_filename(company, job_title)
            filepath = os.path.join(self.output_dir, filename)

            self._html_to_pdf(html_content, filepath)

            logger.info(f"PDF rendered: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"PDF rendering failed: {str(e)}")
            return None

    def _generate_filename(self, company: str, job_title: str) -> str:
        """Generate filename: [Date]_[Company]_[Role]_Resume.pdf"""
        date_str = datetime.now().strftime("%Y%m%d")
        company_clean = company.replace(" ", "").replace("/", "-")[:20]
        title_clean = job_title.replace(" ", "")[:15]
        return f"{date_str}_{company_clean}_{title_clean}_Resume.pdf"

    def _html_to_pdf(self, html_content: str, output_path: str):
        """Convert HTML to PDF using weasyprint."""
        try:
            import weasyprint
            weasyprint.HTML(string=html_content).write_pdf(output_path)
        except ImportError:
            logger.error("weasyprint not installed. Using html2pdf fallback.")
            self._html_to_pdf_fallback(html_content, output_path)
        except Exception as e:
            logger.error(f"Weasyprint conversion failed: {str(e)}")
            raise

    def _html_to_pdf_fallback(self, html_content: str, output_path: str):
        """Fallback: use reportlab to generate simple PDF from HTML."""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            from reportlab.lib.utils import simpleSplit

            c = canvas.Canvas(output_path, pagesize=letter)
            width, height = letter
            y = height - 40

            for line in html_content.split('<'):
                if '>' in line:
                    line = line.split('>')[1]
                line = line.strip()
                if line and len(line) > 0:
                    if y < 40:
                        c.showPage()
                        y = height - 40
                    c.drawString(40, y, line[:100])
                    y -= 12

            c.save()
        except ImportError:
            logger.error("Neither weasyprint nor reportlab available. Saving as HTML.")
            with open(output_path.replace('.pdf', '.html'), 'w') as f:
                f.write(html_content)
