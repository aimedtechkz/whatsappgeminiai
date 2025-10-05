# 🤖 WhatsApp AI Agent System

Complete AI-powered WhatsApp automation system with two independent microservices communicating via message queues.

## 📋 System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                   SYSTEM ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  WhatsApp (Wappi.pro API)                                        │
│           ↓                                                       │
│  ┌──────────────────────────────┐                               │
│  │  PROJECT 1: WhatsApp Gateway │                               │
│  │  - Message Polling (5s)      │                               │
│  │  - Message Sending           │                               │
│  │  - Voice Transcription       │                               │
│  └──────────────────────────────┘                               │
│           ↓                                                       │
│  ┌──────────────────────────────┐                               │
│  │  RabbitMQ Message Queues     │                               │
│  │  - incoming_messages         │                               │
│  │  - outgoing_messages         │                               │
│  │  - voice_transcription       │                               │
│  └──────────────────────────────┘                               │
│           ↓                                                       │
│  ┌──────────────────────────────┐                               │
│  │  PROJECT 2: AI Agent Service │                               │
│  │  - AI Moderator              │                               │
│  │  - AI Sales Agent            │                               │
│  │  - Follow-up Scheduler       │                               │
│  └──────────────────────────────┘                               │
│           ↓                                                       │
│  RabbitMQ → PROJECT 1 → WhatsApp                                │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Features

### PROJECT 1: WhatsApp Gateway
- ✅ **Polling Service**: Retrieves messages every 5 seconds
- ✅ **Sender Service**: Sends responses with rate limiting
- ✅ **Voice Transcription**: Gemini-powered audio to text
- ✅ **Whitelist Filtering**: Ignores specified numbers
- ✅ **Health Check API**: Monitor service status

### PROJECT 2: AI Agent Service
- 🤖 **AI Moderator**: Classifies contacts (client/non-client)
- 💼 **AI Sales Agent**: SPIN-based sales methodology
- 📚 **Knowledge Base**: PDF-powered product information
- 📞 **Follow-up Scheduler**: 5-touch automated sequences
- 🕐 **Smart Scheduling**: Working hours (10:00-18:00 Astana)
- 📊 **Analytics API**: Track performance

## 📦 Project Structure

```
whatsappAI/
├── whatsapp-gateway/          # PROJECT 1
│   ├── api/                   # Health check endpoints
│   ├── config/                # Settings, database, queue
│   ├── models/                # SQLAlchemy models
│   ├── services/              # Core services
│   │   ├── wappi_client.py   # Wappi API wrapper
│   │   ├── polling_service.py
│   │   ├── sender_service.py
│   │   └── voice_service.py
│   ├── utils/                 # Utilities
│   ├── app.py                 # Main entry point
│   ├── init_db.py            # Database setup
│   └── requirements.txt
│
├── ai-agent-service/          # PROJECT 2
│   ├── api/                   # Health check endpoints
│   ├── config/                # Settings, database, queue
│   ├── models/                # SQLAlchemy models
│   ├── services/              # Core services
│   │   ├── gemini_client.py  # Gemini API wrapper
│   │   ├── ai_moderator.py   # Contact classifier
│   │   ├── ai_sales_agent.py # Sales agent
│   │   ├── follow_up_scheduler.py
│   │   ├── message_consumer.py
│   │   └── knowledge_loader.py
│   ├── prompts/               # AI prompts
│   │   ├── moderator_prompt.txt
│   │   ├── sales_agent_prompt.txt
│   │   └── follow_up_prompt.txt
│   ├── knowledge_base/        # PDF files
│   ├── utils/                 # Utilities
│   ├── app.py                 # Main entry point
│   ├── init_db.py            # Database setup
│   └── requirements.txt
│
└── documentation/             # Full documentation
```

## 🛠️ Installation

### Prerequisites
- Python 3.11+
- PostgreSQL (2 databases)
- RabbitMQ or Redis
- Wappi.pro account
- Google Gemini API key

### Quick Start

#### 1. Clone Repository
```bash
git clone <repository-url>
cd whatsappAI
```

#### 2. Setup PROJECT 1 (WhatsApp Gateway)
```bash
cd whatsapp-gateway
cp .env.example .env
# Edit .env with your credentials
pip install -r requirements.txt
python init_db.py
python app.py
```

#### 3. Setup PROJECT 2 (AI Agent Service)
```bash
cd ai-agent-service
cp .env.example .env
# Edit .env with your credentials
# Add PDF files to knowledge_base/
pip install -r requirements.txt
python init_db.py
python app.py
```

## ⚙️ Configuration

### PROJECT 1 Environment Variables
```env
WAPPI_TOKEN=your_token
WAPPI_PROFILE_ID=your_profile_id
DATABASE_URL=postgresql://user:password@host:5432/whatsapp_gateway
RABBITMQ_URL=amqp://user:password@host:5672/
GEMINI_API_KEY=your_gemini_key
```

