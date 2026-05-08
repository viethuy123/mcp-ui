FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY chainlit.md .
RUN mkdir -p /app/.chainlit
COPY config.toml /app/.chainlit/config.toml

EXPOSE 8080

CMD ["python", "-m", "chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "8080", "--headless"]