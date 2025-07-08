#!/usr/bin/env python3
"""
Setup Script for Sentiment Monitoring Service

This script helps set up the sentiment monitoring service with guided configuration.
"""

import os
import sys
import yaml
import getpass
from pathlib import Path


def print_banner():
    """Print welcome banner."""
    print("=" * 60)
    print("  SENTIMENT MONITORING SERVICE SETUP")
    print("=" * 60)
    print()


def get_user_input(prompt: str, default: str = "", sensitive: bool = False) -> str:
    """Get user input with optional default and sensitive handling."""
    if sensitive:
        return getpass.getpass(f"{prompt}: ")
    else:
        if default:
            user_input = input(f"{prompt} [{default}]: ").strip()
            return user_input if user_input else default
        else:
            return input(f"{prompt}: ").strip()


def setup_twilio_config():
    """Set up Twilio configuration."""
    print("\n📱 TWILIO SMS CONFIGURATION")
    print("-" * 30)
    print("To enable SMS alerts, you need a Twilio account.")
    print("Sign up at: https://www.twilio.com/try-twilio")
    print()
    
    enable_twilio = input("Enable SMS alerts via Twilio? (y/n) [n]: ").strip().lower()
    
    if enable_twilio in ['y', 'yes']:
        account_sid = get_user_input("Twilio Account SID", sensitive=False)
        auth_token = get_user_input("Twilio Auth Token", sensitive=True)
        phone_number = get_user_input("Twilio Phone Number (e.g., +1234567890)")
        
        print("\nEnter phone numbers to receive alerts (one per line, press Enter twice when done):")
        alert_phones = []
        while True:
            phone = input("Phone number: ").strip()
            if not phone:
                break
            alert_phones.append(phone)
        
        return {
            'TWILIO_ACCOUNT_SID': account_sid,
            'TWILIO_AUTH_TOKEN': auth_token,
            'TWILIO_PHONE_NUMBER': phone_number,
            'ALERT_PHONE_NUMBERS': ','.join(alert_phones)
        }
    
    return {}


def setup_database_config():
    """Set up database configuration."""
    print("\n🗄️  DATABASE CONFIGURATION")
    print("-" * 30)
    print("Choose database option:")
    print("1. SQLite (simple, for testing)")
    print("2. PostgreSQL (recommended for production)")
    
    choice = input("Choice [1]: ").strip() or "1"
    
    if choice == "2":
        host = get_user_input("PostgreSQL Host", "localhost")
        port = get_user_input("PostgreSQL Port", "5432")
        database = get_user_input("Database Name", "sentiment_monitor")
        username = get_user_input("Username", "sentiment_user")
        password = get_user_input("Password", sensitive=True)
        
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"
    else:
        return "sqlite:///sentiment_monitor.db"


def setup_monitoring_config():
    """Set up monitoring configuration."""
    print("\n📊 MONITORING CONFIGURATION")
    print("-" * 30)
    
    # Check interval
    interval = get_user_input("Check interval in minutes", "60")
    
    # Sentiment thresholds
    print("\nSentiment alert thresholds (range: -1.0 to 1.0):")
    positive_threshold = get_user_input("Positive alert threshold", "0.7")
    negative_threshold = get_user_input("Negative alert threshold", "-0.7")
    
    # Alert cooldown
    cooldown = get_user_input("Alert cooldown in minutes", "120")
    
    # Tickers to monitor
    print("\nDefault tickers to monitor:")
    print("AAPL, GOOGL, MSFT, TSLA, AMZN, NVDA, META, NFLX")
    custom_tickers = input("Enter custom tickers (comma-separated) or press Enter for default: ").strip()
    
    if custom_tickers:
        tickers = [t.strip().upper() for t in custom_tickers.split(',')]
    else:
        tickers = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "NVDA", "META", "NFLX"]
    
    return {
        'interval': int(interval),
        'positive_threshold': float(positive_threshold),
        'negative_threshold': float(negative_threshold),
        'cooldown': int(cooldown),
        'tickers': tickers
    }


def setup_api_config():
    """Set up API configuration."""
    print("\n🌐 API CONFIGURATION")
    print("-" * 30)
    
    sentiment_url = get_user_input("Sentiment API URL", "http://localhost:80/api/sentiment")
    hedge_fund_url = get_user_input("Hedge Fund API URL", "http://localhost:80/api")
    timeout = get_user_input("API Timeout (seconds)", "30")
    
    return {
        'sentiment_url': sentiment_url,
        'hedge_fund_url': hedge_fund_url,
        'timeout': int(timeout)
    }


