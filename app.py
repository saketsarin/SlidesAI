import os
import json
import logging
from flask import Flask, request, jsonify
from openai import OpenAI
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from nltk.tokenize import sent_tokenize
import nltk
from dotenv import load_dotenv
from pathlib import Path
from flask_cors import CORS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Download required NLTK data
nltk.download('punkt', quiet=True)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Google Slides API setup
SCOPES = ['https://www.googleapis.com/auth/presentations', 'https://www.googleapis.com/auth/drive.file']
CLIENT_SECRETS_FILE = "client_secrets.json"

def get_credentials():
    """Get and refresh Google API credentials"""
    try:
        creds = None
        if Path('token.json').exists():
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
            else:
                if not Path(CLIENT_SECRETS_FILE).exists():
                    raise Exception("client_secrets.json file not found")
                
                # Use InstalledAppFlow instead of Flow
                from google_auth_oauthlib.flow import InstalledAppFlow
                flow = InstalledAppFlow.from_client_secrets_file(
                    CLIENT_SECRETS_FILE,
                    SCOPES
                )
                creds = flow.run_local_server(port=8080)
                
                # Save the credentials for the next run
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
        
        return creds
    except Exception as e:
        logger.error(f"Error getting credentials: {str(e)}")
        raise

def initialize_google_credentials():
    """Initialize Google credentials and generate token.json"""
    from google_auth_oauthlib.flow import InstalledAppFlow
    
    if not Path(CLIENT_SECRETS_FILE).exists():
        print("Error: client_secrets.json not found!")
        return False
    
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            SCOPES
        )
        creds = flow.run_local_server(port=8080)
        
        # Save the credentials
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        print("Successfully generated token.json")
        return True
    except Exception as e:
        print(f"Error initializing credentials: {e}")
        return False
    
def create_presentation_content(topic, description=""):
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
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000
        )
        
        content = response.choices[0].message.content
        # Validate JSON structure
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

def summarize_long_content(text, max_sentences=3):
    """Summarize long content using NLTK"""
    try:
        sentences = sent_tokenize(text)
        if len(sentences) <= max_sentences:
            return text
        return ' '.join(sentences[:max_sentences])
    except Exception as e:
        return text

def create_google_slide(service, presentation_id, slide_content, slide_index):
    """Create a single slide in Google Slides with proper element targeting"""
    try:
        # Create the slide
        requests = [{
            'createSlide': {
                'insertionIndex': slide_index,
                'slideLayoutReference': {
                    'predefinedLayout': 'TITLE_AND_BODY'
                }
            }
        }]
        
        response = service.presentations().batchUpdate(
            presentationId=presentation_id,
            body={'requests': requests}
        ).execute()
        
        slide_id = response.get('replies')[0]['createSlide']['objectId']
        
        # Get the slide details
        slide_response = service.presentations().get(
            presentationId=presentation_id,
            fields='slides'
        ).execute()
        
        # Find the created slide and its elements
        for slide in slide_response.get('slides', []):
            if slide.get('objectId') == slide_id:
                for element in slide.get('pageElements', []):
                    shape = element.get('shape', {})
                    placeholder = shape.get('placeholder', {})
                    if placeholder.get('type') == 'TITLE':
                        title_id = element.get('objectId')
                    elif placeholder.get('type') == 'BODY':
                        body_id = element.get('objectId')
        
        if not title_id or not body_id:
            raise Exception("Could not find title or body placeholders")
        
        # Format bullet points
        bullet_points = slide_content['content']
        content_text = '\n• ' + '\n• '.join(bullet_points)
        
        # Create text insertion requests
        update_requests = [
            # Insert title
            {
                'insertText': {
                    'objectId': title_id,
                    'text': slide_content['title']
                }
            },
            # Insert body
            {
                'insertText': {
                    'objectId': body_id,
                    'text': content_text
                }
            },
            # Format title
            {
                'updateTextStyle': {
                    'objectId': title_id,
                    'style': {
                        'fontSize': {
                            'magnitude': 24,
                            'unit': 'PT'
                        },
                        'bold': True
                    },
                    'fields': 'fontSize,bold'
                }
            },
            # Format body
            {
                'updateTextStyle': {
                    'objectId': body_id,
                    'style': {
                        'fontSize': {
                            'magnitude': 18,
                            'unit': 'PT'
                        }
                    },
                    'fields': 'fontSize'
                }
            },
            # Add paragraph styling
            {
                'updateParagraphStyle': {
                    'objectId': body_id,
                    'style': {
                        'lineSpacing': 115,
                        'spaceAbove': {
                            'magnitude': 10,
                            'unit': 'PT'
                        },
                        'spaceBelow': {
                            'magnitude': 10,
                            'unit': 'PT'
                        },
                        'indentStart': {
                            'magnitude': 20,
                            'unit': 'PT'
                        }
                    },
                    'fields': 'lineSpacing,spaceAbove,spaceBelow,indentStart'
                }
            }
        ]
        
        # Execute the updates
        service.presentations().batchUpdate(
            presentationId=presentation_id,
            body={'requests': update_requests}
        ).execute()
        
        logger.info(f"Successfully created slide {slide_index + 1}")
        
    except Exception as e:
        logger.error(f"Error creating slide {slide_index + 1}: {str(e)}")
        raise Exception(f"Error creating slide {slide_index + 1}: {str(e)}")

