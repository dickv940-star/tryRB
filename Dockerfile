FROM python:3.11-slim

WORKDIR /rembg

RUN pip install --upgrade pip && \
    pip install poetry poetry-dynamic-versioning

RUN apt-get update && apt-get install -y curl git && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY . .

RUN poetry config virtualenvs.create false && \
    poetry install --extras "cpu cli" --without dev

# Model weights are downloaded on first use and persisted in the named volume.
EXPOSE 7000
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7000"]