### PROJECT 2 Environment Variables
```env
GEMINI_API_KEY=your_gemini_key
DATABASE_URL=postgresql://user:password@host:5432/ai_agent
RABBITMQ_URL=amqp://user:password@host:5672/
ENABLE_FOLLOW_UPS=true
FOLLOW_UP_INTERVALS=24,72,168,336,720
WORKING_HOURS_START=10
WORKING_HOURS_END=18
```

## 📊 Database Schema

### PROJECT 1 Tables
- **message_logs**: All incoming/outgoing messages
- **whitelist**: Numbers to ignore

### PROJECT 2 Tables
- **contacts**: Contact information and classification
- **messages**: Conversation history
- **follow_ups**: Follow-up sequences
- **scheduled_calls**: Call scheduling

## 🔄 Message Flow

1. **Incoming Message**
   - Wappi API → Polling Service
   - Check whitelist
   - Publish to `incoming_messages` queue

2. **Voice Messages**
   - Publish to `voice_transcription` queue
   - Download audio → Gemini transcription
   - Publish transcribed text to `incoming_messages`

3. **AI Processing**
   - Message Consumer receives message
   - Create/update contact
   - AI Moderator classifies (if needed)
   - AI Sales Agent generates response
   - Publish to `outgoing_messages` queue

4. **Outgoing Message**
   - Sender Service consumes from queue
   - Send via Wappi API
   - Log in database

5. **Follow-up**
   - Scheduler checks contacts
   - Generate follow-up messages (5 touches)
   - Publish to `outgoing_messages` queue

## 📞 Follow-up Strategy

| Touch | Interval | Strategy |
|-------|----------|----------|
| 1 | 24 hours | Friendly reminder |
| 2 | 3 days | Value proposition |
| 3 | 7 days | Social proof |
| 4 | 14 days | Urgency/last chance |
| 5 | 30 days | Farewell message |

**Stop Conditions**:
- Client says YES (definitive agreement)
- Client says NO (definitive rejection)
- Client responds (continues conversation)

**Continue Conditions**:
- Client ignores message
- Client gives uncertain response ("maybe", "I'll think")

## 🏥 Health Monitoring

### PROJECT 1
```bash
curl http://localhost:8000/health
curl http://localhost:8000/stats
```

### PROJECT 2
```bash
curl http://localhost:8001/health
curl http://localhost:8001/stats
curl http://localhost:8001/contacts?is_client=true
curl http://localhost:8001/follow-ups/active
```

## 🚢 Deployment

### Docker Compose
```yaml
version: '3.8'
services:
  whatsapp-gateway:
    build: ./whatsapp-gateway
    env_file: ./whatsapp-gateway/.env
    ports:
      - "8000:8000"

  ai-agent-service:
    build: ./ai-agent-service
    env_file: ./ai-agent-service/.env
    ports:
      - "8001:8001"

  rabbitmq:
    image: rabbitmq:3-management
    ports:
      - "5672:5672"
      - "15672:15672"
```

### Render.com
1. Create two Web Services
2. Connect Git repositories
3. Set environment variables
4. Deploy

## 📝 Key Settings

### Whitelist Numbers (Ignored)
- +77752837306
- +77018855588
- +77088098009

### Working Hours
- Monday - Friday
- 10:00 - 18:00 (Asia/Almaty, UTC+5)

### Rate Limits
- Wappi API: 20 messages/minute
- Polling: Every 5 seconds

## 🧪 Testing

### Test Message Flow
```bash
# Send test message via Wappi
curl -X POST https://wappi.pro/api/sync/message/send \
  -H "Authorization: YOUR_TOKEN" \
  -d '{"recipient":"79115576362","body":"Test message"}'
```

### Check Logs
```bash
# PROJECT 1
tail -f whatsapp-gateway/logs/app_*.log

# PROJECT 2
tail -f ai-agent-service/logs/app_*.log
```

## 🐛 Troubleshooting

### RabbitMQ Connection Issues
```bash
# Check RabbitMQ status
curl http://localhost:15672/api/overview

# Restart service
docker-compose restart rabbitmq
```

### Database Issues
```bash
# Reinitialize databases
python whatsapp-gateway/init_db.py
python ai-agent-service/init_db.py
```

### Gemini API Errors
- Check API key validity
- Verify quota limits
- Review error logs

## 📚 Documentation

Detailed documentation available in `documentation/`:
- [Technical Specification](documentation/techdoc.md)
- [Task List](documentation/tasks.md)
- [API Endpoints](documentation/)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Submit pull request

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- Wappi.pro for WhatsApp API
- Google Gemini for AI capabilities
- RabbitMQ for message queuing

---

**Status**: ✅ Production Ready
**Version**: 1.0.0
**Last Updated**: October 2025
#   w h a t s a p p g e m i n i a i  
 