# Add helper function to validate presentation content
def validate_slide_content(slide_content):
    """Validate the content for a slide"""
    if not isinstance(slide_content, dict):
        raise ValueError("Slide content must be a dictionary")
    
    if 'title' not in slide_content:
        raise ValueError("Slide must have a title")
    
    if 'content' not in slide_content:
        raise ValueError("Slide must have content")
    
    if not isinstance(slide_content['content'], list):
        raise ValueError("Slide content must be a list")
    
    # Ensure content isn't too long
    MAX_POINTS = 10
    MAX_POINT_LENGTH = 200
    
    if len(slide_content['content']) > MAX_POINTS:
        slide_content['content'] = slide_content['content'][:MAX_POINTS]
    
    # Truncate long points
    slide_content['content'] = [
        point[:MAX_POINT_LENGTH] + '...' if len(point) > MAX_POINT_LENGTH else point
        for point in slide_content['content']
    ]
    
    return slide_content

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200

@app.route('/create_presentation', methods=['POST'])
def create_presentation():
    """API endpoint to create presentation"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        topic = data.get('topic')
        description = data.get('description', '')
        
        if not topic:
            return jsonify({'error': 'Topic is required'}), 400
        
        # Generate and validate presentation content
        presentation_content = create_presentation_content(topic, description)
        
        credentials = get_credentials()
        service = build('slides', 'v1', credentials=credentials)
        
        # Create new presentation
        presentation = service.presentations().create(
            body={'title': presentation_content['title']}
        ).execute()
        presentation_id = presentation.get('presentationId')
        
        # Create slides with validation
        for index, slide in enumerate(presentation_content['slides']):
            try:
                # Validate and clean slide content
                slide_data = validate_slide_content({
                    'title': slide['title'],
                    'content': [
                        summarize_long_content(point)
                        for point in slide['content']
                    ]
                })
                
                create_google_slide(service, presentation_id, slide_data, index)
                
            except Exception as e:
                logger.error(f"Error processing slide {index + 1}: {str(e)}")
                continue  # Continue with next slide if one fails
        
        presentation_url = f"https://docs.google.com/presentation/d/{presentation_id}/edit"
        
        return jsonify({
            'success': True,
            'presentation_url': presentation_url,
            'presentation_id': presentation_id
        })
    
    except Exception as e:
        logger.error(f"Presentation creation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Verify environment setup before starting
    if not os.getenv('OPENAI_API_KEY'):
        logger.error("OpenAI API key not found in environment variables")
        print("Error: OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.")
        exit(1)
    
    if not Path(CLIENT_SECRETS_FILE).exists():
        logger.error("client_secrets.json file not found")
        print("Error: client_secrets.json file not found. Please ensure it exists in the project directory.")
        exit(1)
    
    # Initialize Google credentials if token.json doesn't exist
    if not Path('token.json').exists():
        print("Initializing Google credentials...")
        if not initialize_google_credentials():
            print("Failed to initialize Google credentials")
            exit(1)
    
    app.run(debug=False, host='127.0.0.1', port=5000)