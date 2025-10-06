# 🤖 WhatsApp AI Agent System

An intelligent WhatsApp automation system powered by Google Gemini AI, designed for automated customer interaction, lead qualification, and follow-up management.

## 📋 Overview

This system consists of two microservices working together:

1. **WhatsApp Gateway** - Handles WhatsApp message polling and sending via Wappi.pro API
2. **AI Agent Service** - Processes messages with Google Gemini AI, manages contacts, and schedules follow-ups

Both services communicate asynchronously through RabbitMQ message broker and store data in PostgreSQL databases.

## ✨ Features

- 🔄 **Automated Message Processing** - Polls and processes WhatsApp messages in real-time
- 🤖 **AI-Powered Responses** - Uses Google Gemini 2.0 Flash for intelligent conversation
- 📊 **Lead Qualification** - Automatically classifies contacts as cold, warm, or hot leads
- ⏰ **Smart Follow-ups** - Schedules automated follow-up messages based on contact engagement
- 🎙️ **Voice Message Transcription** - Converts voice messages to text using Gemini AI
- 📞 **Call Scheduling** - Tracks and manages scheduled client calls
- 🛡️ **Whitelist Management** - Filters messages from specific phone numbers
- 📚 **Knowledge Base** - Supports PDF-based knowledge for contextual AI responses
- 🏥 **Health Monitoring** - Built-in health check endpoints for both services

## 🏗️ Architecture

```
┌─────────────────┐      ┌──────────────┐      ┌─────────────────┐
│  WhatsApp API   │◄────►│   Gateway    │◄────►│   RabbitMQ      │
│   (Wappi.pro)   │      │   Service    │      │  Message Broker │
└─────────────────┘      └──────────────┘      └─────────────────┘
                                │                        │
                                ▼                        ▼
                         ┌──────────────┐      ┌─────────────────┐
                         │  PostgreSQL  │      │   AI Agent      │
                         │   Gateway    │      │    Service      │
                         └──────────────┘      └─────────────────┘
                                                        │
                                                        ▼
                                                ┌──────────────┐
                                                │  PostgreSQL  │
                                                │    Agent     │
                                                └──────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Wappi.pro account with API access
- Google Gemini API key
- Neon.tech PostgreSQL database (or any PostgreSQL)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd whatsappAI
```

2. **Configure environment variables**
```bash
cp .env.example .env
```

Edit `.env` file with your credentials:
```env
WAPPI_TOKEN=your_wappi_token_here
WAPPI_PROFILE_ID=your_profile_id_here
WAPPI_PHONE_NUMBER=your_phone_number
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql://user:pass@host/db?sslmode=require
```

3. **Start all services**
```bash
docker-compose up -d
```

4. **Initialize databases**
```bash
# Initialize WhatsApp Gateway database and whitelist
docker exec whatsapp-gateway python init_db.py

# Initialize AI Agent database
docker exec ai-agent-service python init_db.py
```

5. **Verify services are running**
```bash
# Check WhatsApp Gateway health
curl http://localhost:8000/health

# Check AI Agent health
curl http://localhost:8001/health
```

## 📦 Services

### WhatsApp Gateway (Port 8000)

**Responsibilities:**
- Polls Wappi.pro API for new WhatsApp messages
- Sends outgoing messages via Wappi.pro
- Transcribes voice messages using Gemini AI
- Manages message whitelist (filtered phone numbers)
- Publishes messages to RabbitMQ queue

**Key Endpoints:**
- `GET /health` - Service health check
- Polling runs automatically in background

### AI Agent Service (Port 8001)

**Responsibilities:**
- Consumes incoming messages from RabbitMQ
- Processes messages with Google Gemini AI
- Manages contact database and conversation history
- Classifies leads (cold/warm/hot)
- Schedules and sends follow-up messages
- Tracks scheduled calls with clients

**Key Endpoints:**
- `GET /health` - Service health check
- Message processing runs automatically via queue consumer

## 🗄️ Database Schema

### Gateway Database
- `message_log` - Stores all incoming/outgoing messages
- `whitelist` - Phone numbers to ignore

