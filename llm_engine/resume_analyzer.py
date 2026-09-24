import json
import re
from pathlib import Path
from typing import Dict, Any
from logging_monitor.logger import get_logger

logger = get_logger("jobber")

# Common tech/professional skills to detect via keyword match in local fallback mode
COMMON_SKILLS = [
    "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "PHP", "Ruby", "Go", "Rust",
    "Swift", "Kotlin", "SQL", "HTML", "HTML5", "CSS", "CSS3", "React", "React.js", "Angular",
    "Vue", "Vue.js", "Node.js", "Express.js", "Django", "Flask", "FastAPI", "Spring", "Spring Boot",
    ".NET", "ASP.NET", "Ruby on Rails", "Laravel", "PostgreSQL", "MySQL", "MongoDB", "Redis",
    "SQLite", "Oracle", "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Jenkins", "Git", "GitHub",
    "GitLab", "CI/CD", "REST", "REST APIs", "GraphQL", "gRPC", "Microservices", "Linux", "Bash",
    "Agile", "Scrum", "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "Pandas",
    "NumPy", "Scikit-learn", "Tableau", "Power BI", "Excel", "JIRA", "Terraform", "Ansible",
    "Nginx", "Apache", "GraphQL", "JWT", "OAuth", "Webpack", "Redux", "Next.js", "Tailwind",
    "Bootstrap", "jQuery", "R", "MATLAB", "Scala", "Hadoop", "Spark", "Kafka", "RabbitMQ"
]


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

    def analyze_local(self, resume_text: str) -> Dict[str, Any]:
        """Regex/heuristic-based extraction, used when the LLM is unavailable
        (quota exceeded, API error, etc). Extracts real data from the text
        directly instead of returning nothing or fake placeholder data."""
        if not resume_text or len(resume_text.strip()) < 20:
            return None

        # Email
        email_match = re.search(r'[\w\.\-+]+@[\w\-]+\.[\w\.\-]+', resume_text)
        email = email_match.group(0) if email_match else ""

        # Phone (handles +91, dashes, spaces, parens)
        phone_match = re.search(r'(\+?\d{1,3}[\s\-]?)?(\(?\d{3,5}\)?[\s\-]?){2,4}\d{3,4}', resume_text)
        phone = phone_match.group(0).strip() if phone_match else ""

        # Name: PDFs often merge the name with phone/email on one line with no
        # separator (e.g. "JOHN SMITH9876543210 | john@x.com"). Take the first
        # non-empty line, strip out the matched email/phone substrings, then
        # take what's left as the name.
        name = ""
        for line in resume_text.splitlines():
            line = line.strip()
            if not line:
                continue
            candidate = line
            if email and email in candidate:
                candidate = candidate.replace(email, ' ')
            if phone and phone in candidate:
                candidate = candidate.replace(phone, ' ')
            # Strip any leftover digits and non-letter separator characters
            # (bullets, middle dots, nbsp, pipes, etc. commonly found between
            # name/phone/email on a resume header line)
            candidate = re.sub(r'\d+', ' ', candidate)
            candidate = re.sub(r"[^A-Za-z.'\-\s]", ' ', candidate)
            candidate = re.sub(r'\s+', ' ', candidate).strip()

            words = candidate.split()
            if 1 < len(words) <= 5 and all(w[0].isupper() for w in words if w and w[0].isalpha()) \
                    and all(re.fullmatch(r"[A-Za-z.'-]+", w) for w in words):
                name = candidate
                break

        # Skills: keyword match against common skills list
        found_skills = []
        text_lower = resume_text.lower()
        for skill in COMMON_SKILLS:
            pattern = r'(?<![\w.])' + re.escape(skill.lower()) + r'(?![\w])'
            if re.search(pattern, text_lower):
                found_skills.append(skill)

        # Summary: first substantial paragraph-like line that isn't the
        # header (skip lines with email/heavy digits - that's contact info)
        summary = ""
        for line in resume_text.splitlines():
            line = line.strip()
            if len(line) > 60 and '@' not in line and sum(c.isdigit() for c in line) <= 2:
                summary = line[:300]
                break

        if not name and not email:
            return None

        return {
            "name": name or "Unknown",
            "email": email,
            "phone": phone,
            "summary": summary or f"Professional with experience in {', '.join(found_skills[:5])}." if found_skills else "",
            "skills": found_skills,
            "experience": [],
            "education": [],
            "_extraction_method": "local_fallback"
        }

    def process_file(self, file_path: str) -> Dict[str, Any]:
        """Extract text from file and analyze with LLM, falling back to
        local regex/heuristic extraction if the LLM is unavailable."""
        logger.info(f"Analyzing resume: {file_path}")

        # Extract text
        text = self.extract_text_from_file(file_path)
        if not text:
            logger.error("Failed to extract text from resume")
            return None

        logger.debug(f"Extracted {len(text)} characters from resume")

        # Try LLM analysis first
        resume_data = self.analyze(text)

        # Fall back to local extraction if LLM failed or is unavailable
        if not resume_data or not resume_data.get('name') or not resume_data.get('email'):
            logger.warning("LLM analysis failed or incomplete, falling back to local extraction")
            local_data = self.analyze_local(text)
            if local_data:
                resume_data = local_data
            elif not resume_data:
                logger.error("Both LLM and local extraction failed")
                return None

        # Ensure required fields
        if not resume_data.get('name') or not resume_data.get('email'):
            logger.warning("Resume missing name or email after all extraction attempts")
            return None

        logger.info(f"Resume analyzed: {resume_data.get('name')} (method: {resume_data.get('_extraction_method', 'llm')})")
        return resume_data
