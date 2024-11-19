import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import time
from config import Config
from utils.ui_helpers import UIHelper
from utils.theme_previews import ThemePreviewer

class PresentationApp:
    def __init__(self):
        self.api_url = 'http://127.0.0.1:5000'
        self.setup_page()
    
    def setup_page(self):
        """Configure Streamlit page settings"""
        # Initialize session state
        if 'presentation_ready' not in st.session_state:
            st.session_state.presentation_ready = False
            st.session_state.selected_theme = None
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
    
    def display_theme_previews(self):
        """Display clickable theme previews"""
        st.subheader("Select a Theme")
        
        # Create columns for theme previews
        cols = st.columns(3)
        
        for idx, (theme_id, theme) in enumerate(Config.PRESENTATION_THEMES.items()):
            with cols[idx % 3]:
                # Create container for preview and selection indicator
                preview_container = st.container()
                
                # Generate theme preview
                preview_html = ThemePreviewer.generate_theme_preview(theme)
                
                # Add click handler using HTML
                clickable_preview = f"""
                <div onclick="parent.postMessage({{theme: '{theme_id}'}}, '*')" style="cursor: pointer; position: relative;">
                    {preview_html}
                    <div style="position: absolute; top: 5px; right: 5px; padding: 5px; background: {'#4CAF50' if st.session_state.selected_theme == theme_id else 'transparent'}; border-radius: 50%;">
                        {'✓' if st.session_state.selected_theme == theme_id else ''}
                    </div>
                </div>
                """
                
                # Display clickable preview
                components.html(clickable_preview, height=150)
                st.caption(theme['name'])
                
                # Handle click events
                if preview_container.button("Select", key=f"theme_{theme_id}", use_container_width=True):
                    st.session_state.selected_theme = theme_id
                    st.rerun()
    
    def generate_presentation(self, topic, description=""):
        """Generate presentation with dynamic layout"""
        if not st.session_state.selected_theme:
            st.error("⚠️ Please select a theme first")
            return None
            
        steps = [
            ("🔄 Initializing...", 10),
            ("🤖 Connecting to AI service...", 20),
            ("📝 Generating content...", 40),
            ("🎨 Creating diagrams...", 60),
            ("📊 Building presentation...", 80),
            ("✅ Finalizing...", 90),
        ]
        
        status_text = st.empty()
        progress_bar = st.progress(0)
        
        try:
            headers = {'Content-Type': 'application/json'}
            payload = {
                'topic': topic,
                'description': description,
                'theme': st.session_state.selected_theme
            }
            
            # Use a separate thread for the request to allow progress updates
            import threading

            def make_request():
                nonlocal response
                response = requests.post(
                    f'{self.api_url}/create_presentation',
                    headers=headers,
                    data=json.dumps(payload),
                    timeout=10000
                )

            response = None
            request_thread = threading.Thread(target=make_request)
            request_thread.start()

            # Update progress bar while the request is being made
            for message, progress in steps:
                if request_thread.is_alive():
                    status_text.write(message)
                    progress_bar.progress(progress)
                    time.sleep(10)
                else:
                    break

            request_thread.join()

            if response is None or response.status_code != 200:
                error_message = response.json().get('error', 'Unknown error occurred') if response else 'No response from server'
                st.error(f"Server Error: {error_message}")
                return None
            
            result = response.json()

            # Show completion
            status_text.write("✨ Presentation ready!")
            progress_bar.progress(100)
            time.sleep(0.5)

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

        # Display theme previews with selection functionality
        self.display_theme_previews()
        
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
                        
                        self.generate_presentation(topic, description)
            
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