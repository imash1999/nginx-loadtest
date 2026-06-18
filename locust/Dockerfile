FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY locustfile.py .
CMD ["locust", "--host=http://nginx", "--headless", "-u", "50", "-r", "10", "--run-time", "60s", "-f", "locustfile.py"]
