# 📈 Stock Alert System

> A powerful Django REST API that monitors stock prices and sends real-time alerts when your conditions are met.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-4.2+-green.svg)](https://djangoproject.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12+-blue.svg)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![AWS](https://img.shields.io/badge/AWS-Deployable-orange.svg)](https://aws.amazon.com)

## 🚀 What This Does

I built this system to solve a real problem - staying on top of stock price movements without constantly checking charts. The application monitors 10 major tech stocks and sends you email alerts based on your custom criteria.

### Key Features I Implemented:

- **Real-time Stock Monitoring**: Tracks AAPL, GOOGL, MSFT, TSLA, AMZN, META, NFLX, NVDA, AMD, INTC
- **Smart Alert System**: Two types of alerts - threshold (price crosses a value) and duration (price condition persists)
- **Email Notifications**: Instant alerts sent to your email when conditions are met
- **User Management**: Complete authentication system with JWT tokens
- **REST API**: Full CRUD operations for managing your alerts
- **Background Tasks**: Uses Celery to handle price updates and alert processing
- **Comprehensive Testing**: Built with pytest for reliability

## 🛠️ Tech Stack

I chose this stack for performance, scalability, and ease of deployment:

- **Backend**: Django 4.2+ with Django REST Framework
- **Database**: PostgreSQL (production) / SQLite (development)  
- **Task Queue**: Celery with Redis broker
- **Authentication**: JWT (JSON Web Tokens)
- **Email**: SMTP integration (Gmail compatible)
- **Testing**: Pytest with coverage reporting
- **Deployment**: Docker + AWS EC2 Free Tier
- **API Documentation**: Django REST Framework browsable API

## 📋 Prerequisites

Make sure you have these installed:

```bash
Python 3.8+
PostgreSQL 12+ (or SQLite for development)
Redis Server
Git
Docker & Docker Compose (for containerized deployment)
```

## 🔧 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/yousefalimansour/System-alert.git
cd System-alert
```

### 2. Set Up Virtual Environment
```bash
python -m venv venv

# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your settings:
SECRET_KEY=your_secret_key_here
DEBUG=True
DATABASE_URL=postgresql://user:password@localhost:5432/stockalert
REDIS_URL=redis://localhost:6379/0

# Email configuration
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# Get your free API key from Twelve Data
TWELVE_DATA_API_KEY=your_free_api_key
```

### 5. Database Setup
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

# Load the predefined stocks
python manage.py loaddata fixtures/stocks.json
```

### 6. Start the Services

You'll need 4 terminal windows:

```bash
# Terminal 1: Django server
python manage.py runserver

# Terminal 2: Redis server
redis-server

# Terminal 3: Celery worker
celery -A config worker -l info

# Terminal 4: Celery beat scheduler
celery -A config beat -l info
```

🎉 **You're ready!** Visit `http://localhost:8000/api/` to explore the API.

## 🐳 Docker Deployment (Recommended)

I've configured Docker for easy deployment:

```bash
# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f
```

## 🔗 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register/` | Create new account |
| POST | `/api/auth/login/` | Login and get tokens |
| POST | `/api/auth/logout/` | Logout |
| POST | `/api/auth/token/refresh/` | Refresh access token |
| GET/PUT | `/api/auth/profile/` | View/update profile |

### Stocks
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stocks/` | List all available stocks |
| GET | `/api/stocks/{id}/` | Get specific stock details |

### Alerts
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stocks/alerts/` | List your alerts |
| POST | `/api/stocks/alerts/` | Create new alert |
| GET | `/api/stocks/alerts/{id}/` | Get alert details |
| PUT/PATCH | `/api/stocks/alerts/{id}/` | Update alert |
| DELETE | `/api/stocks/alerts/{id}/` | Delete alert |
| GET | `/api/stocks/alerts/history/` | View triggered alerts |

## 📱 Usage Examples

### Register a New User
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "trader_joe",
    "email": "joe@example.com", 
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "first_name": "Joe",
    "last_name": "Trader"
  }'
```

### Create a Price Alert
```bash
curl -X POST http://localhost:8000/api/stocks/alerts/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "stock": 1,
    "alert_type": "threshold",
    "condition": "above", 
    "target_price": "175.00",
    "recurring": false
  }'
