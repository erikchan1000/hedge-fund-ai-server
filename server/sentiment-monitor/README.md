# Sentiment Monitoring Service

A comprehensive service that monitors sentiment data from your hedge fund API and sends real-time SMS alerts when significant sentiment changes are detected.

## 🚀 Features

- **Hourly Sentiment Monitoring**: Automatically checks sentiment data every hour
- **SMS Alerts**: Sends phone notifications via Twilio for significant sentiment changes
- **Database Storage**: Stores historical sentiment data and alert history
- **Web Dashboard**: REST API for monitoring service status and viewing data
- **Flexible Deployment**: Supports Docker, systemd, and standalone Python execution
- **Configurable Thresholds**: Customizable sentiment alert thresholds and cooldown periods
- **Multi-Ticker Support**: Monitor multiple stock tickers simultaneously

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL or SQLite (for data storage)
- Redis (for alert cooldowns, optional)
- Twilio Account (for SMS alerts, optional)
- Access to your hedge fund sentiment API

## 🛠️ Quick Setup

### Option 1: Interactive Setup (Recommended)

```bash
cd sentiment-monitor
python setup.py
```

This will guide you through:
- Twilio SMS configuration
- Database setup
- API endpoints
- Monitoring configuration
- Dependency installation

### Option 2: Manual Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**
   ```bash
   cp config.yml.example config.yml
   # Edit config.yml with your settings
   
   # Create .env file for sensitive data
   echo "TWILIO_ACCOUNT_SID=your_sid" > .env
   echo "TWILIO_AUTH_TOKEN=your_token" >> .env
   echo "TWILIO_PHONE_NUMBER=+1234567890" >> .env
   echo "ALERT_PHONE_NUMBERS=+1234567890,+1987654321" >> .env
   echo "DATABASE_URL=sqlite:///sentiment_monitor.db" >> .env
   ```

3. **Test the Service**
   ```bash
   python cron_scheduler.py --mode test
   ```

## 🏃‍♂️ Running the Service

### Python Scheduler (Development)
```bash
# Run with Python's built-in scheduler
python cron_scheduler.py --mode schedule --interval 60

# Run single check
python cron_scheduler.py --mode single

# Test connections
python cron_scheduler.py --mode test
```

### Docker (Production)
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f sentiment-monitor

# Stop services
docker-compose down
```

### System Cron (Linux/Mac)
```bash
# Generate crontab entry
python cron_scheduler.py --mode crontab

# Add to your crontab
crontab -e
# Add the generated line
```

### Systemd Service (Linux)
```bash
# Copy service file
sudo cp sentiment-monitor.service /etc/systemd/system/

# Enable and start
sudo systemctl enable sentiment-monitor
sudo systemctl start sentiment-monitor

# Check status
sudo systemctl status sentiment-monitor
```

## 🌐 Web API

The service includes a REST API for monitoring and control:

### Start Web API
```bash
python web_api.py
```

### API Endpoints

- **Service Status**: `GET /status`
- **Recent Alerts**: `GET /alerts/recent?hours=24`
- **Sentiment History**: `GET /sentiment/{ticker}?hours=24`
- **All Sentiment Data**: `GET /sentiment/all?hours=24`
- **Manual Trigger**: `POST /trigger/check`
- **Ticker-Specific Check**: `POST /trigger/check/{ticker}`
- **Configuration**: `GET /config`
- **Recent Logs**: `GET /logs/recent?lines=100`

### Example Usage
```bash
# Check service status
curl http://localhost:8000/status

# Get recent alerts
curl http://localhost:8000/alerts/recent

# Trigger manual check
curl -X POST http://localhost:8000/trigger/check

# Get AAPL sentiment history
curl http://localhost:8000/sentiment/AAPL?hours=24
```

## ⚙️ Configuration

### Main Configuration (`config.yml`)

```yaml
service:
  name: "sentiment-monitor"
  log_level: "INFO"
  check_interval_minutes: 60

api:
  sentiment_url: "http://localhost:80/api/sentiment"
  hedge_fund_url: "http://localhost:80/api"
  timeout: 30

alerts:
  cooldown_minutes: 120
  sentiment_threshold_positive: 0.7
  sentiment_threshold_negative: -0.7

monitoring:
  tickers:
    - "AAPL"
    - "GOOGL"
    - "MSFT"
    # Add more tickers...
