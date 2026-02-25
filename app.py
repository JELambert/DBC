import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="Drunk Book Club",
    page_icon="🍷",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load custom CSS
css_path = Path(__file__).parent / "assets" / "custom.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

# Sidebar branding
with st.sidebar:
    st.markdown(
        """
        <div style="text-align: center; padding: 1rem 0;">
            <div style="font-size: 3rem;">🍷📚</div>
            <h2 style="color: #C9A96E; font-family: Georgia, serif; margin: 0.5rem 0 0 0;">
                Drunk Book Club
            </h2>
            <p style="color: #A0A0B0; font-size: 0.85rem;">Est. October 2023</p>
        </div>
        <hr style="border-color: rgba(114, 47, 55, 0.3);">
        """,
        unsafe_allow_html=True,
    )

# Landing page content
st.markdown(
    """
    <div style="text-align: center; padding: 3rem 0;">
        <div style="font-size: 5rem;">🍷📚</div>
        <h1 style="font-family: Georgia, serif; color: #C9A96E; font-size: 2.5rem;">
            Welcome to the Drunk Book Club Dashboard
        </h1>
        <p style="color: #A0A0B0; font-size: 1.1rem; max-width: 600px; margin: 1rem auto;">
            23 books. 7 readers. Countless glasses of wine.<br>
            Navigate using the sidebar to explore our reading journey.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)
