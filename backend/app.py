import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from pathlib import Path
from config import Config
from services.openai_service import OpenAIService
from services.google_service import GoogleService
from services.presentation_service import PresentationService
from services.diagram_service import DiagramService
from utils.text_processor import TextProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize services
openai_service = OpenAIService()
TextProcessor.initialize()

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
        
        # Generate presentation content
        presentation_content = openai_service.create_presentation_content(topic, description)
        
        # Get Google credentials and create presentation
        credentials = GoogleService.get_credentials()
        presentation_service = PresentationService(credentials)
        
        presentation_id = presentation_service.create_presentation(presentation_content)
        presentation_url = f"https://docs.google.com/presentation/d/{presentation_id}/edit"
        
        return jsonify({
            'success': True,
            'presentation_url': presentation_url,
            'presentation_id': presentation_id
        })
    
    except Exception as e:
        logger.error(f"Presentation creation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

def verify_environment():
    """Verify environment setup"""
    if not Config.OPENAI_API_KEY:
        logger.error("OpenAI API key not found in environment variables")
        return False
    
    if not Path(Config.CLIENT_SECRETS_FILE).exists():
        logger.error("client_secrets.json file not found")
        return False
    
    # Initialize Google credentials if token.json doesn't exist
    if not Path('token.json').exists():
        logger.info("Initializing Google credentials...")
        if not GoogleService.initialize_credentials():
            logger.error("Failed to initialize Google credentials")
            return False
    
    return True

@app.route('/generate_diagram', methods=['POST'])
def generate_diagram():
    """API endpoint to generate a diagram"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        prompt = data.get('prompt')
        presentation_id = data.get('presentationId')
        slide_id = data.get('slideId')
        
        if not all([prompt, presentation_id, slide_id]):
            return jsonify({'error': 'Missing required parameters'}), 400
        
        # Generate diagram
        diagram_service = DiagramService()
        image_path = diagram_service.generate_diagram(prompt)
        
        # Insert into presentation
        credentials = GoogleService.get_credentials()
        presentation_service = PresentationService(credentials)
        presentation_service.insert_diagram(presentation_id, slide_id, image_path)
        
        return jsonify({
            'success': True,
            'message': 'Diagram generated and inserted successfully'
        })
        
    except Exception as e:
        logger.error(f"Diagram generation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    if not verify_environment():
        exit(1)
    
    app.run(
        debug=Config.DEBUG,
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT
    )