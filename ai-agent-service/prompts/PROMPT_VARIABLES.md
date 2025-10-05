# Prompt Variables Reference

This document describes all variables used in the prompt templates and how they are populated by the system.

---

## 1. moderator_prompt.txt

**Purpose:** Classify contacts as clients, non-clients, or unknown based on conversation history.

**Required Variables:**

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `{contact_name}` | string | Name saved in WhatsApp contacts | "Иван", "ООО Стройком" |
| `{full_name}` | string | Full name from WhatsApp profile | "Иван Петров" |
| `{business_name}` | string | Company name if available | "ООО Стройком", "Нет" |
| `{conversation_history}` | string | Formatted chat history (last 20 messages) | "КЛИЕНТ: Здравствуйте\nБОТ: Привет!" |

**Populated by:** `ai_moderator.py` → `classify_contact()` method

**Output:** JSON with classification result
```json
{
  "isClient": true,
  "confidence": 0.85,
  "reasoning": "Контакт сохранен как 'Иван - ООО Стройком', задает вопросы о ценах"
}
```

---

## 2. sales_agent_prompt.txt

**Purpose:** Generate sales responses to client messages using SPIN methodology.

**Required Variables:**

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `{knowledge_base}` | string | Product information from PDF files | "Курс: Vibe Coding...\nМодули: 1) Веб..." |
| `{conversation_history}` | string | Chat history formatted for display | "КЛИЕНТ: Сколько стоит?\nБОТ: 75,000₸" |
| `{new_message}` | string | Latest message from client | "Есть рассрочка?" |

**Populated by:** `ai_sales_agent.py` → `generate_response()` method

**Output:** Plain text sales response
```
Да, есть рассрочка 0%, выходит 25к в месяц. Один проект окупит курс.

Это удобнее для вас?
```

**Additional Context:**
- System loads knowledge base from `knowledge_base/` folder (PDF files)
- Knowledge base is limited to 3000 chars to avoid token limits
- Conversation history includes last 20 messages

---

## 3. follow_up_prompt.txt

**Purpose:** Generate follow-up messages for clients who stopped responding (5-touch strategy).

**Required Variables:**

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `{touch_number}` | integer | Current touch number (1-5) | 1, 2, 3, 4, 5 |
| `{conversation_history}` | string | Full chat history | "КЛИЕНТ: Интересно\nБОТ: Отлично!" |
| `{last_bot_message}` | string | Last message sent by bot | "Есть вопросы?" |
| `{last_client_message}` | string | Last message from client | "Подумаю" |
| `{follow_up_reason}` | string | Why follow-up was triggered | "Клиент не ответил в течение 24 часов" |
| `{hours_since_last_message}` | integer | Hours since last client message | 24, 72, 168 |
| `{current_datetime}` | string | Current date and time in Asia/Almaty | "2025-10-05 15:30:00 +05" |

**Populated by:** `follow_up_scheduler.py` → `generate_followup_message()` method

**Output:** Plain text follow-up message
```
Привет! Думали над курсом?

Что конкретно волнует?
```

**Follow-up Schedule:**
- Touch 1: 24 hours after last message
- Touch 2: 72 hours (3 days)
- Touch 3: 168 hours (7 days)
- Touch 4: 336 hours (14 days)
- Touch 5: 720 hours (30 days)

---

## Variable Formatting Guidelines

### Conversation History Format

All conversation histories are formatted as:
```
КЛИЕНТ: [message text]
БОТ: [message text]
[ГОЛОСОВОЕ] [transcription]  # For voice messages
```

Example:
```
КЛИЕНТ: Здравствуйте
БОТ: Привет! Интересует курс?
КЛИЕНТ: Да, сколько стоит?
БОТ: 75,000₸ в месяц онлайн
КЛИЕНТ: [ГОЛОСОВОЕ] Есть ли рассрочка?
БОТ: Да, есть рассрочка 0%
```

### Date/Time Format

All dates use Asia/Almaty timezone (UTC+5):
```
2025-10-05 13:45:30 +05
```

### Knowledge Base

Knowledge base content is extracted from PDF files in `knowledge_base/` folder and includes:
- Product descriptions
- Course modules
- Pricing information
- FAQs

---

## Testing Variables

To test if prompts work correctly, check:

1. **Variable Presence:** All `{variable_name}` placeholders are replaced
2. **No Empty Values:** No variables contain "Неизвестно" or "Нет" when data exists
3. **Formatting:** Conversation history is readable
4. **Length:** Knowledge base doesn't exceed 3000 chars

---

## Common Issues

### Issue: Variable not replaced
**Cause:** Typo in variable name or missing in `.format()` call
**Fix:** Check variable name matches exactly in both prompt and code

### Issue: Empty conversation history
**Cause:** Not enough messages in database
**Fix:** Moderator requires minimum 3 messages to classify

### Issue: Knowledge base too long
**Cause:** Large PDF files
**Fix:** System automatically truncates to 3000 chars

---

## Code Locations

- **Moderator:** `services/ai_moderator.py` line 137
- **Sales Agent:** `services/ai_sales_agent.py` line 167
- **Follow-up:** `services/follow_up_scheduler.py` line 194

---

Last Updated: 2025-10-05
