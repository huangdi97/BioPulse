FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY shared/ ./shared/
COPY sales_coach/ ./sales_coach/
EXPOSE 8001
CMD ["uvicorn", "sales_coach.app.main:app", "--host", "0.0.0.0", "--port", "8001"]
