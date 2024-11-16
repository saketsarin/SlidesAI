# setup_google_auth.py
import os
import sys
from google_auth_oauthlib.flow import InstalledAppFlow
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define the scopes
SCOPES = [
    'https://www.googleapis.com/auth/presentations',
    'https://www.googleapis.com/auth/drive.file'
]

REDIRECT_URI = 'http://localhost:8080'

def print_instructions():
    """Print setup instructions"""
    print("\n=== Google OAuth Setup Instructions ===")
    print("\n1. Ensure you have your client_secrets.json file:")
    print("   - Go to https://console.cloud.google.com")
    print("   - Select your project")
    print("   - Go to 'APIs & Services' > 'Credentials'")
    print("   - Click on your OAuth 2.0 Client ID")
    print("   - Click 'DOWNLOAD JSON' and save as 'client_secrets.json' in this directory")
    print("\n2. Add these Authorized redirect URIs in Google Cloud Console:")
    print("   - http://localhost:8080/")
    print("   - http://127.0.0.1:8080/")
    print("\n3. Enable necessary APIs:")
    print("   - Google Slides API")
    print("   - Google Drive API")
    print("\nAfter completing these steps, run this script again.")

def verify_client_secrets():
    """Verify client_secrets.json file"""
    client_secrets_file = Path("client_secrets.json")
    
    if not client_secrets_file.exists():
        print("\n❌ Error: client_secrets.json not found!")
        print_instructions()
        return False
    
    try:
        import json
        with open(client_secrets_file) as f:
            config = json.load(f)
        
        # Basic validation of file structure
        if 'web' not in config or 'client_id' not in config['web']:
            print("\n❌ Error: Invalid client_secrets.json format!")
            print_instructions()
            return False
            
        return True
    except json.JSONDecodeError:
        print("\n❌ Error: client_secrets.json is not valid JSON!")
        print_instructions()
        return False
    except Exception as e:
        print(f"\n❌ Error reading client_secrets.json: {str(e)}")
        print_instructions()
        return False

def setup_google_credentials():
    """Set up Google credentials and generate token.json"""
    print("\n🔄 Setting up Google credentials...")
    
    if not verify_client_secrets():
        return False
    
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            'client_secrets.json',
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        
        # Clear any existing credentials
        if Path('token.json').exists():
            Path('token.json').unlink()
        
        print("\n✨ Opening browser for authentication...")
        print("Please complete the authentication process in your browser.")
        
        creds = flow.run_local_server(
            port=8080,
            prompt='consent',
            access_type='offline'
        )
        
        # Save the credentials
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        
        print("\n✅ Successfully generated token.json")
        print("You can now run the main application!")
        return True
    
    except Exception as e:
        print(f"\n❌ Error during setup: {str(e)}")
        
        if "redirect_uri_mismatch" in str(e):
            print("\n⚠️ Redirect URI Mismatch Error!")
            print("Please ensure you've added these URIs in Google Cloud Console:")
            print("- http://localhost:8080/")
            print("- http://127.0.0.1:8080/")
        
        print_instructions()
        return False

def main():
    """Main setup function"""
    print("\n🚀 Google OAuth Setup Wizard")
    print("============================")
    
    if setup_google_credentials():
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Run the Flask backend: python app.py")
        print("2. Run the Streamlit frontend: streamlit run streamlit_app.py")
    else:
        print("\n❌ Setup failed. Please fix the errors and try again.")
        sys.exit(1)

if __name__ == '__main__':
    main()