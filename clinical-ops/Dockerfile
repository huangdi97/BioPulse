FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY shared/ ./shared/
COPY clinical_ops/ ./clinical_ops/
EXPOSE 8010
CMD ["uvicorn", "clinical_ops.app.main:app", "--host", "0.0.0.0", "--port", "8010"]
