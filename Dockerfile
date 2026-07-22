# Underwriting Copilot — REST API image (optional live backend)
#
# The workbench frontend is a static, self-contained single-file app deployed to
# Cloudflare Pages (see README). It needs no server. This image serves only the
# OPTIONAL FastAPI backend that records the underwriter decision audit trail;
# without it, the app runs standalone and keeps decisions in the browser.
#
# Build:  docker build -t underwriting-copilot-api .
# Run:    docker run -p 8000:8000 underwriting-copilot-api
FROM python:3.13-slim

WORKDIR /app
COPY requirements-pipeline.txt ./
RUN pip install --no-cache-dir -r requirements-pipeline.txt

COPY src/ src/
COPY data/external/ data/external/

# bake a pipeline run (models.joblib, portfolio, evaluation report) into the
# image so the API starts instantly
RUN python src/run_pipeline.py

EXPOSE 8000
CMD ["uvicorn", "api:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]
