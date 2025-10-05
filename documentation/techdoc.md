# 📋 ПОЛНОЕ ТЕХНИЧЕСКОЕ ЗАДАНИЕ: WhatsApp AI Agent System

## 🎯 Общая архитектура системы

Система состоит из **двух независимых проектов**, взаимодействующих через **очереди сообщений (RabbitMQ/Redis)**.

```
┌─────────────────────────────────────────────────────────────────┐
│                        ПРОЕКТ 1                                  │
│                  WhatsApp Gateway Service                        │
│              (Интеграция с Wappi.pro API)                        │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     │ RabbitMQ/Redis Queue
                     │
                     ▼
        ┌────────────────────────────┐
        │   incoming_messages Queue   │
        │   outgoing_messages Queue   │
        │   voice_transcription Queue │
        └────────────────────────────┘
                     │
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                        ПРОЕКТ 2                                  │
│                   AI Agent Service                               │
│          (Gemini 2.5 Pro + Business Logic)                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📦 ПРОЕКТ 1: WhatsApp Gateway Service

### **Назначение**
Отвечает за все взаимодействия с WhatsApp через Wappi.pro API. Получает сообщения, отправляет ответы, транскрибирует голосовые.

### **Технологии**
- **Backend**: Python 3.11+
- **Framework**: FastAPI (для health-check endpoints)
- **Queue**: RabbitMQ (или Redis с pub/sub)
- **Database**: PostgreSQL (только для логирования и отслеживания статусов)
- **Hosting**: Render.com

---

### **Основные компоненты**

#### 1. **Message Polling Service**
**Файл**: `services/polling_service.py`

**Функции**:
- Polling Wappi API каждые 5 секунд
- Получение новых чатов через `POST /api/sync/chats/get`
- Извлечение новых сообщений из каждого чата
- Фильтрация по whitelist (пропуск номеров: +77752837306, +77018855588, +77088098009)
- Публикация новых сообщений в очередь `incoming_messages`

**Endpoints Wappi**:
```
POST https://wappi.pro/api/sync/chats/get
Headers: Authorization: {Token}
Params:
  - profile_id: {profile_id}
  - limit: 100
  - offset: 0
```

**Формат сообщения в очередь**:
```json
{
  "message_id": "3EB0128AE55B5D222DD0",
  "chat_id": "79115576362@c.us",
  "phone_number": "79115576362",
  "sender_name": "Иван Петров",
  "message_text": "Здравствуйте, интересует ваш продукт",
  "is_voice": false,
  "voice_url": null,
  "timestamp": "2025-10-05T14:30:00+05:00",
  "contact_info": {
    "FirstName": "Иван",
    "FullName": "Иван Петров",
    "PushName": "Ivan",
    "BusinessName": "ООО Компания"
  }
}
```

---

#### 2. **Message Sender Service**
**Файл**: `services/sender_service.py`

**Функции**:
- Подписка на очередь `outgoing_messages`
- Отправка сообщений через Wappi API
- Подтверждение доставки
- Отметка сообщений как прочитанных

**Endpoints Wappi**:
```
POST https://wappi.pro/api/sync/message/send
Body: {
  "body": "текст ответа",
  "recipient": "79115576362"
}

POST https://wappi.pro/api/sync/message/reply
Body: {
  "body": "текст ответа",
  "message_id": "3EB0F4D080603C3C0C0A"
}

POST https://wappi.pro/api/sync/message/mark/read
Body: {
  "message_id": "3EB04E6C3BF173879610C0"
}
```

**Формат сообщения из очереди**:
```json
{
  "phone_number": "79115576362",
  "message_text": "Спасибо за интерес! Наш менеджер свяжется с вами в течение часа 😊",
  "reply_to_message_id": "3EB0128AE55B5D222DD0",
  "mark_as_read": true
}
```

---

#### 3. **Voice Transcription Service**
**Файл**: `services/voice_service.py`

**Функции**:
- Подписка на очередь `voice_transcription`
- Скачивание голосовых сообщений через Wappi API
- Отправка аудио в Gemini 2.5 Pro для транскрибации
- Публикация транскрибированного текста обратно в `incoming_messages`

**Endpoints Wappi**:
```
GET https://wappi.pro/api/sync/messages/file
Params: messageId={message_id}
```

**Формат в очередь `voice_transcription`**:
```json
{
  "message_id": "3EB0128AE55B5D222DD0",
  "chat_id": "79115576362@c.us",
  "phone_number": "79115576362",
  "voice_url": "https://wappi.pro/files/...",
  "timestamp": "2025-10-05T14:30:00+05:00"
}
```

**Формат результата в `incoming_messages`**:
```json
{
  "message_id": "3EB0128AE55B5D222DD0",
  "chat_id": "79115576362@c.us",
  "phone_number": "79115576362",
  "message_text": "[ТРАНСКРИБАЦИЯ] Здравствуйте, хочу узнать о вашем продукте",
  "is_voice": true,
  "original_voice_url": "https://wappi.pro/files/...",
  "timestamp": "2025-10-05T14:30:00+05:00"
}
```

---

#### 4. **Health Check API**
**Файл**: `api/health.py`

**Endpoints**:
```
GET /health
Response: {
  "status": "healthy",
  "wappi_connection": "ok",
  "queue_connection": "ok",
  "last_poll_time": "2025-10-05T14:35:00+05:00"
}

