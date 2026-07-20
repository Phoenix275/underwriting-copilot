"""Streamlit wrapper — serves the self-contained Underwriting Copilot dashboard.

The dashboard is a single self-contained HTML file (built by src/dashboard.py).
This wrapper only embeds it full-screen for hosting on Streamlit Community
Cloud — it does no modelling at runtime, which is why requirements.txt is
deliberately minimal. Tech Mahindra GLP Internship — Finance Project 1.
"""
import pathlib

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Underwriting Copilot", page_icon="🛡️", layout="wide")

# strip Streamlit chrome so the embedded app fills the page
st.markdown(
    """
    <style>
      #MainMenu, header, footer {visibility: hidden;}
      .block-container {padding: 0 !important; max-width: 100% !important;}
      .stAppViewBlockContainer {padding: 0 !important;}
      iframe {min-height: 96vh;}
    </style>
    """,
    unsafe_allow_html=True,
)

HTML = pathlib.Path(__file__).parent / "dashboard" / "underwriting_copilot_mvp.html"

if not HTML.exists():
    st.error(
        "Dashboard build not found at `dashboard/underwriting_copilot_mvp.html`.\n\n"
        "Rebuild it with `python src/run_pipeline.py && python src/dashboard.py`, "
        "then copy `output/underwriting_copilot_mvp.html` into `dashboard/`."
    )
    st.stop()

components.html(HTML.read_text(encoding="utf-8"), height=1000, scrolling=True)
