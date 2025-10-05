# AI Agent Service

AI-powered sales agent service using Gemini 2.5 Pro for contact classification, sales responses, and follow-up sequences.

## Features

- 🤖 **AI Moderator**: Classifies contacts as clients/non-clients
- 💼 **AI Sales Agent**: SPIN-based sales methodology
- 📚 **Knowledge Base**: PDF-based product information
- 📞 **Follow-up Scheduler**: 5-touch automated sequences
- 🕐 **Smart Scheduling**: Working hours (10:00-18:00 Astana)
- 📊 **Health Check API**: Monitor service health

## Architecture

```
Incoming Messages → Consumer → AI Moderator → Classification
                                      ↓
                               AI Sales Agent → Response
                                      ↓
                            Follow-up Scheduler → 5 Touches
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

3. **Add knowledge base PDFs**:
```bash
# Place PDF files in knowledge_base/ directory
cp your_product_info.pdf knowledge_base/
```

4. **Initialize database**:
```bash
python init_db.py
```

## Configuration

Required environment variables in `.env`:

```env
# Gemini API
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-2.0-flash-exp

# Database
DATABASE_URL=postgresql://user:password@host:5432/ai_agent

# RabbitMQ
RABBITMQ_URL=amqp://user:password@host:5672/

# Settings
MAX_CONTEXT_MESSAGES=20
ENABLE_FOLLOW_UPS=true
FOLLOW_UP_INTERVALS=24,72,168,336,720
WORKING_HOURS_START=10
WORKING_HOURS_END=18
TIMEZONE=Asia/Almaty
```

## Usage

### Run the service:
```bash
python app.py
```

### Health Check:
```bash
curl http://localhost:8001/health
curl http://localhost:8001/stats
curl http://localhost:8001/contacts
curl http://localhost:8001/follow-ups/active
```

## Services

### 1. Message Consumer
- Consumes from `incoming_messages` queue
- Creates/updates contacts
- Routes to AI Moderator or Sales Agent
- Stops follow-ups when client responds

### 2. AI Moderator
- Classifies contacts using Gemini
- Criteria: company name, business questions, style
- Returns: isClient (true/false/null), confidence, reasoning
- Minimum 3 messages required

### 3. AI Sales Agent
- Generates responses using SPIN methodology
- Uses PDF knowledge base
- Schedules calls (working hours only)
- Sends to `outgoing_messages` queue

### 4. Follow-up Scheduler
- 5-touch sequence: 24h, 3d, 7d, 14d, 30d
- Stops on: YES, NO, or client response
- Continues on: ignore or uncertain response

## Database Models

### Contact
- phone_number, name, business_name
- is_client, classification_confidence
- last_message_at

### Message
- contact_id, message_text
- is_from_bot, is_voice
- timestamp

### FollowUp
- contact_id, touch_number (1-5)
- next_touch_at, is_completed
- stop_reason

### ScheduledCall
- contact_id, scheduled_at
- timezone, status, notes

## Prompts

### Moderator Prompt
Located in: `prompts/moderator_prompt.txt`
- Client criteria (company, business questions)
- Non-client criteria (spam, personal)
- Returns JSON with classification

### Sales Agent Prompt
Located in: `prompts/sales_agent_prompt.txt`
- SPIN selling methodology
- Knowledge base integration
- Call scheduling rules
- Professional tone

### Follow-up Prompt
Located in: `prompts/follow_up_prompt.txt`
- Touch 1: Friendly reminder
- Touch 2: Value proposition
- Touch 3: Social proof
- Touch 4: Urgency/last chance
- Touch 5: Farewell message

## API Endpoints

- `GET /health` - Service health status
- `GET /stats` - Statistics (contacts, messages, follow-ups)
- `GET /contacts?is_client=true` - Get contacts by status
- `GET /follow-ups/active` - Active follow-up sequences
- `GET /` - Service information

## Deployment

### Docker
```bash
docker build -t ai-agent-service .
docker run -d --env-file .env ai-agent-service
```

### Render.com
1. Connect GitHub repository
2. Set environment variables
3. Upload PDF files to knowledge_base/
4. Deploy

## Knowledge Base

Place PDF files in `knowledge_base/` directory:
- product_info.pdf
- pricing.pdf
- faq.pdf

The system will automatically load and index all PDFs on startup.

## Monitoring

- Logs: `logs/app_YYYY-MM-DD.log`
- Retention: 30 days
- Health endpoint: `/health`

## Troubleshooting

### Common Issues

1. **Gemini API errors**
   - Check GEMINI_API_KEY
   - Verify quota limits

2. **Classification not working**
   - Ensure at least 3 messages in conversation
   - Check moderator_prompt.txt

3. **Follow-ups not sending**
   - Verify ENABLE_FOLLOW_UPS=true
   - Check working hours settings

## License

MIT
