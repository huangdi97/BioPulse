FROM python:3.12-slim
WORKDIR /app
COPY clinical-ops/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY shared/ ./shared/
COPY clinical-ops/ ./clinical-ops/
EXPOSE 8010
CMD ["uvicorn", "clinical-ops.app.main:app", "--host", "0.0.0.0", "--port", "8010"]
