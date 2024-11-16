import streamlit as st

class UIHelper:
    @staticmethod
    def show_progress(message, progress):
        """Show progress in a single line"""
        return st.empty(), st.progress(progress)
    
    @staticmethod
    def show_presentation_details(result):
        """Show presentation details in expandable section"""
        st.success("✅ Presentation created successfully!")
        st.markdown(f"🔗 [View Presentation]({result['presentation_url']})")
        
        with st.expander("📊 Presentation Details"):
            st.write(f"Presentation ID: {result['presentation_id']}")
            st.write(f"Direct link: {result['presentation_url']}")
            st.write("You can now open the presentation in Google Slides")