FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Railway/Render inject PORT at runtime; default to 8000 for local `docker run`.
ENV PORT=8000
EXPOSE 8000

# `alembic upgrade head` first so a fresh deploy always has the current
# schema (Phase 3.5), then start the API.
CMD alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port ${PORT}
