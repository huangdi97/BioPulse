FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim
RUN adduser --disabled-password --gecos "" appuser
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY shared/ ./shared/
COPY cloud/ ./cloud/
EXPOSE 8000
USER appuser
CMD ["uvicorn", "cloud.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
