FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements*.txt /app/backend/
RUN pip install --no-cache-dir -r backend/requirements.lock.txt
COPY backend /app/backend
COPY frontend/public/samples /app/frontend/public/samples
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
