FROM python:3.12-slim
WORKDIR /app
COPY market-access/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY shared/ ./shared/
COPY market-access/ ./market-access/
EXPOSE 8007
CMD ["uvicorn", "market-access.app.main:app", "--host", "0.0.0.0", "--port", "8007"]
