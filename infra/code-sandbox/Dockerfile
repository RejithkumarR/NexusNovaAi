FROM python:3.12-slim

RUN useradd --create-home --uid 10001 nova
WORKDIR /workspace
USER nova

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

ENTRYPOINT ["python"]