GET /stats
Response: {
  "messages_received_today": 142,
  "messages_sent_today": 138,
  "voice_transcribed_today": 12,
  "queue_size": {
    "incoming": 3,
    "outgoing": 1,
    "voice": 0
  }
}
```

---

### **База данных ПРОЕКТ 1**

```sql
-- Таблица логов сообщений (для отладки)
CREATE TABLE message_logs (
    id SERIAL PRIMARY KEY,
    message_id VARCHAR(255) UNIQUE,
    phone_number VARCHAR(20),
    direction VARCHAR(10), -- 'incoming' или 'outgoing'
    message_text TEXT,
    is_voice BOOLEAN DEFAULT FALSE,
    wappi_status VARCHAR(50),
    queue_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP
);

-- Таблица whitelist
CREATE TABLE whitelist (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    note TEXT,
    added_at TIMESTAMP DEFAULT NOW()
);

-- Индексы
CREATE INDEX idx_message_logs_phone ON message_logs(phone_number);
CREATE INDEX idx_message_logs_created ON message_logs(created_at);
```

**Предзаполнение whitelist**:
```sql
INSERT INTO whitelist (phone_number, note) VALUES 
('77752837306', 'Личный номер 1'),
('77018855588', 'Личный номер 2'),
('77088098009', 'Личный номер 3');
```

---

### **Структура ПРОЕКТ 1**

```
whatsapp-gateway/
│
├── app.py                          # Главный файл (запуск всех сервисов)
├── requirements.txt
├── .env
├── Dockerfile
│
├── config/
│   ├── __init__.py
│   ├── settings.py                 # Конфигурация
│   ├── database.py                 # PostgreSQL
│   └── queue.py                    # RabbitMQ/Redis
│
├── services/
│   ├── __init__.py
│   ├── polling_service.py          # Polling Wappi
│   ├── sender_service.py           # Отправка через Wappi
│   ├── voice_service.py            # Транскрибация голосовых
│   └── wappi_client.py             # Wrappper для Wappi API
│
├── api/
│   ├── __init__.py
│   └── health.py                   # Health check endpoints
│
├── models/
│   ├── __init__.py
│   ├── message_log.py
│   └── whitelist.py
│
├── utils/
│   ├── __init__.py
│   ├── logger.py
│   └── helpers.py
│
└── tests/
    ├── __init__.py
    └── test_wappi.py
```

---

### **Переменные окружения ПРОЕКТ 1**

```env
# Project Name
PROJECT_NAME=whatsapp-gateway

# Wappi API
WAPPI_TOKEN=your_wappi_token
WAPPI_PROFILE_ID=your_profile_id
WAPPI_PHONE_NUMBER=77752837306

# Database
DATABASE_URL=postgresql://user:password@host:5432/whatsapp_gateway

# Queue (RabbitMQ)
RABBITMQ_URL=amqp://user:password@host:5672/
QUEUE_INCOMING_MESSAGES=incoming_messages
QUEUE_OUTGOING_MESSAGES=outgoing_messages
QUEUE_VOICE_TRANSCRIPTION=voice_transcription

