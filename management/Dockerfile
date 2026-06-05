FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY shared/ ./shared/
COPY management/ ./management/
EXPOSE 8012
CMD ["uvicorn", "management.app.main:app", "--host", "0.0.0.0", "--port", "8012"]
