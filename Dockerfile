FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements-backend.txt .
RUN pip install --upgrade pip && pip install -r requirements-backend.txt

COPY server.py .

EXPOSE 7000
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7000"]
