import json
import logging
from openai import OpenAI
from config import Config

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
    
    def create_presentation_content(self, topic, description=""):
        """Generate detailed presentation content with varied text formatting"""
        try:
            logger.info(f"Generating content for topic: {topic}")
            
            prompt = f"""Create a detailed presentation outline for the topic: {topic}
            Additional context: {description}
            
            Please provide rich, detailed content for each slide with varied text formatting.
            Each slide should include a combination of these elements as appropriate:
            1. A clear, concise title
            2. An opening paragraph introducing the slide's topic
            3. Detailed bullet points (4-6 points) with sub-bullets where relevant
            4. Key statistics or data points
            5. Specific examples or case studies
            6. Concluding remarks or transition text
            7. For visual slides, include a detailed diagram_prompt
            
            Format as JSON with the following structure:
            {{
                "title": "Main presentation title",
                "slides": [
                    {{
                        "title": "Slide title",
                        "content": [
                            {{
                                "type": "paragraph",
                                "text": "Opening paragraph text..."
                            }},
                            {{
                                "type": "bullets",
                                "items": [
                                    {{
                                        "text": "Main bullet point",
                                        "subitems": ["Sub-bullet 1", "Sub-bullet 2"]
                                    }},
                                    // More bullet points...
                                ]
                            }},
                            {{
                                "type": "stats",
                                "items": ["Statistic 1: Value", "Statistic 2: Value"]
                            }},
                            {{
                                "type": "conclusion",
                                "text": "Concluding remark or transition"
                            }}
                        ],
                        "diagram_prompt": "Optional. Detailed instructions for diagram generation"
                    }}
                ]
            }}

            Make the content substantial and informative, with proper flow between points.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=3000  # Increased for more detailed content
            )
            
            content = response.choices[0].message.content
            parsed_content = json.loads(content)
            
            if not isinstance(parsed_content, dict) or 'title' not in parsed_content or 'slides' not in parsed_content:
                raise ValueError("Invalid content structure received from GPT-4")
            
            return parsed_content
            
        except Exception as e:
            logger.error(f"Error generating presentation content: {str(e)}")
            raise