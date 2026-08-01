import google.generativeai as genai
from typing import Optional
from logging_monitor.logger import get_logger

logger = get_logger("jobber")


class GeminiClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def generate(self, prompt: str, max_tokens: int = 2048) -> Optional[str]:
        """Generate text using Gemini API."""
        try:
            logger.debug(f"Gemini API call: {len(prompt)} chars prompt")
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.7,
                )
            )
            if response.text:
                logger.debug(f"Gemini response: {len(response.text)} chars")
                return response.text
            return None
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            return None

    def generate_json(self, prompt: str) -> Optional[dict]:
        """Generate JSON response."""
        import json
        try:
            response = self.generate(prompt)
            if response:
                json_str = response.strip()
                if json_str.startswith("```json"):
                    json_str = json_str[7:]
                if json_str.startswith("```"):
                    json_str = json_str[3:]
                if json_str.endswith("```"):
                    json_str = json_str[:-3]
                return json.loads(json_str.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
        except Exception as e:
            logger.error(f"Gemini JSON generation error: {str(e)}")
        return None
