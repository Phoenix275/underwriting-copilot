# Underwriting Copilot — production POC image
# Build:  docker build -t underwriting-copilot .
# Dashboard:  docker run -p 8501:8501 underwriting-copilot
# REST API:   docker run -p 8000:8000 underwriting-copilot \
#               uvicorn api:app --app-dir src --host 0.0.0.0
FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt requirements-pipeline.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-pipeline.txt

COPY src/ src/
COPY data/external/ data/external/
COPY dashboard/ dashboard/
COPY streamlit_app.py .

# bake a fresh pipeline run (models.joblib, portfolio, evaluation report)
# into the image so both the dashboard and the API start instantly
RUN python src/run_pipeline.py && python src/dashboard.py \
    && cp output/underwriting_copilot_mvp.html dashboard/underwriting_copilot_mvp.html

EXPOSE 8501 8000
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
