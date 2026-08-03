import json
from pathlib import Path
from typing import Dict, Any
from logging_monitor.logger import get_logger

logger = get_logger("jobber")


class ResumeAnalyzer:
    """Parse and analyze resume files (PDF, DOCX, TXT) to extract structured data."""

    def __init__(self, llm_client):
        self.llm = llm_client

    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text from resume file (PDF, DOCX, TXT)."""
        try:
            path = Path(file_path)

            if path.suffix.lower() == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()

            elif path.suffix.lower() in ['.pdf']:
                try:
                    from PyPDF2 import PdfReader
                    reader = PdfReader(file_path)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text()
                    return text
                except Exception as e:
                    logger.error(f"PDF extraction failed: {str(e)}")
                    return ""

            elif path.suffix.lower() in ['.docx', '.doc']:
                try:
                    from docx import Document
                    doc = Document(file_path)
                    text = "\n".join([para.text for para in doc.paragraphs])
                    return text
                except Exception as e:
                    logger.error(f"DOCX extraction failed: {str(e)}")
                    return ""

            else:
                logger.warning(f"Unsupported file format: {path.suffix}")
                return ""

        except Exception as e:
            logger.error(f"Text extraction error: {str(e)}")
            return ""

    def analyze(self, resume_text: str) -> Dict[str, Any]:
        """Use LLM to parse resume text and extract structured data."""
        if not resume_text or len(resume_text.strip()) < 50:
            return None

        prompt = f"""Analyze this resume and extract structured information. Return ONLY valid JSON with no markdown formatting or code blocks.

Resume Text:
{resume_text}

Extract and return this exact JSON structure (use empty strings if info not found):
{{
  "name": "Full name of the person",
  "email": "Email address",
  "phone": "Phone number",
  "summary": "Professional summary or objective (2-3 sentences)",
  "skills": ["Skill1", "Skill2", "Skill3"],
  "experience": [
    {{
      "title": "Job title",
      "company": "Company name",
      "duration": "Start-End year",
      "description": "Key responsibilities and achievements"
    }}
  ],
  "education": [
    {{
      "degree": "Degree name",
      "school": "School/University name",
      "year": "Year of graduation"
    }}
  ]
}}

Important: Return ONLY the JSON, no other text."""

        try:
            response = self.llm.generate(prompt)
            if not response:
                return None

            # Parse JSON from response
            text = response.strip()
            if text.startswith('```'):
                text = text.split('```')[1]
                if text.startswith('json'):
                    text = text[4:]
            text = text.strip()

            resume_data = json.loads(text)
            return resume_data

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Resume analysis error: {str(e)}")
            return None

    def process_file(self, file_path: str) -> Dict[str, Any]:
        """Extract text from file and analyze with LLM."""
        logger.info(f"Analyzing resume: {file_path}")

        # Extract text
        text = self.extract_text_from_file(file_path)
        if not text:
            logger.error("Failed to extract text from resume")
            return None

        logger.debug(f"Extracted {len(text)} characters from resume")

        # Analyze with LLM
        resume_data = self.analyze(text)
        if not resume_data:
            logger.error("Failed to analyze resume")
            return None

        # Ensure required fields
        if not resume_data.get('name') or not resume_data.get('email'):
            logger.warning("Resume missing name or email")
            return None

        logger.info(f"Resume analyzed: {resume_data.get('name')}")
        return resume_data