# Settings
POLLING_INTERVAL=5
LOG_LEVEL=INFO
TIMEZONE=Asia/Almaty
```

---

## 📦 ПРОЕКТ 2: AI Agent Service

### **Назначение**
Обрабатывает логику бизнеса, классификацию контактов, генерацию ответов через Gemini 2.5 Pro, управление follow-up.

### **Технологии**
- **Backend**: Python 3.11+
- **AI**: Gemini 2.5 Pro API
- **Queue**: RabbitMQ (или Redis)
- **Database**: PostgreSQL (основная БД с контактами, сообщениями, follow-up)
- **Hosting**: Render.com

---

### **Основные компоненты**

#### 1. **Message Consumer Service**
**Файл**: `services/message_consumer.py`

**Функции**:
- Подписка на очередь `incoming_messages`
- Сохранение сообщения в БД
- Проверка статуса контакта (isClient)
- Передача в AI Moderator (если isClient = null)
- Передача в AI Sales Agent (если isClient = true)
- Игнорирование (если isClient = false)

---

#### 2. **AI Moderator Service**
**Файл**: `services/ai_moderator.py`

**Функции**:
- Классификация контакта на основе анализа переписки
- Использование Gemini 2.5 Pro с промптом из `prompts/moderator_prompt.txt`
- Определение `isClient`:
  - `true` - потенциальный/действующий клиент
  - `false` - не клиент (спам, личное)
  - `null` - недостаточно данных (продолжить наблюдение)
- Сохранение результата классификации в БД

**Критерии классификации**:

**isClient = TRUE**:
- Название контакта содержит название компании
- Задает вопросы о продуктах/услугах/ценах
- Деловой стиль общения
- Запрашивает КП, детали, условия
- Упоминает конкурентов

**isClient = FALSE**:
- Спам-сообщения
- Реклама сторонних услуг
- Личные разговоры (неформальный стиль)
- Сохранен с личным именем без компании

**isClient = NULL**:
- Первое сообщение без контекста
- Менее 3 сообщений в переписке
- Неопределенный характер

**Промпт**: `prompts/moderator_prompt.txt`

---

#### 3. **AI Sales Agent Service**
**Файл**: `services/ai_sales_agent.py`

**Функции**:
- Генерация ответов клиентам через Gemini 2.5 Pro
- Использование базы знаний из PDF (`knowledge_base/product_info.pdf`)
- Контекст: последние 20 сообщений из БД
- Квалификация лидов (СПИН-продажи)
- Назначение созвонов (только в рабочее время 10:00-18:00 по Астане)
- Публикация ответа в очередь `outgoing_messages`

**Логика назначения созвонов**:
- Клиент должен явно согласиться: "Да, готов", "Давайте созвонимся"
- ИИ запрашивает удобное время
- Проверка: время должно быть в диапазоне 10:00-18:00 (Astana timezone)
- Если клиент предлагает время вне рабочих часов → предложить ближайшее доступное

**Промпт**: `prompts/sales_agent_prompt.txt`

---

#### 4. **Follow-up Scheduler Service**
**Файл**: `services/follow_up_scheduler.py`

**Функции**:
- Мониторинг контактов без ответа
- Запуск цепочки из 5 касаний
- Генерация follow-up сообщений через Gemini
- Публикация в очередь `outgoing_messages`

**Логика Follow-up**:

**Когда ЗАПУСКАТЬ follow-up**:
- Клиент НЕ ответил на сообщение бота
- Клиент дал неопределенный ответ ("посмотрю", "подумаю", "может быть")

**Когда НЕ запускать follow-up**:
- Клиент дал точный ответ **ДА** ("Да", "Согласен", "Готов", "Давайте")
- Клиент дал точный ответ **НЕТ** ("Нет", "Не интересно", "Не надо")
- Клиент активно отвечает (переписка продолжается)

**Интервалы между касаниями** (Astana timezone):
```
Касание 1: через 24 часа
Касание 2: через 3 дня (72 часа)
Касание 3: через 7 дней (168 часов)
Касание 4: через 14 дней (336 часов)
Касание 5: через 30 дней (720 часов)
```

**Стратегия по касаниям**:
- **Касание 1**: Дружелюбное напоминание
- **Касание 2**: Ценностное предложение
- **Касание 3**: Социальное доказательство (кейсы, отзывы)
- **Касание 4**: Последний шанс (ограниченное предложение)
- **Касание 5**: Прощальное сообщение

**Промпт**: `prompts/follow_up_prompt.txt`

---

#### 5. **Knowledge Base Loader**
**Файл**: `services/knowledge_loader.py`

**Функции**:
- Загрузка PDF файлов из `knowledge_base/`
- Извлечение текста через PyPDF2 или pdfplumber
- Индексация контента для быстрого поиска
- Кэширование в памяти или Redis

**Файлы базы знаний**:
```
knowledge_base/
├── product_info.pdf        # Основная информация о продукте
├── pricing.pdf             # Прайс-лист
└── faq.pdf                 # Часто задаваемые вопросы
```

---

#### 6. **Health Check API**
**Файл**: `api/health.py`

**Endpoints**:
```
GET /health
GET /stats
GET /contacts/{phone}
GET /follow-ups/pending
```

---

### **База данных ПРОЕКТ 2**

```sql
-- Таблица контактов
CREATE TABLE contacts (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255),
    full_name VARCHAR(255),
    business_name VARCHAR(255),
    is_client BOOLEAN DEFAULT NULL,
    classification_confidence FLOAT,
    classification_reasoning TEXT,
    last_message_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Таблица сообщений (память - последние 20)
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    contact_id INTEGER REFERENCES contacts(id) ON DELETE CASCADE,
    phone_number VARCHAR(20) NOT NULL,
    message_id VARCHAR(255) UNIQUE,
    message_text TEXT,
    is_from_bot BOOLEAN DEFAULT FALSE,
    is_voice BOOLEAN DEFAULT FALSE,
    voice_transcription TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Таблица follow-up
