import json
from typing import Optional, Dict, Any
from db.db import JobberDB
from logging_monitor.logger import get_logger

logger = get_logger("jobber")


class FormCache:
    """Cache parsed forms and field mappings in database."""

    def __init__(self, db: JobberDB):
        self.db = db

    def cache_form(self, job_id: int, form_fields: Dict[str, Any], field_mapping: Dict[str, str]):
        """Cache parsed form and field mapping."""
        try:
            self.db.cache_form_mapping(job_id, form_fields, field_mapping)
            logger.info(f"Form cached for job {job_id}")
        except Exception as e:
            logger.error(f"Failed to cache form: {str(e)}")

    def get_cached_form(self, job_id: int) -> Optional[Dict[str, Any]]:
        """Get cached form and mapping."""
        try:
            return self.db.get_form_mapping(job_id)
        except Exception as e:
            logger.error(f"Failed to retrieve cached form: {str(e)}")
            return None

    def has_cached_form(self, job_id: int) -> bool:
        """Check if form is cached."""
        return self.get_cached_form(job_id) is not None
