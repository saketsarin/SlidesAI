import json
import logging
from openai import OpenAI
from config import Config

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
    
    def create_presentation_content(self, topic, description=""):
        """Generate presentation content using GPT-4"""
        try:
            logger.info(f"Generating content for topic: {topic}")
            
            prompt = f"""Create a detailed presentation outline for the topic: {topic}
            Additional context: {description}
            
            Please provide:
            1. A compelling title
            2. 10 main sections
            3. 3-4 key points for each section
            4. Relevant examples or data points where applicable
            
            Format as JSON with the following structure:
            {{
                "title": "Main title",
                "slides": [
                    {{"title": "Slide title", "content": ["point 1", "point 2", "point 3"]}},
                ]
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            parsed_content = json.loads(content)
            
            if not isinstance(parsed_content, dict) or 'title' not in parsed_content or 'slides' not in parsed_content:
                raise ValueError("Invalid content structure received from GPT-4")
            
            return parsed_content
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            raise Exception("Failed to parse presentation content")
        except Exception as e:
            logger.error(f"Error generating presentation content: {str(e)}")
            raise