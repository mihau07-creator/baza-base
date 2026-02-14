FROM python:3.9-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# Hugging Face Spaces expects port 7860
EXPOSE 7860

HEALTHCHECK CMD curl --fail http://localhost:7860/_stcore/health

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0"]