### Agent Database
- `contacts` - Contact information and lead classification
- `messages` - Conversation history with AI context
- `follow_ups` - Scheduled follow-up messages
- `scheduled_calls` - Planned client calls

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `WAPPI_TOKEN` | Wappi.pro API token | Required |
| `WAPPI_PROFILE_ID` | Wappi.pro profile ID | Required |
| `WAPPI_PHONE_NUMBER` | Your WhatsApp number | Required |
| `GEMINI_API_KEY` | Google Gemini API key | Required |
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `POLLING_INTERVAL` | Message polling interval (seconds) | 5 |
| `TIMEZONE` | System timezone | Asia/Almaty |
| `WORKING_HOURS_START` | Follow-up start hour | 10 |
| `WORKING_HOURS_END` | Follow-up end hour | 18 |
| `ENABLE_FOLLOW_UPS` | Enable automated follow-ups | true |
| `FOLLOW_UP_INTERVALS` | Follow-up intervals in hours | 24,72,168,336,720 |
| `MAX_CONTEXT_MESSAGES` | Max messages in AI context | 20 |
| `LOG_LEVEL` | Logging level | INFO |

### Whitelist Management

Add phone numbers to whitelist (messages from these numbers will be ignored):

1. Edit `whatsapp-gateway/init_db.py` and add numbers to the `whitelist_numbers` list
2. Run: `docker exec whatsapp-gateway python init_db.py`

## 📚 Knowledge Base

Place PDF documents in `ai-agent-service/knowledge_base/` directory. The AI agent will use these documents to provide contextual responses.

Supported formats:
- PDF documents (automatically processed and cached)

## 🔍 Monitoring & Logs

### View Logs
```bash
# Gateway logs
docker logs whatsapp-gateway -f

# Agent logs
docker logs ai-agent-service -f

# RabbitMQ management UI
# Open http://localhost:15672
# Username: admin, Password: admin123
```

### Service Status
```bash
docker-compose ps
```

## 🛠️ Development

### Project Structure
```
whatsappAI/
├── whatsapp-gateway/           # Gateway service
│   ├── api/                   # FastAPI endpoints
│   ├── services/              # Business logic
│   ├── models/                # Database models
│   ├── config/                # Configuration
│   ├── app.py                 # Main application
│   └── Dockerfile
│
├── ai-agent-service/          # AI Agent service
│   ├── api/                   # FastAPI endpoints
│   ├── services/              # AI logic & consumers
│   ├── models/                # Database models
│   ├── knowledge_base/        # PDF documents
│   ├── app.py                 # Main application
│   └── Dockerfile
│
├── docker-compose.yml         # Docker orchestration
└── .env                       # Environment variables
```

### Running Tests
```bash
# Gateway tests
docker exec whatsapp-gateway pytest

# Agent tests
docker exec ai-agent-service pytest
```

## 🔄 Follow-up System

The AI agent automatically schedules follow-ups based on contact engagement:

**Default intervals:**
- 24 hours (1 day)
- 72 hours (3 days)
- 168 hours (1 week)
- 336 hours (2 weeks)
- 720 hours (1 month)

Follow-ups only send during working hours (10 AM - 6 PM by default).

## 🔐 Security

- ✅ Environment variables for sensitive data
- ✅ `.env` files excluded from git
- ✅ Database connection over SSL
- ✅ Whitelist filtering
- ✅ No hardcoded credentials

**Important:** Never commit `.env` files or expose API keys!

## 🐛 Troubleshooting

### Services won't start
```bash
# Check logs
docker-compose logs

# Restart services
docker-compose restart

# Rebuild containers
docker-compose up -d --build
```

### Database connection issues
- Verify `DATABASE_URL` in `.env` is correct
- Check PostgreSQL service is healthy: `docker-compose ps`
- Test connection: `docker exec whatsapp-postgres-gateway pg_isready`

### RabbitMQ connection issues
- Check RabbitMQ is running: `docker-compose ps rabbitmq`
- Access management UI: http://localhost:15672 (admin/admin123)

### Messages not processing
- Verify Wappi.pro credentials are correct
- Check Gateway logs: `docker logs whatsapp-gateway -f`
- Verify RabbitMQ queues have messages: http://localhost:15672

## 📄 License

This project is proprietary software.

## 🤝 Support

For issues and questions, contact the development team.

---

**Made with ❤️ using Google Gemini AI, Python, FastAPI, and Docker**
