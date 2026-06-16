FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY shared/ ./shared/
COPY sales-assistant/ ./sales-assistant/
EXPOSE 8004
CMD ["uvicorn", "sales_assistant.app.main:app", "--host", "0.0.0.0", "--port", "8004"]

RUN adduser --disabled-password --gecos "" appuser
USER appuser
