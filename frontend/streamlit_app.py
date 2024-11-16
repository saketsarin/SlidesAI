import streamlit as st
import streamlit.components.v1 as components
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
        # Initialize session state
        if 'presentation_ready' not in st.session_state:
            st.session_state.presentation_ready = False
            st.set_page_config(
                page_title="Slides AI",
                page_icon="../Logo_small.png",
                layout="centered"
            )
        elif st.session_state.presentation_ready:
            st.set_page_config(
                page_title="Slides AI",
                page_icon="../Logo_small.png",
                layout="wide"
            )
    
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
    
    def embed_presentation(self, presentation_id):
        """Embed Google Slides presentation"""
        embed_html = f"""
        <iframe
            src="https://docs.google.com/presentation/d/{presentation_id}/embed?start=false&loop=false&delayms=3000"
            frameborder="0"
            width="100%"
            height="350"
            allowfullscreen="true"
            mozallowfullscreen="true"
            webkitallowfullscreen="true">
        </iframe>
        """
        components.html(embed_html, height=370)
    
    def generate_presentation(self, topic, description=""):
        """Generate presentation with dynamic layout"""
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
            
            # Show initial progress
            for message, progress in steps[:2]:
                status_text.write(message)
                progress_bar.progress(progress)
                time.sleep(0.3)
            
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
            
            result = response.json()
            
            # Update session state and trigger rerun
            st.session_state.presentation_ready = True
            st.session_state.presentation_id = result['presentation_id']
            st.session_state.presentation_url = result['presentation_url']
            st.rerun()
            
            return result
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
        finally:
            status_text.empty()
            progress_bar.empty()
        return None
    
    def run(self):
        """Run the Streamlit application"""
        if not self.check_backend_health():
            st.stop()
        
        st.title("🎯 Slides AI")
        st.write("Generate professional presentations in under a minute!")
        
        # If presentation is ready, use wide layout with columns
        if st.session_state.presentation_ready:
            col1, col2 = st.columns([1, 2])
            
            with col1:
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
            
            # Show current presentation in right column
            with col2:
                if 'presentation_id' in st.session_state:
                    self.embed_presentation(st.session_state.presentation_id)
                    st.success("✅ Presentation created successfully!")
                    st.markdown(f"🔗 [Edit Presentation]({st.session_state.presentation_url})")
        
        else:
            # Use centered layout for initial form
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
                    
                    self.generate_presentation(topic, description)

if __name__ == '__main__':
    app = PresentationApp()
    app.run()