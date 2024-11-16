import logging
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from config import Config

logger = logging.getLogger(__name__)

class GoogleService:
    @staticmethod
    def get_credentials():
        """Get and refresh Google API credentials"""
        try:
            creds = None
            if Path('token.json').exists():
                creds = Credentials.from_authorized_user_file('token.json', Config.GOOGLE_SCOPES)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    with open('token.json', 'w') as token:
                        token.write(creds.to_json())
                else:
                    if not Path(Config.CLIENT_SECRETS_FILE).exists():
                        raise Exception("client_secrets.json file not found")
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        Config.CLIENT_SECRETS_FILE,
                        Config.GOOGLE_SCOPES
                    )
                    creds = flow.run_local_server(port=8080)
                    
                    with open('token.json', 'w') as token:
                        token.write(creds.to_json())
            
            return creds
        except Exception as e:
            logger.error(f"Error getting credentials: {str(e)}")
            raise
    
    @staticmethod
    def initialize_credentials():
        """Initialize Google credentials and generate token.json"""
        if not Path(Config.CLIENT_SECRETS_FILE).exists():
            logger.error("client_secrets.json not found!")
            return False
        
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                Config.CLIENT_SECRETS_FILE,
                Config.GOOGLE_SCOPES
            )
            creds = flow.run_local_server(port=8080)
            
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
            logger.info("Successfully generated token.json")
            return True
        except Exception as e:
            logger.error(f"Error initializing credentials: {e}")
            return False