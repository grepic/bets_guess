FROM python:3.12-slim

WORKDIR /app

COPY apps/api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY packages/ /app/packages/
COPY apps/api/ /app/apps/api/

ENV PYTHONPATH=/app
ENV SMARTBETS_DATABASE_URL=postgresql+asyncpg://smartbets:smartbets@postgres:5432/smartbets
ENV SMARTBETS_REDIS_URL=redis://redis:6379/0

EXPOSE 8000

CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
