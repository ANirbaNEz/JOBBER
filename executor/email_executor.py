import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional
from .executor_base import ExecutorBase
from logging_monitor.logger import get_logger

logger = get_logger("jobber")


class EmailExecutor(ExecutorBase):
    """Execute email-based job applications."""

    def __init__(self, smtp_server: str, smtp_port: int, email: str, password: str):
        super().__init__("email")
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email = email
        self.password = password

    def execute(self, recipient_email: str, subject: str, body: str, pdf_path: str = None) -> bool:
        """Send job application via email.

        Args:
            recipient_email: Email address to send to
            subject: Email subject
            body: Email body (cover letter)
            pdf_path: Path to resume PDF

        Returns:
            True if successful
        """
        try:
            logger.info(f"Email executor: sending to {recipient_email}")

            msg = MIMEMultipart()
            msg["From"] = self.email
            msg["To"] = recipient_email
            msg["Subject"] = subject

            msg.attach(MIMEText(body, "plain"))

            if pdf_path:
                self._attach_pdf(msg, pdf_path)

            self._send_email(msg, recipient_email)

            logger.info(f"Email sent to {recipient_email}")
            self.success = True
            return True

        except Exception as e:
            logger.error(f"Email execution failed: {str(e)}")
            self.error_message = str(e)
            return False

    def _attach_pdf(self, msg: MIMEMultipart, pdf_path: str):
        """Attach PDF resume to email."""
        try:
            with open(pdf_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())

            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename= {pdf_path}")
            msg.attach(part)

            logger.debug(f"Attached PDF: {pdf_path}")
        except Exception as e:
            logger.error(f"Failed to attach PDF: {str(e)}")

    def _send_email(self, msg: MIMEMultipart, recipient: str):
        """Send email via SMTP."""
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {recipient}")
        except Exception as e:
            logger.error(f"SMTP failed: {str(e)}")
            raise
