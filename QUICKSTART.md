# 🚀 Quick Start Guide

Get your WhatsApp AI Agent System running in minutes!

## Prerequisites

- Docker & Docker Compose installed
- Wappi.pro account with WhatsApp connected
- Google Gemini API key

## Step 1: Get API Credentials

### Wappi.pro Setup
1. Go to https://wappi.pro
2. Sign up and connect your WhatsApp number
3. Navigate to Settings → API
4. Copy your:
   - API Token
   - Profile ID

### Google Gemini Setup
1. Go to https://ai.google.dev
2. Sign in with Google account
3. Create API key
4. Copy the key

## Step 2: Configure Environment

```bash
# Clone repository (or download)
git clone <repository-url>
cd whatsappAI

# Create environment file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

**Edit `.env` file:**
```env
WAPPI_TOKEN=your_actual_wappi_token
WAPPI_PROFILE_ID=your_actual_profile_id
WAPPI_PHONE_NUMBER=77752837306
GEMINI_API_KEY=your_actual_gemini_key
```

## Step 3: Add Knowledge Base (Optional)

```bash
# Add your product PDF files
cp your_product_info.pdf ai-agent-service/knowledge_base/
cp your_pricing.pdf ai-agent-service/knowledge_base/
```

Or use the sample file for testing.

## Step 4: Launch System

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

## Step 5: Initialize Databases

```bash
# Initialize PROJECT 1 database
docker-compose exec whatsapp-gateway python init_db.py

# Initialize PROJECT 2 database
docker-compose exec ai-agent-service python init_db.py
```

## Step 6: Verify Services

### Check Health Endpoints

```bash
# WhatsApp Gateway Health
curl http://localhost:8000/health

# AI Agent Service Health
curl http://localhost:8001/health
```

### Check RabbitMQ

Open browser: http://localhost:15672
- Username: `admin`
- Password: `admin123`

### Check Databases

```bash
# Connect to PostgreSQL
docker-compose exec postgres-gateway psql -U postgres -d whatsapp_gateway
docker-compose exec postgres-agent psql -U postgres -d ai_agent
```

## Step 7: Test the System

### Send Test Message

1. Send WhatsApp message to your connected number
2. Check logs:
```bash
docker-compose logs -f whatsapp-gateway
docker-compose logs -f ai-agent-service
```

### Monitor Queues

```bash
# Check queue stats
curl http://localhost:8000/stats
curl http://localhost:8001/stats
```

## 🎉 You're Done!

Your WhatsApp AI Agent is now running!

### What Happens Next:

1. **New Messages** → Polling service retrieves every 5s
2. **Voice Messages** → Automatically transcribed
3. **Classification** → AI determines if contact is a client
4. **Responses** → AI generates sales responses
5. **Follow-ups** → Automated 5-touch sequences

## 📊 Monitoring

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f whatsapp-gateway
docker-compose logs -f ai-agent-service
```

### Health Checks
```bash
# Gateway health
curl http://localhost:8000/health

# Agent health
curl http://localhost:8001/health

# Get statistics
curl http://localhost:8000/stats
curl http://localhost:8001/stats

# View contacts
curl http://localhost:8001/contacts?is_client=true

# Active follow-ups
curl http://localhost:8001/follow-ups/active
```

### RabbitMQ Management
- URL: http://localhost:15672
- Username: `admin`
- Password: `admin123`

## 🔧 Common Commands

### Restart Services
```bash
docker-compose restart
```

### Stop Services
```bash
docker-compose down
```

### View Service Logs
```bash
docker-compose logs -f whatsapp-gateway
docker-compose logs -f ai-agent-service
```

### Update Configuration
```bash
# Edit .env
nano .env

# Restart to apply changes
docker-compose down
docker-compose up -d
```

### Database Access
```bash
# Gateway database
docker-compose exec postgres-gateway psql -U postgres -d whatsapp_gateway

# Agent database
docker-compose exec postgres-agent psql -U postgres -d ai_agent
```

## 🐛 Troubleshooting

### Services won't start
```bash
# Check logs
docker-compose logs

# Verify .env file
cat .env

# Restart everything
docker-compose down
docker-compose up -d
```

### No messages being processed
```bash
# Check Wappi credentials
curl -H "Authorization: YOUR_TOKEN" https://wappi.pro/api/sync/chats/get?profile_id=YOUR_PROFILE_ID

# Check polling service logs
docker-compose logs -f whatsapp-gateway | grep "polling"
```

### Database errors
```bash
# Reinitialize databases
docker-compose exec whatsapp-gateway python init_db.py
docker-compose exec ai-agent-service python init_db.py
```

### RabbitMQ connection issues
```bash
# Check RabbitMQ is running
docker-compose ps rabbitmq

# Restart RabbitMQ
docker-compose restart rabbitmq
```

## 📝 Configuration Tips

### Whitelist Numbers
Edit in database or `init_db.py`:
- +77752837306
- +77018855588
- +77088098009

### Working Hours
Change in `.env`:
```env
WORKING_HOURS_START=10
WORKING_HOURS_END=18
TIMEZONE=Asia/Almaty
```

### Follow-up Intervals
Change in `.env`:
```env
FOLLOW_UP_INTERVALS=24,72,168,336,720
# (24h, 3d, 7d, 14d, 30d in hours)
```

### Disable Follow-ups
```env
ENABLE_FOLLOW_UPS=false
```

## 🚀 Next Steps

1. **Customize Prompts**
   - Edit `ai-agent-service/prompts/*.txt`
   - Restart AI Agent Service

2. **Add Product Info**
   - Upload PDFs to `ai-agent-service/knowledge_base/`
   - Restart AI Agent Service

3. **Monitor Performance**
   - Check `/stats` endpoints regularly
   - Review logs for errors
   - Adjust settings as needed

4. **Scale Up**
   - Deploy to cloud (Render.com, AWS, etc.)
   - Add monitoring (Prometheus, Grafana)
   - Setup alerts

## 📞 Support

Need help? Check:
- [Full Documentation](README.md)
- [Technical Docs](documentation/techdoc.md)
- [Task List](documentation/tasks.md)

---

**Happy Automating! 🤖**
