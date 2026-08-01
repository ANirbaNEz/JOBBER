from typing import Optional, Dict, List
from logging_monitor.logger import get_logger

logger = get_logger("jobber")


class MockLLM:
    """Mock LLM for testing. Returns realistic but hardcoded responses."""

    def generate(self, prompt: str, max_tokens: int = 2048) -> Optional[str]:
        """Return a mock response."""
        if "resume" in prompt.lower() and "tailor" in prompt.lower():
            return """{"name": "Your Name", "email": "your.email@example.com", "phone": "+1-555-1234", "summary": "Experienced Python engineer with strong backend development skills and proven ability to build scalable systems.", "skills": ["Python", "FastAPI", "PostgreSQL", "REST APIs", "Docker", "Git", "System Design", "Agile"], "experience": [{"title": "Senior Software Engineer", "company": "Tech Company A", "duration": "2021-Present", "description": "Led architecture and development of microservices platform serving 10M+ users. Mentored team of 5 engineers."}], "education": [{"degree": "Bachelor of Science in Computer Science", "school": "University Name", "year": 2016}]}"""

        elif "cover letter" in prompt.lower():
            return """I am a Senior Python Engineer with 5+ years of experience building scalable backend systems. I'm excited about this opportunity because your company is at the forefront of modern web technologies, and I'm particularly interested in your microservices architecture. My experience with FastAPI, PostgreSQL, and system design aligns perfectly with your team's needs, and I'm eager to contribute to building products that impact millions of users. I would welcome the opportunity to discuss how my expertise can contribute to your team's success."""

        elif "question" in prompt.lower() and "answer" in prompt.lower():
            return """[
{"question": "Why are you interested in this position?", "answer": "I'm genuinely excited about this role because of your company's innovative approach to backend engineering. The tech stack you're using (FastAPI, PostgreSQL) aligns perfectly with my expertise, and I'm impressed by your commitment to scalable, maintainable code."},
{"question": "What relevant experience do you have?", "answer": "I have 5+ years as a Senior Software Engineer, where I architected and led microservices platforms handling 10M+ users. I've built REST APIs, optimized database queries, and mentored teams of engineers in Agile environments."},
{"question": "Describe a challenging project you worked on", "answer": "I led a major database migration that reduced query latency by 40% without downtime. This involved careful planning, coordinated execution, and extensive testing to ensure zero data loss and minimal user impact."},
{"question": "Where do you see yourself in 5 years?", "answer": "I aspire to be a technical leader and architect, guiding teams on strategic technology decisions. I want to deepen my expertise in distributed systems while also developing my mentorship skills to help other engineers grow."}
]"""

        logger.debug("Mock LLM response generated")
        return None

    def generate_json(self, prompt: str) -> Optional[Dict]:
        """Generate JSON response."""
        import json
        response = self.generate(prompt)
        if response:
            try:
                json_str = response.strip()
                if json_str.startswith("```json"):
                    json_str = json_str[7:]
                if json_str.startswith("```"):
                    json_str = json_str[3:]
                if json_str.endswith("```"):
                    json_str = json_str[:-3]
                return json.loads(json_str.strip())
            except json.JSONDecodeError:
                pass
        return None
