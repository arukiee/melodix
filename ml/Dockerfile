FROM python:3.12-slim

WORKDIR /app
COPY ml/requirements.txt /app/ml/requirements.txt
RUN pip install --no-cache-dir -r /app/ml/requirements.txt
COPY ml /app/ml

EXPOSE 8100
CMD ["uvicorn", "ml.inference.app:app", "--host", "0.0.0.0", "--port", "8100"]