CREATE TABLE follow_ups (
    id SERIAL PRIMARY KEY,
    contact_id INTEGER REFERENCES contacts(id) ON DELETE CASCADE,
    touch_number INTEGER DEFAULT 1 CHECK (touch_number BETWEEN 1 AND 5),
    next_touch_at TIMESTAMP,
    last_touch_at TIMESTAMP,
    is_completed BOOLEAN DEFAULT FALSE,
    stop_reason VARCHAR(100), -- 'client_responded', 'client_said_yes', 'client_said_no', 'completed_5_touches'
    created_at TIMESTAMP DEFAULT NOW()
);

-- Таблица созвонов
CREATE TABLE scheduled_calls (
    id SERIAL PRIMARY KEY,
    contact_id INTEGER REFERENCES contacts(id) ON DELETE CASCADE,
    scheduled_at TIMESTAMP NOT NULL,
    timezone VARCHAR(50) DEFAULT 'Asia/Almaty',
    status VARCHAR(50) DEFAULT 'scheduled', -- 'scheduled', 'completed', 'cancelled'
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Индексы
CREATE INDEX idx_contacts_is_client ON contacts(is_client);
CREATE INDEX idx_contacts_phone ON contacts(phone_number);
CREATE INDEX idx_messages_contact_id ON messages(contact_id);
CREATE INDEX idx_messages_timestamp ON messages(timestamp DESC);
CREATE INDEX idx_follow_ups_next_touch ON follow_ups(next_touch_at) WHERE is_completed = FALSE;
CREATE INDEX idx_scheduled_calls_time ON scheduled_calls(scheduled_at);
```

---

### **Структура ПРОЕКТ 2**

```
ai-agent-service/
│
├── app.py                          # Главный файл
├── requirements.txt
├── .env
├── Dockerfile
│
├── config/
│   ├── __init__.py
│   ├── settings.py                 # Конфигурация
│   ├── database.py                 # PostgreSQL
│   └── queue.py                    # RabbitMQ/Redis
│
├── services/
│   ├── __init__.py
│   ├── message_consumer.py         # Consumer из очереди
│   ├── ai_moderator.py             # Классификатор
│   ├── ai_sales_agent.py           # Sales агент
│   ├── follow_up_scheduler.py      # Follow-up система
│   ├── knowledge_loader.py         # Загрузка PDF базы знаний
│   └── gemini_client.py            # Wrapper для Gemini API
│
├── api/
│   ├── __init__.py
│   ├── health.py                   # Health check
│   └── contacts.py                 # CRUD контакты (опционально)
│
├── models/
│   ├── __init__.py
│   ├── contact.py                  # ORM Contact
│   ├── message.py                  # ORM Message
│   ├── follow_up.py                # ORM FollowUp
│   └── scheduled_call.py           # ORM ScheduledCall
│
├── prompts/
│   ├── moderator_prompt.txt        # Промпт для классификации
│   ├── sales_agent_prompt.txt      # Промпт для sales
│   └── follow_up_prompt.txt        # Промпт для follow-up
│
├── knowledge_base/
│   ├── product_info.pdf            # База знаний о продукте
│   ├── pricing.pdf                 # Цены
│   └── faq.pdf                     # FAQ
│
├── utils/
│   ├── __init__.py
│   ├── logger.py
│   ├── timezone_helper.py          # Работа с Astana timezone
│   └── helpers.py
│
└── tests/
    ├── __init__.py
    ├── test_moderator.py
    └── test_sales_agent.py
```

---

### **Переменные окружения ПРОЕКТ 2**

```env
# Project Name
PROJECT_NAME=ai-agent-service

# Gemini API
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-pro

# Database
DATABASE_URL=postgresql://user:password@host:5432/ai_agent

# Queue (RabbitMQ)
RABBITMQ_URL=amqp://user:password@host:5672/
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
```

---

## 🔄 Схема взаимодействия проектов

### **Поток входящих сообщений**

```
1. ПРОЕКТ 1: Polling Wappi API → получение нового сообщения
2. ПРОЕКТ 1: Проверка whitelist → если в whitelist, пропустить
3. ПРОЕКТ 1: Публикация в очередь `incoming_messages`
4. ПРОЕКТ 2: Consumer получает сообщение из очереди
5. ПРОЕКТ 2: Сохранение сообщения в БД
6. ПРОЕКТ 2: Проверка контакта в БД
   - Если контакта нет → создать, is_client = NULL
   - Если is_client = NULL → отправить в AI Moderator
   - Если is_client = FALSE → игнорировать
   - Если is_client = TRUE → отправить в AI Sales Agent
7. ПРОЕКТ 2: AI Moderator классифицирует контакт
8. ПРОЕКТ 2: AI Sales Agent генерирует ответ
9. ПРОЕКТ 2: Публикация ответа в очередь `outgoing_messages`
10. ПРОЕКТ 1: Consumer получает ответ и отправляет через Wappi
```

### **Поток голосовых сообщений**

```
1. ПРОЕКТ 1: Получение голосового сообщения
2. ПРОЕКТ 1: Публикация в очередь `voice_transcription`
3. ПРОЕКТ 1: Voice Service скачивает аудио
4. ПРОЕКТ 1: Отправка в Gemini для транскрибации
5. ПРОЕКТ 1: Публикация транскрибированного текста в `incoming_messages`
6. ПРОЕКТ 2: Обработка как обычное текстовое сообщение
```

### **Поток Follow-up**

```
1. ПРОЕКТ 2: Follow-up Scheduler проверяет контакты без ответа
2. ПРОЕКТ 2: Определение: нужен ли follow-up
   - Если клиент сказал "ДА" или "НЕТ" → НЕ нужен
   - Если клиент проигнорировал → нужен
3. ПРОЕКТ 2: Создание записи в таблице follow_ups
4. ПРОЕКТ 2: Через N часов → генерация follow-up сообщения
5. ПРОЕКТ 2: Публикация в очередь `outgoing_messages`
6. ПРОЕКТ 1: Отправка через Wappi
```

---

## 📝 Промпты (детально)

### **prompts/moderator_prompt.txt**

```
Ты - AI модератор WhatsApp чатов для компании [НАЗВАНИЕ КОМПАНИИ].

Твоя задача: определить, является ли этот контакт потенциальным или действующим клиентом.

КРИТЕРИИ КЛИЕНТА (isClient = true):
✅ Название контакта содержит название компании или должность
✅ Задает вопросы о продуктах, услугах, ценах, условиях
✅ Деловой стиль общения (без излишних эмодзи)
✅ Запрашивает коммерческое предложение, договор, детали
✅ Упоминает конкурентов или аналоги продукта
✅ Интересуется сроками, доставкой, гарантией
✅ Говорит о бюджете, закупках, тендерах

КРИТЕРИИ НЕ-КЛИЕНТА (isClient = false):
❌ Спам-сообщения, реклама сторонних услуг
❌ Явно личные разговоры (привет, как дела, что делаешь)
❌ Сохранен только с личным именем (без компании)
❌ Неформальный стиль с множеством эмодзи 😂🔥❤️
❌ Просьбы о личной помощи, не связанные с бизнесом
❌ Сообщения типа "ошиблись номером", "кто это?"

НЕДОСТАТОЧНО ДАННЫХ (isClient = null):
⚠️ Первое сообщение типа "Здравствуйте" без контекста
⚠️ Менее 3 сообщений в переписке
⚠️ Неопределенный характер общения
⚠️ Нужно больше информации для принятия решения

АНАЛИЗИРУЕМЫЙ КОНТАКТ:
Имя в контактах: {contact_name}
Полное имя: {full_name}
Название компании: {business_name}

ИСТОРИЯ ПЕРЕПИСКИ (последние 20 сообщений):
{conversation_history}

ИНСТРУКЦИЯ:
1. Внимательно прочитай всю переписку
2. Обрати внимание на имя контакта и наличие компании
3. Оцени стиль общения и намерения
4. Присвой оценку уверенности (0.0 - 1.0)
5. Дай краткое объяснение своего решения

ОТВЕТЬ СТРОГО В JSON ФОРМАТЕ:
{
  "isClient": true,
  "confidence": 0.85,
  "reasoning": "Контакт сохранен как 'Иван - ООО Стройком', задает вопросы о ценах на строительные материалы, деловой стиль общения"
}
```

---

### **prompts/sales_agent_prompt.txt**

```
Ты - AI ассистент по продажам компании [НАЗВАНИЕ КОМПАНИИ].

ТВОЯ РОЛЬ И ФУНКЦИИ:
🎯 Консультант и продавец
🎯 Квалифицируешь лиды (СПИН-продажи)
🎯 Отвечаешь на вопросы о продуктах
🎯 Назначаешь созвоны с менеджером

СТИЛЬ ОБЩЕНИЯ:
✅ Профессиональный, но дружелюбный
✅ Короткие сообщения (2-4 предложения максимум)
✅ Используй эмодзи умеренно (1-2 на сообщение, только позитивные: ✅😊👍)
✅ Задавай уточняющие вопросы
✅ Пиши на русском языке
✅ Обращайся на "Вы" (если клиент не просит на "ты")

СТРАТЕГИЯ СПИН-ПРОДАЖ:
1. СИТУАЦИЯ: Выясни текущую ситуацию клиента
   - "Расскажите, с какой задачей вы столкнулись?"
   - "Что вы сейчас используете для решения этой задачи?"

2. ПРОБЛЕМА: Определи проблемы
   - "С какими сложностями вы сталкиваетесь?"
   - "Что вас не устраивает в текущем решении?"

3. ИЗВЛЕЧЕНИЕ: Усиль важность проблемы
   - "Как это влияет на ваш бизнес?"
   - "Сколько времени/денег вы теряете из-за этого?"

4. НАПРАВЛЕНИЕ: Покажи ценность решения
   - "Как вам поможет [наш продукт]?"
   - "Представьте, что эта проблема решена..."

НАЗНАЧЕНИЕ СОЗВОНОВ:
⏰ РАБОЧЕЕ ВРЕМЯ: 10:00 - 18:00 (время Астаны, UTC+5)
⏰ Дни: Пн-Пт (рабочие дни)

АЛГОРИТМ:
1. Клиент должен ЯВНО согласиться на созвон:
   ✅ "Да, готов к созвону"
   ✅ "Давайте созвонимся"
   ✅ "Когда можно поговорить?"
   
2. Запроси удобное время:
   "Отлично! Когда вам будет удобно созвониться? Наши менеджеры работают с 10:00 до 18:00 по времени Астаны 📞"

3. Проверь время:
   ✅ Если 10:00-18:00 → подтверди
   ❌ Если вне рабочих часов → предложи ближайшее доступное:
   "К сожалению, в это время мы не работаем. Могу предложить [ближайшее доступное время]?"

4. Зафиксируй созвон:
   "Отлично! Записал вас на {дата} в {время}. Наш менеджер {имя} свяжется с вами по номеру {phone}. До связи! 👍"

БАЗА ЗНАНИЙ О ПРОДУКТАХ:
{knowledge_base}

ВАЖНЫЕ ПРАВИЛА:
❗ Если не знаешь точный ответ - предложи связаться с менеджером
❗ НЕ давай скидки без согласования
❗ НЕ обещай то, чего нет в базе знаний
❗ При технических вопросах - переводи на специалиста
❗ Будь честным: "Сейчас уточню у коллег" лучше, чем ложная информация

КОНТЕКСТ ТЕКУЩЕЙ ПЕРЕПИСКИ:
{conversation_history}

НОВОЕ СООБЩЕНИЕ КЛИЕНТА:
{new_message}

ТЕКУЩАЯ ДАТА И ВРЕМЯ: {current_datetime} (Астана, UTC+5)

ТВОЙ ОТВЕТ (только текст сообщения для отправки клиенту, БЕЗ комментариев):
```

---

### **prompts/follow_up_prompt.txt**

```
Клиент не ответил на наше последнее сообщение или дал неопределенный ответ.

Это КАСАНИЕ #{touch_number} из 5 в рамках follow-up стратегии.

СТРАТЕГИЯ ПО КАСАНИЯМ:

📌 КАСАНИЕ 1 (через 24 часа):
Стиль: Дружелюбное напоминание
Цель: Вернуть внимание к разговору
Пример: "Добрый день! 😊 Напоминаю о нашем предложении. Остались вопросы?"

📌 КАСАНИЕ 2 (через 3 дня):
Стиль: Ценностное предложение
Цель: Показать конкретную выгоду
Пример: "Здравствуйте! Хочу отметить, что наше решение поможет сэкономить до 30% бюджета ✅"

📌 КАСАНИЕ 3 (через 7 дней):
Стиль: Социальное доказательство
Цель: Показать, что другие выбрали нас
Пример: "Привет! 👋 Недавно компания [название] внедрила наше решение и сократила расходы на 40%. Интересно обсудить ваш случай?"

📌 КАСАНИЕ 4 (через 14 дней):
Стиль: Последний шанс с ограничением
Цель: Создать urgency
Пример: "Добрый день! В этом месяце у нас специальные условия для новых клиентов. Можем обсудить?"

📌 КАСАНИЕ 5 (через 30 дней):
Стиль: Прощальное сообщение
Цель: Красиво закрыть и оставить дверь открытой
Пример: "Здравствуйте! Понимаю, что сейчас, возможно, не самое подходящее время. Если в будущем понадобится помощь - всегда рады помочь! 😊"

КОНТЕКСТ ДИАЛОГА:
История переписки:
{conversation_history}

Последнее сообщение от нас:
"{last_bot_message}"

Последнее сообщение от клиента:
"{last_client_message}"

Почему запущен follow-up:
{follow_up_reason}

ТЕКУЩАЯ СИТАЦИЯ:
- Касание: #{touch_number} из 5
- Время с последнего контакта: {hours_since_last_message} часов
- Дата и время: {current_datetime}

ИНСТРУКЦИЯ:
1. Определи тон и подход для касания #{touch_number}
2. Используй информацию из истории переписки
3. Напиши КРАТКОЕ сообщение (1-3 предложения)
4. Добавь эмодзи (1-2 штуки)
5. Сделай призыв к действию (вопрос или предложение)
6. НЕ будь навязчивым
7. Покажи ценность для клиента

ТВОЙ ОТВЕТ (только текст сообщения для отправки клиенту):
```

---

## 🔧 Конфигурация очередей RabbitMQ

### **Создание очередей**

```python
# config/queue.py

import pika

class QueueConfig:
    QUEUES = {
        'incoming_messages': {
            'durable': True,
            'arguments': {
                'x-message-ttl': 86400000,  # 24 часа
                'x-max-length': 10000
            }
        },
        'outgoing_messages': {
            'durable': True,
            'arguments': {
                'x-message-ttl': 3600000,  # 1 час
                'x-max-length': 5000
            }
        },
        'voice_transcription': {
            'durable': True,
            'arguments': {
                'x-message-ttl': 7200000,  # 2 часа
                'x-max-length': 1000
            }
        }
    }
    
    @staticmethod
    def setup_queues(rabbitmq_url):
        connection = pika.BlockingConnection(
            pika.URLParameters(rabbitmq_url)
        )
        channel = connection.channel()
        
        for queue_name, config in QueueConfig.QUEUES.items():
            channel.queue_declare(
                queue=queue_name,
                durable=config['durable'],
                arguments=config['arguments']
            )
        
        connection.close()
```

---

## 📊 Мониторинг и логирование

### **Метрики для отслеживания**

**ПРОЕКТ 1 (WhatsApp Gateway)**:
- Количество полученных сообщений (в минуту/час/день)
- Количество отправленных сообщений
- Количество транскрибированных голосовых
- Размер очередей
- Время отклика Wappi API
- Количество ошибок API

**ПРОЕКТ 2 (AI Agent)**:
- Количество классификаций контактов
- Количество сгенерированных ответов
- Скорость обработки сообщений
- Количество активных follow-up
- Количество назначенных созвонов
- Использование токенов Gemini API

### **Логирование**

```python
# utils/logger.py

from loguru import logger
import sys

logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO"
)