```

### Create a Duration Alert
```bash
curl -X POST http://localhost:8000/api/stocks/alerts/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "stock": 2,
    "alert_type": "duration",
    "condition": "below",
    "target_price": "2400.00", 
    "duration_minutes": 60
  }'
```

## 📊 Monitored Stocks

I've preconfigured these 10 major tech stocks:

- **AAPL** - Apple Inc.
- **GOOGL** - Alphabet Inc.
- **MSFT** - Microsoft Corporation  
- **TSLA** - Tesla Inc.
- **AMZN** - Amazon.com Inc.
- **META** - Meta Platforms Inc.
- **NFLX** - Netflix Inc.
- **NVDA** - NVIDIA Corporation
- **AMD** - Advanced Micro Devices Inc.
- **INTC** - Intel Corporation

## 🧪 Running Tests

I've written comprehensive tests to ensure reliability:

```bash
# Run all tests
pytest

# Run specific test files
pytest tests/test_authentication.py
pytest tests/test_alerts.py

# Run with coverage report
pytest --cov=. --cov-report=html
```

Test coverage includes:
- User authentication and authorization
- Alert creation and management
- Email notification system
- API endpoint validation
- Background task processing

## 🚀 AWS Deployment

I've included complete deployment instructions for AWS EC2 Free Tier:

1. **EC2 Setup**: Launch t2.micro instance with Ubuntu 22.04
2. **Docker Deployment**: Use the provided docker-compose.yml
3. **Production Configuration**: Environment variables and security settings
4. **SSL Setup**: Optional HTTPS configuration
5. **Monitoring**: Health checks and logging

See the [deployment guide](deployment-guide.md) for detailed steps.

## 📁 Project Structure

```
STOCK-ALERT-SYSTEM/
├── config/                 # Django project settings
├── users/                  # User authentication app
├── stocks/                 # Stock monitoring and alerts app
│   ├── management/
│   │   └── commands/
│   │       └── fetch_stock_prices.py
│   ├── models.py          # Database models
│   ├── serializers.py     # API serializers
│   ├── views.py           # API views
│   ├── tasks.py           # Celery tasks
│   └── services.py        # Business logic
├── tests/                  # Test suite
├── fixtures/               # Sample data
├── docker-compose.yml      # Container orchestration
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## ⚙️ Configuration Details

### Email Settings
I've configured the system to work with Gmail SMTP. You'll need to:
1. Enable 2-factor authentication on your Gmail account
2. Generate an app-specific password
3. Use that password in your `.env` file

### Stock Price Updates
- **Frequency**: Every 5 minutes during market hours
- **API**: Uses Twelve Data free tier (800 requests/day)
- **Fallback**: Financial Modeling Prep API as backup

### Alert Processing
- **Check Interval**: Every minute
- **Email Delivery**: Immediate via SMTP
- **History Tracking**: All triggered alerts are logged

## 🔒 Security Features

I've implemented several security measures:
- JWT token authentication
- CORS configuration for API access
- SQL injection protection via Django ORM
- XSS protection with Django security middleware
- Rate limiting on API endpoints
- Environment variable protection

## 🚨 Troubleshooting

### Common Issues I've Encountered:

**Celery not processing tasks**
```bash
# Check Redis connection
redis-cli ping

# Restart Celery worker
celery -A config worker -l info
```

**Email notifications not working**
```bash
# Test email configuration
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])
```

**Stock API rate limits**
- Monitor your API usage at Twelve Data dashboard
- The system implements exponential backoff for failed requests

## 🤝 Contributing

I welcome contributions! Here's how you can help:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Commit: `git commit -m 'Add amazing feature'`
5. Push: `git push origin feature/amazing-feature`
6. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ About Me

I'm Yousef Ali Mansour, a passionate developer focused on building practical solutions for real-world problems. This project combines my interests in finance, automation, and clean API design.

🌐 Connect With Me
GitHub: @yousefalimansour
LinkedIn: Yousef Morad
Email: moradyousef954@gmail.com
Phone: 01098433918
📞 Support & Feedback
Found a bug? Have a feature request? Want to discuss the architecture?
🐛 Bug Reports: Create an issue with detailed reproduction steps
💡 Feature Requests: Open an issue with your ideas
🤔 Questions: Start a discussion in GitHub Discussions
📧 Direct Contact: Email me for collaboration opportunities


---

⭐ **If you find this project useful, please consider giving it a star!**

Built with ❤️ by Yousef Ali Mansour
