FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Persist subscriber data
VOLUME ["/app/subscribers.json", "/app/bot.log"]

CMD ["python", "bot.py"]