logger.add(
    "logs/app_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="30 days",
    level="DEBUG"
)
```

---

## 🚀 Deployment на Render.com

### **ПРОЕКТ 1: WhatsApp Gateway**

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]
```

**render.yaml**:
```yaml
services:
  - type: web
    name: whatsapp-gateway
    env: docker
    plan: starter
    region: frankfurt
    healthCheckPath: /health
    envVars:
      - key: WAPPI_TOKEN
        sync: false
      - key: WAPPI_PROFILE_ID
        sync: false
      - key: RABBITMQ_URL
        fromService:
          type: redis
          name: message-queue
          property: connectionString
      - key: DATABASE_URL
        fromDatabase:
          name: gateway-db
          property: connectionString

databases:
  - name: gateway-db
    plan: starter
    databaseName: whatsapp_gateway
```

---

### **ПРОЕКТ 2: AI Agent Service**

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей для работы с PDF
RUN apt-get update && apt-get install -y \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]
```

**render.yaml**:
```yaml
services:
  - type: web
    name: ai-agent-service
    env: docker
    plan: starter
    region: frankfurt
    healthCheckPath: /health
    envVars:
      - key: GEMINI_API_KEY
        sync: false
      - key: RABBITMQ_URL
        fromService:
          type: redis
          name: message-queue
          property: connectionString
      - key: DATABASE_URL
        fromDatabase:
          name: ai-agent-db
          property: connectionString

