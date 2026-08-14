FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       poppler-utils tesseract-ocr tesseract-ocr-por \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY pipeline /workspace/benchmark/pipeline
COPY cases /workspace/benchmark/cases
RUN touch /workspace/benchmark/__init__.py

ENV PYTHONPATH=/workspace PYTHONUNBUFFERED=1
