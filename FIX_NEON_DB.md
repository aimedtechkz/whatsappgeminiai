# 🔧 Neon.tech Database URL Fix

## ❌ Problem

Neon.tech PostgreSQL URLs contain query parameters (`?sslmode=require&channel_binding=require`) that cause Pydantic validation errors.

**Error:**
```
Extra inputs are not permitted [type=extra_forbidden, input_value='require&channel_binding=require', input_type=str]
```

## ✅ Solutions

### **Solution 1: Quote the URL (Recommended)**

In your `.env` files, wrap the DATABASE_URL in quotes:

#### **ai-agent-service/.env**
```env
DATABASE_URL="postgresql://neondb_owner:npg_SwrTZs7Goz3E@ep-sparkling-unit-ag1o345l-pooler.c-2.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
```

#### **whatsapp-gateway/.env**
```env
DATABASE_URL="postgresql://your_neon_url_here?sslmode=require&channel_binding=require"
```

### **Solution 2: Already Fixed in Code! ✅**

I've updated both `config/settings.py` files to ignore extra fields:

```python
class Config:
    env_file = ".env"
    case_sensitive = True
    extra = "ignore"  # Ignore extra fields from .env parsing
```

This prevents the error even without quotes.

## 📝 Complete .env Example

### **ai-agent-service/.env**
```env
# Project Name
PROJECT_NAME=ai-agent-service

# Gemini API
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp

# Neon.tech Database (QUOTED!)
DATABASE_URL="postgresql://neondb_owner:npg_SwrTZs7Goz3E@ep-sparkling-unit-ag1o345l-pooler.c-2.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

# RabbitMQ (from Docker Compose)
RABBITMQ_URL=amqp://admin:admin123@localhost:5672/
QUEUE_INCOMING_MESSAGES=incoming_messages
QUEUE_OUTGOING_MESSAGES=outgoing_messages

# Settings
MAX_CONTEXT_MESSAGES=20
ENABLE_FOLLOW_UPS=true
FOLLOW_UP_INTERVALS=24,72,168,336,720
TIMEZONE=Asia/Almaty
WORKING_HOURS_START=10
WORKING_HOURS_END=18

# Knowledge Base
KNOWLEDGE_BASE_PATH=./knowledge_base/
PDF_CACHE_ENABLED=true

# Logging
LOG_LEVEL=INFO
HEALTH_CHECK_PORT=8001
```

### **whatsapp-gateway/.env**
```env
# Project Name
PROJECT_NAME=whatsapp-gateway

# Wappi API
WAPPI_TOKEN=your_wappi_token_here
WAPPI_PROFILE_ID=your_profile_id_here
WAPPI_PHONE_NUMBER=77752837306
WAPPI_BASE_URL=https://wappi.pro

# Neon.tech Database (QUOTED!)
DATABASE_URL="postgresql://your_neon_url_here?sslmode=require&channel_binding=require"

# RabbitMQ (from Docker Compose)
RABBITMQ_URL=amqp://admin:admin123@localhost:5672/
QUEUE_INCOMING_MESSAGES=incoming_messages
QUEUE_OUTGOING_MESSAGES=outgoing_messages
QUEUE_VOICE_TRANSCRIPTION=voice_transcription

# Gemini API
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp

# Settings
POLLING_INTERVAL=5
LOG_LEVEL=INFO
TIMEZONE=Asia/Almaty
HEALTH_CHECK_PORT=8000
```

## 🚀 Test the Fix

```bash
# Restart Docker Compose
docker-compose down
docker-compose up -d

# Check if services start without errors
docker-compose logs -f
```

## ✅ Should Work Now!

The combination of:
1. ✅ Quoting the DATABASE_URL
2. ✅ Updated settings.py with `extra = "ignore"`

...ensures the Neon.tech URL works perfectly!
