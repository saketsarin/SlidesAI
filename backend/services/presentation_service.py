import logging
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import os
from config import Config
from services.diagram_service import DiagramService
from utils.content_validator import ContentValidator
from utils.text_processor import TextProcessor

logger = logging.getLogger(__name__)

class PresentationService:
    def __init__(self, credentials):
        self.credentials = credentials
        self.service = build('slides', 'v1', credentials=credentials)
        self.drive_service = build('drive', 'v3', credentials=credentials)
        self.images_folder_id = self._get_or_create_images_folder()

    def _rgb_to_text_color_dict(self, rgb_dict):
        """Convert RGB dictionary to proper Google Slides text color format"""
        return {
            'opaqueColor': {
                'rgbColor': rgb_dict
            }
        }

    def _rgb_to_fill_color_dict(self, rgb_dict):
        """Convert RGB dictionary to proper Google Slides fill color format"""
        return {
            'rgbColor': rgb_dict
        }

    def _apply_theme(self, presentation_id, theme_name='modern'):
        """Apply theme to the presentation with proper color formatting"""
        try:
            theme = Config.PRESENTATION_THEMES.get(theme_name, Config.PRESENTATION_THEMES['modern'])
            
            presentation = self.service.presentations().get(
                presentationId=presentation_id
            ).execute()
            
            slide_ids = [slide.get('objectId') for slide in presentation.get('slides', [])]
            requests = []
            
            for slide_id in slide_ids:
                if 'gradient_color' in theme:
                    requests.append({
                        'updatePageProperties': {
                            'objectId': slide_id,
                            'pageProperties': {
                                'pageBackgroundFill': {
                                    'gradientFill': {
                                        'gradient': {
                                            'type': 'LINEAR',
                                            'stops': [
                                                {
                                                    'position': 0,
                                                    'color': self._rgb_to_fill_color_dict(theme['background_color'])
                                                },
                                                {
                                                    'position': 1,
                                                    'color': self._rgb_to_fill_color_dict(theme['gradient_color'])
                                                }
                                            ]
                                        }
                                    }
                                }
                            },
                            'fields': 'pageBackgroundFill.gradientFill'
                        }
                    })
                else:
                    requests.append({
                        'updatePageProperties': {
                            'objectId': slide_id,
                            'pageProperties': {
                                'pageBackgroundFill': {
                                    'solidFill': {
                                        'color': self._rgb_to_fill_color_dict(theme['background_color'])
                                    }
                                }
                            },
                            'fields': 'pageBackgroundFill.solidFill'
                        }
                    })
            
            if requests:
                self.service.presentations().batchUpdate(
                    presentationId=presentation_id,
                    body={'requests': requests}
                ).execute()
            
            logger.info(f"Applied theme {theme_name} to presentation {presentation_id}")
            
        except Exception as e:
            logger.error(f"Error applying theme: {str(e)}")
            raise
    
    def _get_or_create_images_folder(self):
        """Get or create a folder for presentation images"""
        try:
            folder_name = "SlidesAI_Images"
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            
            results = self.drive_service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            existing_folders = results.get('files', [])
            
            if existing_folders:
                logger.info(f"Found existing images folder: {existing_folders[0]['id']}")
                return existing_folders[0]['id']
            
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            folder = self.drive_service.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()
            
            folder_id = folder.get('id')
            logger.info(f"Created new images folder: {folder_id}")
            return folder_id
            
        except Exception as e:
            logger.error(f"Error creating images folder: {str(e)}")
            raise

    def _get_text_ranges(self, content):
        """Find ranges of different text styles in the content"""
        ranges = []
        lines = content.split('\n')
        current_index = 0
        
        for line in lines:
            line_length = len(line) + 1  # +1 for newline
            
            if line.startswith('📊'):
                ranges.append({
                    'start': current_index,
                    'end': current_index + line_length,
                    'style': 'stats'
                })
            elif line.startswith('Key Statistics:'):
                ranges.append({
                    'start': current_index,
                    'end': current_index + line_length,
                    'style': 'heading'
                })
            
            current_index += line_length
        
        return ranges

    def _format_content(self, content_blocks):
        """Format varied content types into slide text"""
        formatted_text = ""
        
        for block in content_blocks:
            block_type = block.get('type', '')
            
            if block_type == 'paragraph':
                formatted_text += f"{block['text']}\n\n"
            
            elif block_type == 'bullets':
                for item in block['items']:
                    if isinstance(item, dict):
                        # Main bullet with sub-bullets
                        formatted_text += f"• {item['text']}\n"
                        for subitem in item.get('subitems', []):
                            formatted_text += f"    ◦ {subitem}\n"
                    else:
                        # Simple bullet point
                        formatted_text += f"• {item}\n"
                formatted_text += "\n"
            
            elif block_type == 'stats':
                formatted_text += "Key Statistics:\n"
                for stat in block['items']:
                    formatted_text += f"📊 {stat}\n"
                formatted_text += "\n"
            
            elif block_type == 'conclusion':
                formatted_text += f"\n{block['text']}\n"
        
        return formatted_text.strip()
    
    def _create_text_style_request(self, object_id, range_info, style_type):
        """Create a properly formatted text style request"""
        base_request = {
            'updateTextStyle': {
                'objectId': object_id,
                'textRange': {
                    'type': 'FIXED_RANGE',
                    'startIndex': range_info['start'],
                    'endIndex': range_info['end']
                },
                'style': {},
                'fields': ''
            }
        }
        
        if style_type == 'heading':
            base_request['updateTextStyle'].update({
                'style': {
                    'bold': True,
                    'fontSize': {'magnitude': 16, 'unit': 'PT'}
                },
                'fields': 'bold,fontSize'
            })
        elif style_type == 'stats':
            base_request['updateTextStyle'].update({
                'style': {
                    'foregroundColor': {
                        'opaqueColor': {'rgbColor': {'red': 0.2, 'green': 0.4, 'blue': 0.7}}
                    },
                    'bold': True
                },
                'fields': 'foregroundColor,bold'
            })
        elif style_type == 'bullet':
            base_request['updateTextStyle'].update({
                'style': {
                    'fontSize': {'magnitude': 14, 'unit': 'PT'}
                },
                'fields': 'fontSize'
            })
        elif style_type == 'subbullet':
            base_request['updateTextStyle'].update({
                'style': {
                    'fontSize': {'magnitude': 12, 'unit': 'PT'}
                },
                'fields': 'fontSize'
            })
        elif style_type == 'paragraph':
            base_request['updateTextStyle'].update({
                'style': {
                    'fontSize': {'magnitude': 14, 'unit': 'PT'}
                },
                'fields': 'fontSize'
            })
        
        return base_request
    
    def _create_slide(self, presentation_id, index, slide_content, theme_name='modern'):
        """Create a slide with themed formatting"""
        try:
            theme = Config.PRESENTATION_THEMES.get(theme_name, Config.PRESENTATION_THEMES['modern'])
            
            has_image = 'diagram_prompt' in slide_content and slide_content['diagram_prompt']
            layout = 'TITLE_AND_TWO_COLUMNS' if has_image else 'TITLE_AND_BODY'
            
            requests = [{
                'createSlide': {
                    'insertionIndex': index,
                    'slideLayoutReference': {
                        'predefinedLayout': layout
                    }
                }
            }]
            
            response = self.service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={'requests': requests}
            ).execute()
            
            slide_id = response.get('replies')[0]['createSlide']['objectId']
            slide_details = self._get_slide_details(presentation_id, slide_id)
            title_id, body_id = slide_details['title_id'], slide_details['body_id']
            
            formatted_text = self._format_content(slide_content['content'])
            
            # Convert colors to proper format for text
            primary_color = self._rgb_to_text_color_dict(theme['primary_color'])
            secondary_color = self._rgb_to_text_color_dict(theme.get('secondary_color', theme['primary_color']))
            
            text_requests = [
                {
                    'insertText': {
                        'objectId': title_id,
                        'text': slide_content['title']
                    }
                },
                {
                    'insertText': {
                        'objectId': body_id,
                        'text': formatted_text
                    }
                },
                {
                    'updateTextStyle': {
                        'objectId': title_id,
                        'style': {
                            'fontSize': {'magnitude': 24, 'unit': 'PT'},
                            'bold': True,
                            'foregroundColor': primary_color
                        },
                        'fields': 'fontSize,bold,foregroundColor'
                    }
                },
                {
                    'updateTextStyle': {
                        'objectId': body_id,
                        'style': {
                            'fontSize': {'magnitude': 14, 'unit': 'PT'},
                            'foregroundColor': secondary_color
                        },
                        'fields': 'fontSize,foregroundColor'
                    }
                },
                {
                    'updateParagraphStyle': {
                        'objectId': body_id,
                        'style': {
                            'lineSpacing': 150,
                            'spaceAbove': {'magnitude': 10, 'unit': 'PT'},
                            'spaceBelow': {'magnitude': 10, 'unit': 'PT'},
                            'indentStart': {'magnitude': 20, 'unit': 'PT'}
                        },
                        'fields': 'lineSpacing,spaceAbove,spaceBelow,indentStart'
                    }
                }
            ]
            
            if has_image:
                text_requests.append({
                    'updatePageElementTransform': {
                        'objectId': body_id,
                        'transform': {
                            'scaleX': 1,
                            'scaleY': 1,
                            'translateX': 30,
                            'translateY': 100,
                            'unit': 'PT'
                        },
                        'applyMode': 'ABSOLUTE'
                    }
                })
            
            # Execute text updates
            self.service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={'requests': text_requests}
            ).execute()
            
            return slide_id
            
        except Exception as e:
            logger.error(f"Error creating slide {index + 1}: {str(e)}")
            raise
    
    def create_presentation(self, content, theme_name='modern'):
        """Create a new presentation with theme"""
        try:
            # Create presentation
            presentation = self.service.presentations().create(
                body={'title': content['title']}
            ).execute()
            
            presentation_id = presentation.get('presentationId')
            
            # Apply theme first
            self._apply_theme(presentation_id, theme_name)

            # Initialize diagram service if needed
            diagram_service = DiagramService()
            
            # Create slides
            for index, slide_content in enumerate(content['slides']):
                slide_id = self._create_slide(presentation_id, index, slide_content, theme_name)
                
                # Generate and insert diagram if needed
                if 'diagram_prompt' in slide_content and slide_content['diagram_prompt']:
                    try:
                        image_path = diagram_service.generate_diagram(slide_content['diagram_prompt'])
                        self.insert_diagram(presentation_id, slide_id, image_path)
                    except Exception as e:
                        logger.error(f"Error generating/inserting diagram for slide {index + 1}: {str(e)}")
            
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
    
    def insert_diagram(self, presentation_id, slide_id, image_path):
        """Insert a diagram into a slide on the right side"""
        try:
            # Upload image to Google Drive
            media = MediaFileUpload(
                image_path, 
                mimetype='image/png',
                resumable=True
            )
            
            file_metadata = {
                'name': os.path.basename(image_path),
                'parents': [self.images_folder_id]
            }
            
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webContentLink'
            ).execute()
            
            image_id = file.get('id')
            
            # Set public access permission
            self.drive_service.permissions().create(
                fileId=image_id,
                body={
                    'type': 'anyone',
                    'role': 'reader',
                    'allowFileDiscovery': False
                }
            ).execute()
            
            # Format the correct image URL
            image_url = f"https://drive.google.com/uc?export=view&id={image_id}"
            
            # Calculate positions for right-side placement
            image_width = 350  # PT
            image_height = 250  # PT
            right_margin = 30  # PT
            image_x = 720 - image_width - right_margin
            
            # Create image with positioning for right side
            requests = [{
                'createImage': {
                    'url': image_url,
                    'elementProperties': {
                        'pageObjectId': slide_id,
                        'size': {
                            'width': {'magnitude': image_width, 'unit': 'PT'},
                            'height': {'magnitude': image_height, 'unit': 'PT'}
                        },
                        'transform': {
                            'scaleX': 1,
                            'scaleY': 1,
                            'translateX': image_x,
                            'translateY': 150,
                            'unit': 'PT'
                        }
                    }
                }
            }]
            
            # Execute the image insertion
            self.service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={'requests': requests}
            ).execute()
            
            # Clean up local file
            try:
                os.remove(image_path)
            except Exception as e:
                logger.warning(f"Could not delete temporary image file: {str(e)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error inserting diagram: {str(e)}")
            raise