```

### Environment Variables (`.env`)

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/sentiment_monitor
REDIS_URL=redis://localhost:6379/0

# Twilio SMS
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
ALERT_PHONE_NUMBERS=+1234567890,+1987654321
```

## 📊 Database Schema

The service creates two main tables:

### Sentiment Records
- Stores historical sentiment data for each ticker
- Includes sentiment score, confidence, timestamp
- Enables historical analysis and trending

### Alert Records
- Tracks all sent alerts
- Records success/failure status
- Prevents duplicate alerts via cooldown system

## 📱 SMS Alerts

When sentiment crosses your configured thresholds, you'll receive SMS alerts like:

```
🚀 STRONG POSITIVE sentiment detected for $AAPL!
Score: 0.850
Confidence: 87.3%
Time: 2025-01-07 14:30:15
```

### Alert Features
- **Cooldown System**: Prevents spam (default: 2 hours)
- **Multi-Recipient**: Send to multiple phone numbers
- **Threshold-Based**: Only alerts on significant sentiment changes
- **Rich Messages**: Includes score, confidence, and timing

## 🐳 Docker Deployment

The service includes a complete Docker setup:

```bash
# Development
docker-compose up

# Production with nginx
docker-compose --profile production up -d

# Scale if needed
docker-compose up --scale sentiment-monitor=2
```

### Docker Services
- **sentiment-monitor**: Main application with cron
- **postgres**: Database storage
- **redis**: Caching and cooldowns
- **nginx**: Reverse proxy (production profile)

## 🔧 Maintenance

### Viewing Logs
```bash
# Service logs
tail -f logs/sentiment_monitor_$(date +%Y-%m-%d).log

# Cron logs
tail -f logs/cron_$(date +%Y-%m-%d).log

# Docker logs
docker-compose logs -f sentiment-monitor
```

### Database Maintenance
```bash
# Connect to database
psql $DATABASE_URL

# Cleanup old records (older than 30 days)
DELETE FROM sentiment_records WHERE timestamp < NOW() - INTERVAL '30 days';
DELETE FROM alert_records WHERE sent_at < NOW() - INTERVAL '30 days';
```

### Health Checks
```bash
# Test service connectivity
python cron_scheduler.py --mode test

# Check web API health
curl http://localhost:8000/health

# Manual sentiment check
python cron_scheduler.py --mode single
```

## 🚨 Troubleshooting

### Common Issues

**1. "No sentiment data" errors**
- Check API URL configuration in `config.yml`
- Verify hedge fund API is running and accessible
- Test with: `curl http://localhost:80/api/sentiment/AAPL`

**2. SMS alerts not sending**
- Verify Twilio credentials in `.env`
- Check phone number format (+1234567890)
- Ensure Twilio account has sufficient balance

**3. Database connection errors**
- Check `DATABASE_URL` in environment variables
- Ensure PostgreSQL is running
- Test connection: `psql $DATABASE_URL`

**4. Permission errors**
- Make scripts executable: `chmod +x *.py`
- Check file permissions in logs directory
- Ensure user has write access

### Debug Mode
```bash
# Run with debug logging
python cron_scheduler.py --mode test --config config.yml

# Check service status
python -c "
from sentiment_service import SentimentMonitorService
service = SentimentMonitorService()
print('Service initialized successfully')
"
```

## 📈 Monitoring & Analytics

### Key Metrics to Monitor
- **Alert Frequency**: How often alerts are triggered
- **Sentiment Trends**: Historical sentiment patterns
- **Service Uptime**: Monitoring cycles completion rate
- **API Response Times**: Hedge fund API performance

### Performance Optimization
- **Database Indexing**: Ensure indexes on ticker and timestamp
- **Redis Caching**: Use Redis for alert cooldowns
- **Async Processing**: Concurrent ticker monitoring
- **Log Rotation**: Regular log cleanup

## 🔒 Security Considerations

- **Environment Variables**: Store sensitive data in `.env`, not config files
- **Database Access**: Use dedicated user with minimal permissions
- **API Keys**: Rotate Twilio credentials regularly
- **Network Security**: Use HTTPS for API endpoints
- **Log Sanitization**: Avoid logging sensitive information

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 📞 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review logs for error messages
3. Test individual components
4. Create an issue with detailed information

---

**Happy Monitoring! 📊📱** 