FROM python:3.12-slim AS base

WORKDIR /app

COPY apps/api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY packages/ /app/packages/
COPY apps/api/ /app/apps/api/
COPY alembic/ /app/alembic/
COPY alembic.ini /app/alembic.ini

ENV PYTHONPATH=/app

EXPOSE 8000

# Development target (default)
FROM base AS dev
CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production target
FROM base AS prod
RUN pip install --no-cache-dir gunicorn
CMD ["gunicorn", "apps.api.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
