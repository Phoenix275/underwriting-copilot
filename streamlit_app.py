"""Streamlit wrapper — serves the self-contained Underwriting Copilot dashboard.

The dashboard is a single self-contained HTML file (built by src/dashboard.py).
This wrapper just embeds it full-screen so it can be hosted on Streamlit
Community Cloud. Tech Mahindra GLP Internship — Finance Project 1.
"""
import pathlib

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Underwriting Copilot", page_icon="🛡️", layout="wide")

# strip Streamlit chrome so the app fills the page
st.markdown(
    """
    <style>
      #MainMenu, header, footer {visibility: hidden;}
      .block-container {padding: 0 !important; max-width: 100% !important;}
      iframe {min-height: 96vh;}
    </style>
    """,
    unsafe_allow_html=True,
)

HTML = pathlib.Path(__file__).parent / "dashboard" / "underwriting_copilot_mvp.html"
components.html(HTML.read_text(encoding="utf-8"), height=1000, scrolling=True)
