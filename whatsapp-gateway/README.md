# WhatsApp Gateway Service

WhatsApp message gateway service that integrates with Wappi.pro API for sending/receiving WhatsApp messages.

## Features

- 📥 **Message Polling**: Polls Wappi API every 5 seconds for new messages
- 📤 **Message Sending**: Sends messages from queue to WhatsApp
- 🎤 **Voice Transcription**: Transcribes voice messages using Gemini AI
- 🚫 **Whitelist Filtering**: Filters messages from specified numbers
- 📊 **Health Check API**: Monitor service health and statistics
- 🔄 **RabbitMQ Integration**: Publishes/consumes messages via queues

## Architecture

```
WhatsApp (Wappi API) → Polling Service → RabbitMQ Queues
                                            ↓
                                      AI Agent Service
                                            ↓
                       Sender Service ← RabbitMQ Queues
                              ↓
                    WhatsApp (Wappi API)
```

## Installation

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your credentials
```

3. **Initialize database**:
```bash
python init_db.py
```

## Configuration

Required environment variables in `.env`:

```env
# Wappi API
WAPPI_TOKEN=your_token
WAPPI_PROFILE_ID=your_profile_id
WAPPI_PHONE_NUMBER=77752837306

# Database
DATABASE_URL=postgresql://user:password@host:5432/whatsapp_gateway

# RabbitMQ
RABBITMQ_URL=amqp://user:password@host:5672/

# Gemini API (for voice transcription)
GEMINI_API_KEY=your_gemini_key
```

## Usage

### Run the service:
```bash
python app.py
```

### Health Check:
```bash
curl http://localhost:8000/health
curl http://localhost:8000/stats
```

## Services

### 1. Polling Service
- Polls Wappi API every 5 seconds
- Checks whitelist
- Publishes to `incoming_messages` queue
- Publishes voice messages to `voice_transcription` queue

### 2. Sender Service
- Consumes from `outgoing_messages` queue
- Sends via Wappi API
- Rate limiting: 20 messages/minute
- Retry logic: 3 attempts

### 3. Voice Transcription Service
- Consumes from `voice_transcription` queue
- Downloads audio from Wappi
- Transcribes using Gemini
- Publishes text to `incoming_messages`

## Database Models

### MessageLog
- Tracks all incoming/outgoing messages
- Fields: message_id, phone_number, direction, text, is_voice, status

### Whitelist
- Stores numbers to ignore
- Pre-populated with: +77752837306, +77018855588, +77088098009

## API Endpoints

- `GET /health` - Service health status
- `GET /stats` - Daily statistics
- `GET /` - Service information

## Deployment

### Docker
```bash
docker build -t whatsapp-gateway .
docker run -d --env-file .env whatsapp-gateway
```

### Render.com
1. Connect GitHub repository
2. Set environment variables
3. Deploy

## Monitoring

- Logs: `logs/app_YYYY-MM-DD.log`
- Retention: 30 days
- Health endpoint: `/health`

## Troubleshooting

### Common Issues

1. **RabbitMQ connection failed**
   - Check RABBITMQ_URL
   - Verify queue service is running

2. **Wappi API errors**
   - Verify WAPPI_TOKEN and WAPPI_PROFILE_ID
   - Check rate limits

3. **Database errors**
   - Run `python init_db.py`
   - Check DATABASE_URL

## License

MIT
