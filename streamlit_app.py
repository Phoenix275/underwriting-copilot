"""Streamlit wrapper — serves the self-contained Underwriting Copilot workbench.

The workbench is a Vite/React app built to a single HTML file (web/ →
dashboard/underwriting_copilot_mvp.html) with its data, fonts and styles
inlined. This wrapper only hosts it, which is why requirements.txt is
deliberately just Streamlit: nothing is modelled at runtime.

Tech Mahindra GLP Internship — Finance Project 1.
"""
import pathlib

import streamlit as st

st.set_page_config(page_title="Underwriting Copilot", page_icon="🛡️", layout="wide")

# strip Streamlit's chrome so the embedded app owns the page
st.markdown(
    """
    <style>
      #MainMenu, header, footer {visibility: hidden;}
      .block-container {padding: 0 !important; max-width: 100% !important;}
      .stAppViewBlockContainer {padding: 0 !important;}
      iframe {min-height: 96vh; border: 0;}
    </style>
    """,
    unsafe_allow_html=True,
)

HTML = pathlib.Path(__file__).parent / "dashboard" / "underwriting_copilot_mvp.html"

if not HTML.exists():
    st.error(
        "Workbench build not found at `dashboard/underwriting_copilot_mvp.html`.\n\n"
        "Build it with:\n\n"
        "```\n"
        "python src/run_pipeline.py && python src/webdata.py\n"
        "npm --prefix web ci && npm --prefix web run release\n"
        "```"
    )
    st.stop()

markup = HTML.read_text(encoding="utf-8")

# st.iframe replaced st.components.v1.html in Streamlit 1.56; keep the old path
# working so the app still runs on whatever version Community Cloud resolves.
if hasattr(st, "iframe"):
    st.iframe(markup, height=1000)
else:  # pragma: no cover - older Streamlit
    import streamlit.components.v1 as components

    components.html(markup, height=1000, scrolling=True)
