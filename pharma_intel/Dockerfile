FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY shared/ ./shared/
COPY pharma_intel/ ./pharma_intel/
EXPOSE 8006
CMD ["uvicorn", "pharma_intel.app.main:app", "--host", "0.0.0.0", "--port", "8006"]

RUN adduser --disabled-password --gecos "" appuser
USER appuser
