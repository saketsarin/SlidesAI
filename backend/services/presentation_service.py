import logging
from googleapiclient.discovery import build
from utils.content_validator import ContentValidator
from utils.text_processor import TextProcessor

logger = logging.getLogger(__name__)

class PresentationService:
    def __init__(self, credentials):
        self.service = build('slides', 'v1', credentials=credentials)
    
    def create_slide(self, presentation_id, slide_content, slide_index):
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
            
            response = self.service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={'requests': requests}
            ).execute()
            
            slide_id = response.get('replies')[0]['createSlide']['objectId']
            
            # Get slide details and element IDs
            slide_details = self._get_slide_details(presentation_id, slide_id)
            title_id, body_id = slide_details['title_id'], slide_details['body_id']
            
            # Create and execute update requests
            update_requests = self._create_update_requests(title_id, body_id, slide_content)
            
            self.service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={'requests': update_requests}
            ).execute()
            
            logger.info(f"Successfully created slide {slide_index + 1}")
            
        except Exception as e:
            logger.error(f"Error creating slide {slide_index + 1}: {str(e)}")
            raise
    
    def create_presentation(self, content):
        """Create a new presentation and populate it with slides"""
        try:
            # Create new presentation
            presentation = self.service.presentations().create(
                body={'title': content['title']}
            ).execute()
            presentation_id = presentation.get('presentationId')
            
            # Create slides
            for index, slide in enumerate(content['slides']):
                try:
                    slide_data = ContentValidator.validate_slide_content({
                        'title': slide['title'],
                        'content': [
                            TextProcessor.summarize_long_content(point)
                            for point in slide['content']
                        ]
                    })
                    
                    self.create_slide(presentation_id, slide_data, index)
                    
                except Exception as e:
                    logger.error(f"Error processing slide {index + 1}: {str(e)}")
                    continue
            
            return presentation_id
            
        except Exception as e:
            logger.error(f"Error creating presentation: {str(e)}")
            raise
    
    def _get_slide_details(self, presentation_id, slide_id):
        """Get slide details including element IDs"""
        slide_response = self.service.presentations().get(
            presentationId=presentation_id,
            fields='slides'
        ).execute()
        
        title_id = None
        body_id = None
        
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
        
        return {'title_id': title_id, 'body_id': body_id}
    
    def _create_update_requests(self, title_id, body_id, slide_content):
        """Create update requests for slide content"""
        bullet_points = slide_content['content']
        content_text = '\n• ' + '\n• '.join(bullet_points)
        
        return [
            {
                'insertText': {
                    'objectId': title_id,
                    'text': slide_content['title']
                }
            },
            {
                'insertText': {
                    'objectId': body_id,
                    'text': content_text
                }
            },
            {
                'updateTextStyle': {
                    'objectId': title_id,
                    'style': {
                        'fontSize': {'magnitude': 24, 'unit': 'PT'},
                        'bold': True
                    },
                    'fields': 'fontSize,bold'
                }
            },
            {
                'updateTextStyle': {
                    'objectId': body_id,
                    'style': {
                        'fontSize': {'magnitude': 18, 'unit': 'PT'}
                    },
                    'fields': 'fontSize'
                }
            },
            {
                'updateParagraphStyle': {
                    'objectId': body_id,
                    'style': {
                        'lineSpacing': 115,
                        'spaceAbove': {'magnitude': 10, 'unit': 'PT'},
                        'spaceBelow': {'magnitude': 10, 'unit': 'PT'},
                        'indentStart': {'magnitude': 20, 'unit': 'PT'}
                    },
                    'fields': 'lineSpacing,spaceAbove,spaceBelow,indentStart'
                }
            }
        ]