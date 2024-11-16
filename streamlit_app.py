# streamlit_app.py
import streamlit as st
import requests
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def generate_presentation(topic, description=""):
    """Make API call to Flask backend with progress tracking"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Preparing request
        status_text.write("🔄 Initializing presentation generation...")
        progress_bar.progress(10)
        time.sleep(1)  # Give user time to see status
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        payload = {
            'topic': topic,
            'description': description
        }
        
        # Step 2: Sending request
        status_text.write("🤖 Connecting to AI service...")
        progress_bar.progress(20)
        
        response = requests.post(
            'http://127.0.0.1:5000/create_presentation',
            headers=headers,
            data=json.dumps(payload),
            timeout=180  # 3 minutes timeout
        )
        
        # Step 3: Processing response
        progress_bar.progress(90)
        status_text.write("📊 Finalizing presentation...")
        
        if response.status_code != 200:
            error_data = response.json()
            error_message = error_data.get('error', 'Unknown error occurred')
            st.error(f"Server Error: {error_message}")
            status_text.empty()
            progress_bar.empty()
            return None
            
        # Step 4: Complete
        progress_bar.progress(100)
        status_text.write("✅ Presentation generated successfully!")
        time.sleep(1)
        status_text.empty()
        progress_bar.empty()
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {str(e)}")
        if hasattr(e.response, 'text'):
            st.error(f"Server response: {e.response.text}")
    except json.JSONDecodeError as e:
        st.error(f"Invalid response from server: {str(e)}")
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
    finally:
        status_text.empty()
        progress_bar.empty()
    return None

def main():
    """Streamlit UI"""
    st.set_page_config(
        page_title="AI Presentation Generator",
        page_icon="📊",
        layout="centered"
    )
    
    st.title("🎯 AI Presentation Generator")
    st.write("Generate professional presentations powered by GPT-4")
    
    # Add a status indicator for the backend service
    try:
        health_check = requests.get('http://127.0.0.1:5000/health')
        if health_check.status_code != 200:
            st.sidebar.error("❌ Backend service is not responding properly")
    except:
        st.sidebar.error("❌ Backend service is not running")
        st.error("Please ensure the Flask backend is running (python app.py)")
        st.stop()
    
    with st.form("presentation_form"):
        topic = st.text_input("📝 Enter presentation topic", 
                            placeholder="e.g., Artificial Intelligence in Healthcare")
        description = st.text_area("📄 Additional description (optional)", 
                                 placeholder="Add any specific points or focus areas you'd like to include")
        submitted = st.form_submit_button("🚀 Generate Presentation")
        
        if submitted:
            if not topic:
                st.error("⚠️ Please enter a topic")
                return
            
            result = generate_presentation(topic, description)
            
            if result and result.get('success'):
                st.success("✅ Presentation created successfully!")
                st.markdown(f"🔗 [View Presentation]({result['presentation_url']})")
                
                with st.expander("📊 Presentation Details"):
                    st.write(f"Presentation ID: {result['presentation_id']}")
                    st.write(f"Direct link: {result['presentation_url']}")
                    st.write("You can now open the presentation in Google Slides")

if __name__ == '__main__':
    main()