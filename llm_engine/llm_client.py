import google.generativeai as genai
from typing import Optional
from logging_monitor.logger import get_logger

logger = get_logger("jobber")


class GeminiClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=api_key)
        # Try different models in order of preference (newest first)
        models_to_try = [
            "gemini-3.6-flash",
            "gemini-2.0-flash",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-pro"
        ]

        self.model = None
        for model_name in models_to_try:
            try:
                self.model = genai.GenerativeModel(model_name)
                logger.info(f"Using {model_name} model")
                break
            except Exception as e:
                logger.debug(f"Model {model_name} not available: {str(e)}")
                continue

        if not self.model:
            raise Exception("No available Gemini models found")

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