def create_config_file(config_data):
    """Create configuration file."""
    config = {
        'service': {
            'name': 'sentiment-monitor',
            'log_level': 'INFO',
            'environment': 'production',
            'check_interval_minutes': config_data['monitoring']['interval']
        },
        'api': config_data['api'],
        'alerts': {
            'cooldown_minutes': config_data['monitoring']['cooldown'],
            'sentiment_threshold_positive': config_data['monitoring']['positive_threshold'],
            'sentiment_threshold_negative': config_data['monitoring']['negative_threshold']
        },
        'monitoring': {
            'tickers': config_data['monitoring']['tickers']
        },
        'database': {
            'pool_size': 10,
            'max_overflow': 20
        },
        'redis': {
            'db': 0
        },
        'logging': {
            'format': '{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}',
            'rotation': '1 day',
            'retention': '30 days'
        }
    }
    
    # Write config file
    with open('config.yml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False, indent=2)
    
    print("✓ Configuration file created: config.yml")


def create_env_file(env_vars):
    """Create environment variables file."""
    if not env_vars:
        return
    
    env_content = "# Sentiment Monitor Environment Variables\n\n"
    
    # Database URL
    if 'database_url' in env_vars:
        env_content += f"DATABASE_URL={env_vars['database_url']}\n"
    
    # Redis URL
    env_content += "REDIS_URL=redis://localhost:6379/0\n\n"
    
    # Twilio settings
    if 'TWILIO_ACCOUNT_SID' in env_vars:
        env_content += f"TWILIO_ACCOUNT_SID={env_vars['TWILIO_ACCOUNT_SID']}\n"
        env_content += f"TWILIO_AUTH_TOKEN={env_vars['TWILIO_AUTH_TOKEN']}\n"
        env_content += f"TWILIO_PHONE_NUMBER={env_vars['TWILIO_PHONE_NUMBER']}\n"
        env_content += f"ALERT_PHONE_NUMBERS={env_vars['ALERT_PHONE_NUMBERS']}\n"
    
    # Write .env file
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✓ Environment file created: .env")


def install_dependencies():
    """Install Python dependencies."""
    print("\n📦 INSTALLING DEPENDENCIES")
    print("-" * 30)
    
    try:
        import subprocess
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Dependencies installed successfully")
        else:
            print(f"✗ Error installing dependencies: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Error installing dependencies: {e}")
        return False
    
    return True


def create_service_scripts():
    """Create service management scripts."""
    
    # Start script
    start_script = """#!/bin/bash
echo "Starting Sentiment Monitor Service..."
python cron_scheduler.py --mode schedule --interval 60
"""
    
    # Stop script (for systemd)
    systemd_service = """[Unit]
Description=Sentiment Monitor Service
After=network.target

[Service]
Type=simple
User=sentiment
WorkingDirectory=/opt/sentiment-monitor
ExecStart=/usr/bin/python3 cron_scheduler.py --mode schedule --interval 60
Restart=always
RestartSec=10
Environment=PYTHONPATH=/opt/sentiment-monitor

[Install]
WantedBy=multi-user.target
"""
    
    # Write scripts
    with open('start.sh', 'w') as f:
        f.write(start_script)
    
    with open('sentiment-monitor.service', 'w') as f:
        f.write(systemd_service)
    
    # Make start script executable
    os.chmod('start.sh', 0o755)
    
    print("✓ Service scripts created: start.sh, sentiment-monitor.service")


def main():
    """Main setup function."""
    print_banner()
    
    # Collect configuration
    twilio_config = setup_twilio_config()
    database_url = setup_database_config()
    monitoring_config = setup_monitoring_config()
    api_config = setup_api_config()
    
    # Create configuration files
    config_data = {
        'monitoring': monitoring_config,
        'api': api_config
    }
    
    create_config_file(config_data)
    
    # Create environment file
    env_vars = twilio_config.copy()
    env_vars['database_url'] = database_url
    create_env_file(env_vars)
    
    # Install dependencies
    if not install_dependencies():
        print("\n⚠️  Warning: Failed to install dependencies automatically")
        print("   Please run: pip install -r requirements.txt")
    
    # Create service scripts
    create_service_scripts()
    
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    print("✓ Logs directory created")
    
    # Final instructions
    print("\n🎉 SETUP COMPLETE!")
    print("=" * 30)
    print("\nNext steps:")
    print("1. Test the service: python cron_scheduler.py --mode test")
    print("2. Run a single check: python cron_scheduler.py --mode single")
    print("3. Start the scheduler: python cron_scheduler.py --mode schedule")
    print("4. Start the web API: python web_api.py")
    print("5. Or use Docker: docker-compose up -d")
    print("\nWeb interface will be available at: http://localhost:8000")
    print("\nFor production deployment, consider using the systemd service file.")


if __name__ == "__main__":
    main() 