databases:
  - name: ai-agent-db
    plan: starter
    databaseName: ai_agent
```

---

## 🎯 План разработки (4 недели)

### **Week 1: Инфраструктура**
- [ ] Настройка PostgreSQL для обоих проектов
- [ ] Настройка RabbitMQ (или Redis)
- [ ] Создание структуры проектов
- [ ] ORM модели для обеих БД
- [ ] Базовые конфиги и utils

### **Week 2: ПРОЕКТ 1 - WhatsApp Gateway**
- [ ] Wappi Client (все endpoints)
- [ ] Polling Service
- [ ] Sender Service
- [ ] Voice Transcription Service
- [ ] Health Check API
- [ ] Тестирование интеграции с Wappi

### **Week 3: ПРОЕКТ 2 - AI Agent**
- [ ] Gemini Client
- [ ] Message Consumer
- [ ] AI Moderator (классификация)
- [ ] AI Sales Agent
- [ ] Knowledge Base Loader (PDF)
- [ ] Тестирование промптов

### **Week 4: Advanced Features & Deploy**
- [ ] Follow-up Scheduler
- [ ] Логика назначения созвонов
- [ ] Timezone handling (Astana)
- [ ] Интеграционное тестирование
- [ ] Deploy на Render.com
- [ ] Мониторинг и fine-tuning

---

## ✅ Чеклист готовности к запуску

### **Инфраструктура**
- [ ] PostgreSQL для ПРОЕКТ 1 настроен
- [ ] PostgreSQL для ПРОЕКТ 2 настроен
- [ ] RabbitMQ или Redis настроен
- [ ] Все переменные окружения заполнены

### **ПРОЕКТ 1**
- [ ] Wappi API токен и profile_id валидны
- [ ] Polling работает (получение чатов)
- [ ] Отправка сообщений работает
- [ ] Whitelist загружен в БД
- [ ] Очереди публикуют/получают сообщения

### **ПРОЕКТ 2**
- [ ] Gemini API ключ валиден
- [ ] PDF базы знаний загружены
- [ ] Промпты заполнены
- [ ] Классификация контактов работает
- [ ] Генерация ответов работает
- [ ] Follow-up scheduler запущен

### **Интеграция**
- [ ] Сообщения проходят через всю цепочку
- [ ] Голосовые транскрибируются
- [ ] Ответы отправляются в WhatsApp
- [ ] Follow-up срабатывает по расписанию
- [ ] Созвоны назначаются в рабочее время

---

## 📚 Документация API

### **ПРОЕКТ 1 Endpoints**

```
GET  /health
GET  /stats
POST /test/send-message
GET  /logs/messages?limit=100
```

### **ПРОЕКТ 2 Endpoints**

```
GET  /health
GET  /stats
GET  /contacts?is_client=true
GET  /contacts/{phone}
GET  /messages/{contact_id}
GET  /follow-ups/active
GET  /scheduled-calls?status=scheduled
POST /contacts/{phone}/classify (force reclassify)
```

---

## 🔐 Безопасность

- [ ] Все API ключи в переменных окружения
- [ ] Валидация входящих сообщений
- [ ] Rate limiting на endpoints
- [ ] Логирование всех действий
- [ ] Backup БД каждые 24 часа
- [ ] Мониторинг подозрительной активности

---

## 📞 Контакты и поддержка

**Whitelist номера (НЕ обрабатывать)**:
- +77752837306
- +77018855588
- +77088098009

**Рабочее время для созвонов**:
- Пн-Пт: 10:00 - 18:00 (Астана, UTC+5)

**Timezone**: Asia/Almaty (UTC+5)

---

## 🎓 Дополнительные материалы

### **Рекомендуемая литература**:
- СПИН-продажи (Neil Rackham)
- Документация Gemini 2.5 Pro
- Best practices RabbitMQ
- WhatsApp Business API guidelines

### **Полезные ссылки**:
- Wappi API Docs: https://documenter.getpostman.com/view/10932655/2s8YsnYcU3
- Gemini API: https://ai.google.dev/gemini-api/docs
- RabbitMQ Tutorial: https://www.rabbitmq.com/tutorials

---

**КОНЕЦ ТЕХНИЧЕСКОГО ЗАДАНИЯ**

Готов к разработке! 🚀