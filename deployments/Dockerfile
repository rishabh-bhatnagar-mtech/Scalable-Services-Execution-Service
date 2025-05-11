FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y docker.io

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

EXPOSE 7000

CMD ["python", "main.py"]
