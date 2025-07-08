FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    cron \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create logs directory
RUN mkdir -p logs

# Make scripts executable
RUN chmod +x *.py

# Create cron file for hourly sentiment checks
RUN echo "0 * * * * cd /app && python run_single_check.py >> logs/cron.log 2>&1" > /etc/cron.d/sentiment-monitor

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/sentiment-monitor

# Apply cron job
RUN crontab /etc/cron.d/sentiment-monitor

# Create the log file to be able to run tail
RUN touch /var/log/cron.log

# Health check
HEALTHCHECK --interval=5m --timeout=30s --start-period=1m --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=10)" || exit 1

# Default command runs the web API and cron
CMD ["sh", "-c", "cron && python web_api.py"] 