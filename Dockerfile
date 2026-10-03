FROM python:3.11-slim

# Install system dependencies: Graphviz, Tesseract OCR (with Arabic & English), Poppler, ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    graphviz \
    tesseract-ocr \
    tesseract-ocr-ara \
    tesseract-ocr-eng \
    poppler-utils \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose standard Streamlit port
EXPOSE 8501

# Default command for web service (overridden by worker or cron in render.yaml)
CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0", "--server.fileWatcherType", "none", "--client.toolbarMode", "minimal"]
