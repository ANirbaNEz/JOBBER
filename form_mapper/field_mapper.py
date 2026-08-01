from typing import Dict, List, Any, Optional
from config.config import Resume
from logging_monitor.logger import get_logger

logger = get_logger("jobber")


class FieldMapper:
    """Map resume data to form fields using heuristics."""

    def __init__(self):
        self.skill_keywords = ["skill", "expertise", "technical", "proficiency", "competency"]
        self.email_keywords = ["email", "mail", "e-mail", "contact_email"]
        self.phone_keywords = ["phone", "telephone", "mobile", "number", "contact_phone"]
        self.name_keywords = ["name", "full_name", "fullname", "first_name"]
        self.experience_keywords = ["experience", "years", "background", "resume"]
        self.education_keywords = ["education", "degree", "school", "university"]

    def map_fields(self, form_fields: List[Dict], tailored_resume: Dict[str, Any]) -> Dict[str, str]:
        """Map form fields to resume data.

        Returns dict: {field_name: value}
        """
        mapping = {}

        for field in form_fields:
            name = field.get("name", "")
            field_type = field.get("type", "text")
            label = field.get("label", "").lower()

            value = self._match_field(name, label, field_type, tailored_resume)

            if value:
                mapping[name] = value
                logger.debug(f"Mapped field '{name}' = '{value[:50]}'")
            else:
                logger.debug(f"Could not map field '{name}'")

        logger.info(f"Mapped {len(mapping)}/{len(form_fields)} fields")
        return mapping

    def _match_field(self, name: str, label: str, field_type: str, tailored_resume: Dict) -> Optional[str]:
        """Match a single field to resume data."""
        name_lower = name.lower()
        label_lower = label.lower()

        if self._matches_keywords(name_lower, label_lower, self.email_keywords):
            return tailored_resume.get("email", "")

        if self._matches_keywords(name_lower, label_lower, self.phone_keywords):
            return tailored_resume.get("phone", "")

        if self._matches_keywords(name_lower, label_lower, self.name_keywords):
            return tailored_resume.get("name", "")

        if self._matches_keywords(name_lower, label_lower, self.skill_keywords):
            skills = tailored_resume.get("skills", [])
            return ", ".join(skills) if skills else ""

        if self._matches_keywords(name_lower, label_lower, self.experience_keywords):
            experience = tailored_resume.get("experience", [])
            if experience:
                exp_text = " | ".join([
                    f"{e.get('title')} at {e.get('company')}" for e in experience
                ])
                return exp_text
            return ""

        if self._matches_keywords(name_lower, label_lower, self.education_keywords):
            education = tailored_resume.get("education", [])
            if education:
                edu_text = " | ".join([
                    f"{e.get('degree')} from {e.get('school')}" for e in education
                ])
                return edu_text
            return ""

        if field_type == "textarea":
            summary = tailored_resume.get("summary", "")
            return summary if summary else ""

        return None

    def _matches_keywords(self, name: str, label: str, keywords: List[str]) -> bool:
        """Check if field name/label matches any keyword."""
        combined = f"{name} {label}"

        for keyword in keywords:
            if keyword in combined:
                return True

        return False
