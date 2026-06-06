FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY shared/ ./shared/
COPY market_access/ ./market_access/
EXPOSE 8007
CMD ["uvicorn", "market_access.app.main:app", "--host", "0.0.0.0", "--port", "8007"]
