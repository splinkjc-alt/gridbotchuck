# GridBot Chuck - Crypto Grid Trading Bot
# Free paper trading | Paid live trading bots available

FROM python:3.13-slim

LABEL maintainer="splinkjc-alt"
LABEL description="Grid trading bot for crypto with RSI, Bollinger Bands, and multi-timeframe analysis"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for data persistence
RUN mkdir -p /app/logs /app/data

# Environment variables (override with docker run -e or .env file)
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO

# Expose API port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/api/bot/status || exit 1

# Default command - paper trading mode
CMD ["python", "main.py", "--config", "config/config.json"]
