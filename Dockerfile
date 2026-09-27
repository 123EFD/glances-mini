# Lightweight Python 3.13 image
FROM python:3.13-slim

WORKDIR /app

# Install dependencies first for Docker caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY src/ src/

# Expose FastAPI port
EXPOSE 8001

# Start Uvicorn pointing to src directory
CMD ["uvicorn", "glances_mini.web.app:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8001"]