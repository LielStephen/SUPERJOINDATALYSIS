FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8501 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download en_core_web_sm || true

COPY . .

EXPOSE 8000 8501 10000

HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=3 \
    CMD curl --fail http://localhost:${PORT}/health || curl --fail http://localhost:${PORT}/healthz || exit 1

CMD ["sh", "-c", "if [ \"$RUN_STREAMLIT\" = \"true\" ]; then streamlit run app.py --server.port=${PORT:-8501} --server.address=0.0.0.0 --server.headless=true; else uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}; fi"]

