from abc import ABC, abstractmethod
from logging_monitor.logger import get_logger

logger = get_logger("jobber")


class ExecutorBase(ABC):
    """Base class for application executors (browser, email, etc)."""

    def __init__(self, executor_type: str):
        self.executor_type = executor_type
        self.success = False
        self.error_message = ""

    @abstractmethod
    def execute(self, job_url: str, field_mapping: dict, pdf_path: str = None) -> bool:
        """Execute application submission.

        Args:
            job_url: URL of job application
            field_mapping: Dict mapping form fields to values
            pdf_path: Path to resume PDF (for file upload)

        Returns:
            True if successful, False otherwise
        """
        pass

    def log_execution(self, job_id: int, status: str, message: str):
        """Log execution result."""
        logger.info(f"[Job {job_id}] {self.executor_type}: {status} - {message}")
