FROM python:3.12-slim
WORKDIR /app
COPY patient-engage/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY shared/ ./shared/
COPY patient-engage/ ./patient-engage/
EXPOSE 8011
CMD ["uvicorn", "patient-engage.app.main:app", "--host", "0.0.0.0", "--port", "8011"]

RUN adduser --disabled-password --gecos "" appuser
USER appuser
