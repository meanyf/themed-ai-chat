FROM python:3.12-slim

WORKDIR /srv/chat
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY pyproject.toml .
COPY app/ app/
RUN pip install --no-cache-dir .

COPY alembic.ini .
COPY migrations/ migrations/
COPY frontend/ frontend/

USER 65532:65532
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"]
