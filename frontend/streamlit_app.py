import streamlit as st
import requests
import json
import time
from utils.ui_helpers import UIHelper

class PresentationApp:
    def __init__(self):
        self.api_url = 'http://127.0.0.1:5000'
        self.setup_page()
    
    def setup_page(self):
        """Configure Streamlit page settings"""
        st.set_page_config(
            page_title="AI Presentation Generator",
            page_icon="📊",
            layout="centered"
        )
        
        st.title("🎯 AI Presentation Generator")
        st.write("Generate professional presentations powered by GPT-4")
    
    def check_backend_health(self):
        """Check if backend service is running"""
        try:
            health_check = requests.get(f'{self.api_url}/health')
            if health_check.status_code != 200:
                st.sidebar.error("❌ Backend service is not responding properly")
                return False
            return True
        except:
            st.sidebar.error("❌ Backend service is not running")
            st.error("Please ensure the Flask backend is running (python app.py)")
            return False
    
    def generate_presentation(self, topic, description=""):
        """Generate presentation with single-line progress tracking"""
        steps = [
            ("🔄 Initializing...", 10),
            ("🤖 Connecting to AI service...", 20),
            ("📝 Generating content...", 40),
            ("🎨 Creating slides...", 60),
            ("📊 Formatting presentation...", 80),
            ("✅ Finalizing...", 90),
        ]
        
        status_text = st.empty()
        progress_bar = st.progress(0)
        
        try:
            headers = {'Content-Type': 'application/json'}
            payload = {
                'topic': topic,
                'description': description
            }
            
            # Show progress while making request
            for message, progress in steps:
                status_text.write(message)
                progress_bar.progress(progress)
                time.sleep(0.5)  # Simulate progress
            
            response = requests.post(
                f'{self.api_url}/create_presentation',
                headers=headers,
                data=json.dumps(payload),
                timeout=180
            )
            
            if response.status_code != 200:
                error_data = response.json()
                error_message = error_data.get('error', 'Unknown error occurred')
                st.error(f"Server Error: {error_message}")
                return None
            
            # Show completion
            status_text.write("✨ Presentation ready!")
            progress_bar.progress(100)
            time.sleep(0.5)
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            st.error(f"Connection error: {str(e)}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                st.error(f"Server response: {e.response.text}")
        except json.JSONDecodeError as e:
            st.error(f"Invalid response from server: {str(e)}")
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
        finally:
            # Clean up progress indicators
            status_text.empty()
            progress_bar.empty()
        return None
    
    def run(self):
        """Run the Streamlit application"""
        if not self.check_backend_health():
            st.stop()
        
        with st.form("presentation_form"):
            topic = st.text_input(
                "📝 Enter presentation topic",
                placeholder="e.g., Artificial Intelligence in Healthcare"
            )
            
            description = st.text_area(
                "📄 Additional description (optional)",
                placeholder="Add any specific points or focus areas you'd like to include"
            )
            
            submitted = st.form_submit_button("🚀 Generate Presentation")
            
            if submitted:
                if not topic:
                    st.error("⚠️ Please enter a topic")
                    return
                
                result = self.generate_presentation(topic, description)
                
                if result and result.get('success'):
                    UIHelper.show_presentation_details(result)

if __name__ == '__main__':
    app = PresentationApp()
    app.run()