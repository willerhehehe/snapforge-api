FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir .

RUN playwright install --with-deps chromium

ENV PORT=8080
EXPOSE ${PORT}

CMD uvicorn snapforge.main:app --host 0.0.0.0 --port ${PORT}
