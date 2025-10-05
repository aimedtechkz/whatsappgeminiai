# 📋 ПЛАН ЗАДАЧ ДЛЯ РАЗРАБОТЧИКА: WhatsApp AI Agent System

## 🎯 О документе

**Назначение**: Пошаговый план разработки системы WhatsApp AI Agent  
**Для кого**: Backend разработчик Python  
**Срок выполнения**: 4 недели  
**Архитектура**: 2 независимых проекта + очереди сообщений

---

## 📊 WEEK 1: Инфраструктура и базовая настройка

### **День 1-2: Настройка окружения и баз данных**

#### Задача 1.1: Создать PostgreSQL базы данных
- Зарегистрироваться на Render.com
- Создать две PostgreSQL базы:
  - `whatsapp_gateway` - для ПРОЕКТ 1
  - `ai_agent` - для ПРОЕКТ 2
- Записать connection strings в безопасное место
- Проверить подключение к обеим БД через psql или DBeaver

#### Задача 1.2: Настроить RabbitMQ/Redis
- Выбрать сервис очередей: RabbitMQ (рекомендуется) или Redis
- Развернуть RabbitMQ на CloudAMQP (бесплатный план) или Redis на Render
- Создать три очереди:
  - `incoming_messages` (TTL: 24 часа, max length: 10000)
  - `outgoing_messages` (TTL: 1 час, max length: 5000)
  - `voice_transcription` (TTL: 2 часа, max length: 1000)
- Записать URL подключения
- Проверить подключение через RabbitMQ Management UI

#### Задача 1.3: Получить API ключи
- Зарегистрироваться на Wappi.pro
- Получить токен авторизации (Token)
- Получить profile_id из личного кабинета
- Записать номер WhatsApp: +77752837306
- Протестировать API через Postman (отправить тестовое сообщение)
- Зарегистрироваться на Google AI Studio
- Получить Gemini API ключ
- Протестировать запрос к Gemini 2.5 Pro через curl или Postman

---

### **День 3-4: Структура проектов и ORM модели**

#### Задача 1.4: Создать структуру ПРОЕКТ 1 (WhatsApp Gateway)
- Создать репозиторий Git: `whatsapp-gateway`
- Создать структуру папок:
  - `config/` - конфигурация
  - `services/` - бизнес-логика
  - `models/` - ORM модели
  - `api/` - REST endpoints
  - `utils/` - утилиты
  - `tests/` - тесты
- Создать `requirements.txt` со всеми зависимостями
- Создать `.env.example` с шаблоном переменных окружения
- Создать `.gitignore` (исключить .env, __pycache__, logs/)
- Создать `README.md` с инструкцией по запуску

#### Задача 1.5: Создать структуру ПРОЕКТ 2 (AI Agent)
- Создать репозиторий Git: `ai-agent-service`
- Создать структуру папок:
  - `config/` - конфигурация
  - `services/` - AI сервисы
  - `models/` - ORM модели
  - `api/` - REST endpoints
  - `prompts/` - текстовые промпты
  - `knowledge_base/` - PDF файлы
  - `utils/` - утилиты
  - `tests/` - тесты
- Создать `requirements.txt` со всеми зависимостями
- Создать `.env.example`
- Создать `.gitignore`
- Создать `README.md`

#### Задача 1.6: Создать ORM модели для ПРОЕКТ 1
- Установить SQLAlchemy и psycopg2-binary
- Создать файл `config/database.py`:
  - Настроить подключение к PostgreSQL
  - Создать Base для декларативных моделей
  - Настроить session factory
- Создать модель `models/message_log.py`:
  - Поля: id, message_id, phone_number, direction, message_text, is_voice, wappi_status, queue_status, created_at, processed_at
  - Индексы: по phone_number и created_at
- Создать модель `models/whitelist.py`:
  - Поля: id, phone_number, note, added_at
  - Unique constraint на phone_number
- Создать миграционный скрипт для создания таблиц
- Применить миграции к БД
- Предзаполнить whitelist тремя номерами: +77752837306, +77018855588, +77088098009

#### Задача 1.7: Создать ORM модели для ПРОЕКТ 2
- Установить SQLAlchemy и psycopg2-binary
- Создать файл `config/database.py` с подключением к БД
- Создать модель `models/contact.py`:
  - Поля: id, phone_number, name, full_name, business_name, is_client, classification_confidence, classification_reasoning, last_message_at, created_at, updated_at
  - Индексы: по phone_number и is_client
  - Unique constraint на phone_number
- Создать модель `models/message.py`:
  - Поля: id, contact_id (FK), phone_number, message_id, message_text, is_from_bot, is_voice, voice_transcription, timestamp
  - Индексы: по contact_id и timestamp (DESC)
  - Cascade delete при удалении контакта
- Создать модель `models/follow_up.py`:
  - Поля: id, contact_id (FK), touch_number (1-5), next_touch_at, last_touch_at, is_completed, stop_reason, created_at
  - Check constraint: touch_number BETWEEN 1 AND 5
  - Индекс: по next_touch_at где is_completed = FALSE
- Создать модель `models/scheduled_call.py`:
  - Поля: id, contact_id (FK), scheduled_at, timezone, status, notes, created_at
  - Индекс: по scheduled_at
- Создать миграции и применить к БД

---

### **День 5-7: Базовые сервисы и конфигурация**

#### Задача 1.8: Настроить конфигурацию для обоих проектов
- В ПРОЕКТ 1 создать `config/settings.py`:
  - Загрузка переменных окружения через python-dotenv
  - Валидация обязательных переменных (WAPPI_TOKEN, RABBITMQ_URL, DATABASE_URL)
  - Константы: POLLING_INTERVAL=5, TIMEZONE='Asia/Almaty'
- В ПРОЕКТ 2 создать `config/settings.py`:
  - Загрузка переменных окружения
  - Валидация GEMINI_API_KEY, RABBITMQ_URL, DATABASE_URL
  - Константы: MAX_CONTEXT_MESSAGES=20, WORKING_HOURS_START=10, WORKING_HOURS_END=18
  - Парсинг FOLLOW_UP_INTERVALS="24,72,168,336,720" в список чисел

#### Задача 1.9: Создать модуль работы с очередями для ПРОЕКТ 1
- Создать файл `config/queue.py`
- Реализовать класс QueueManager:
  - Метод подключения к RabbitMQ/Redis
  - Метод публикации сообщения в очередь (принимает имя очереди и dict сообщения)
  - Метод подписки на очередь (callback функция)
  - Метод проверки размера очереди
  - Обработка ошибок подключения с повторными попытками
- Создать singleton инстанс для переиспользования подключения
- Добавить graceful shutdown при SIGTERM/SIGINT

#### Задача 1.10: Создать модуль работы с очередями для ПРОЕКТ 2
- Создать файл `config/queue.py` (идентичный ПРОЕКТ 1)
- Реализовать класс QueueManager с теми же методами
- Настроить prefetch_count=1 для равномерного распределения нагрузки
- Добавить логирование всех операций с очередью

#### Задача 1.11: Настроить логирование
- В обоих проектах создать `utils/logger.py`
- Настроить loguru:
  - Вывод в консоль с цветным форматированием
  - Запись в файл `logs/app_{date}.log` с ротацией (каждый день)
  - Хранение логов 30 дней
  - Уровни: DEBUG для разработки, INFO для продакшена
- Создать helper функции:
  - `log_incoming_message(message_data)`
  - `log_outgoing_message(message_data)`
  - `log_error(service_name, error, context)`
  - `log_queue_operation(operation, queue_name, data)`

#### Задача 1.12: Создать утилиты для работы с timezone
- В ПРОЕКТ 2 создать `utils/timezone_helper.py`
- Установить библиотеку pytz
- Реализовать функции:
  - `get_current_time_astana()` - возвращает текущее время в timezone Asia/Almaty
  - `is_working_hours(datetime_obj)` - проверяет, находится ли время в диапазоне 10:00-18:00
  - `get_next_working_time(datetime_obj)` - если время вне рабочих часов, возвращает следующее доступное (10:00 следующего рабочего дня)
  - `is_working_day(datetime_obj)` - проверка, что это не выходной (Пн-Пт)
  - `format_datetime_for_user(datetime_obj)` - форматирование для отображения клиенту: "15 октября в 14:30"

---

## 📊 WEEK 2: ПРОЕКТ 1 - WhatsApp Gateway Service

### **День 8-9: Wappi API клиент**

#### Задача 2.1: Создать Wappi API client wrapper
- Создать файл `services/wappi_client.py`
- Установить библиотеку requests
- Реализовать класс WappiClient с методами:
  - `__init__()` - инициализация с токеном и profile_id из settings
  - `get_chats(limit=100, offset=0, show_all=False)` - получение списка чатов
  - `send_message(recipient, body)` - отправка обычного сообщения
  - `reply_to_message(message_id, body)` - ответ на конкретное сообщение
  - `mark_as_read(message_id, mark_all=False)` - отметка прочитанным
  - `get_message_file(message_id)` - скачивание файла (для голосовых)
- Для каждого метода:
  - Добавить обработку HTTP ошибок (400, 401, 429, 500)
  - Логировать запросы и ответы
  - Добавить retry механизм (3 попытки с exponential backoff)
  - Валидировать обязательные параметры
- Создать метод `_make_request(method, endpoint, params, data)` для переиспользования логики
- Добавить timeout для всех запросов (30 секунд)

#### Задача 2.2: Тестирование Wappi клиента
- Создать файл `tests/test_wappi.py`
- Написать unit-тесты:
  - Тест успешной отправки сообщения (mock responses)
  - Тест обработки 429 ошибки (rate limit)
  - Тест обработки 500 ошибки с retry
  - Тест валидации параметров (пустой recipient)
- Написать integration тест:
  - Реальная отправка тестового сообщения на свой номер
  - Проверка получения чатов
  - Проверка отметки как прочитанного
- Запустить тесты и убедиться, что все проходят

---

### **День 10-11: Polling Service**

#### Задача 2.3: Реализовать Message Polling Service
- Создать файл `services/polling_service.py`
- Реализовать класс MessagePollingService:
  - `__init__()` - инициализация WappiClient, QueueManager, подключение к БД
  - `start_polling()` - основной асинхронный цикл
  - `process_chats()` - получение всех чатов через WappiClient
  - `extract_new_messages(dialog)` - извлечение новых сообщений из диалога
  - `is_in_whitelist(phone_number)` - проверка номера в whitelist из БД
  - `publish_to_queue(message_data)` - публикация в очередь incoming_messages
- Логика работы:
  - Каждые 5 секунд вызывать get_chats(limit=100)
  - Для каждого диалога в ответе:
    - Извлечь phone_number из chat_id (убрать "@c.us")
    - Проверить whitelist - если номер в списке, пропустить
    - Извлечь информацию о контакте (FirstName, FullName, BusinessName)
    - Получить последнее сообщение из диалога
    - Проверить, обрабатывалось ли это сообщение (проверка message_id в message_logs)
    - Если новое - сформировать dict с данными
    - Сохранить в message_logs со статусом 'queued'
    - Опубликовать в очередь incoming_messages
- Обработка голосовых сообщений:
  - Определять тип сообщения (is_voice = true если есть audio)
  - Для голосовых публиковать в очередь voice_transcription
- Обработка ошибок:
  - При ошибке API продолжить работу, не останавливать polling
  - Логировать все ошибки с контекстом
  - При потере соединения с очередью - пытаться переподключиться

#### Задача 2.4: Настроить запуск polling как фоновой задачи
- Установить библиотеку asyncio
- Создать главный файл `app.py` для ПРОЕКТ 1:
  - Импортировать MessagePollingService
  - Создать async main() функцию
  - Запустить polling_service.start_polling() в бесконечном цикле
  - Добавить обработку SIGTERM для graceful shutdown
- Протестировать локально:
  - Запустить app.py
  - Проверить, что чаты получаются каждые 5 секунд
  - Проверить, что сообщения попадают в очередь
  - Проверить логи на наличие ошибок

---

### **День 12-13: Sender Service**

#### Задача 2.5: Реализовать Message Sender Service
- Создать файл `services/sender_service.py`
- Реализовать класс MessageSenderService:
  - `__init__()` - инициализация WappiClient, QueueManager, БД
  - `start_consuming()` - подписка на очередь outgoing_messages
  - `process_outgoing_message(message_data)` - обработка одного сообщения
  - `send_via_wappi(phone, text, reply_to_id)` - отправка через Wappi
  - `mark_message_as_sent(message_id)` - обновление статуса в БД
- Логика обработки:
  - Получить сообщение из очереди outgoing_messages
  - Извлечь данные: phone_number, message_text, reply_to_message_id (опционально)
  - Если есть reply_to_message_id - использовать reply_to_message(), иначе send_message()
  - Если в сообщении флаг mark_as_read=true - вызвать mark_as_read()
  - Сохранить в message_logs со статусом 'sent' и direction='outgoing'
  - Подтвердить обработку сообщения в очереди (ack)
- Обработка ошибок:
  - При неудаче отправки - повторить 3 раза
  - После 3 неудач - переместить в dead-letter queue или логировать
  - Не ломать весь сервис при ошибке одного сообщения
- Добавить throttling:
  - Не отправлять более 20 сообщений в минуту (ограничение Wappi)
  - Использовать sleep между отправками

#### Задача 2.6: Интеграция Sender в app.py
- Обновить `app.py` ПРОЕКТ 1:
  - Импортировать MessageSenderService
  - Запустить sender_service.start_consuming() параллельно с polling
  - Использовать asyncio.gather() для запуска обоих сервисов
- Протестировать end-to-end:
  - Вручную добавить сообщение в очередь outgoing_messages
  - Проверить, что сообщение отправилось в WhatsApp
  - Проверить логи и БД на корректность статусов

---

### **День 14: Voice Transcription Service**

#### Задача 2.7: Реализовать Voice Transcription Service
- Создать файл `services/voice_service.py`
- Установить библиотеку для работы с Gemini: google-genai
- Реализовать класс VoiceTranscriptionService:
  - `__init__()` - инициализация WappiClient, Gemini client, QueueManager
  - `start_consuming()` - подписка на очередь voice_transcription
  - `process_voice_message(message_data)` - обработка одного голосового
  - `download_audio(message_id)` - скачивание файла через Wappi API
  - `transcribe_with_gemini(audio_bytes)` - транскрибация через Gemini
  - `publish_transcription(original_data, transcription)` - публикация обратно в incoming_messages
- Логика транскрибации:
  - Получить message_data из очереди voice_transcription
  - Скачать аудио файл через wappi_client.get_message_file()
  - Конвертировать в base64 если нужно
  - Отправить в Gemini 2.5 Pro с промптом: "Транскрибируй это голосовое сообщение на русском языке:"
  - Получить текст транскрипции
  - Сформировать новое сообщение с префиксом "[ТРАНСКРИБАЦИЯ]"
  - Опубликовать в очередь incoming_messages с флагом is_voice=true
- Обработка ошибок:
  - Если не удалось скачать - логировать и пропустить
  - Если Gemini вернул ошибку - повторить 2 раза
  - Сохранять статус в БД
- Оптимизация:
  - Кэшировать аудио файлы временно (удалять после обработки)
  - Логировать время транскрибации для мониторинга

#### Задача 2.8: Добавить Voice Service в app.py
- Обновить `app.py`:
  - Импортировать VoiceTranscriptionService
  - Добавить в asyncio.gather() третий сервис
- Протестировать:
  - Отправить голосовое сообщение на номер бота
  - Проверить, что оно попало в очередь voice_transcription
  - Проверить, что транскрипция появилась в incoming_messages
  - Проверить точность транскрипции на русском языке

---

### **День 14: Health Check API**

#### Задача 2.9: Создать Health Check endpoints
- Установить FastAPI и uvicorn
- Создать файл `api/health.py`
- Реализовать endpoints:
  - `GET /health` - статус сервиса (healthy/unhealthy)
    - Проверить подключение к PostgreSQL
    - Проверить подключение к RabbitMQ
    - Проверить доступность Wappi API (ping)
    - Вернуть время последнего успешного polling
  - `GET /stats` - статистика за сегодня
    - Посчитать messages_received_today из message_logs
    - Посчитать messages_sent_today
    - Посчитать voice_transcribed_today
    - Получить размер каждой очереди
- Добавить CORS middleware для доступа из браузера
- Запустить FastAPI на порту 8000 параллельно с основными сервисами

#### Задача 2.10: Финальное тестирование ПРОЕКТ 1
- Проверить все компоненты работают вместе:
  - Polling получает сообщения
  - Voice транскрибируются
  - Сообщения из outgoing отправляются
  - Whitelist корректно фильтрует
- Нагрузочное тестирование:
  - Отправить 50 сообщений подряд
  - Проверить, что все обработались
  - Проверить потребление памяти
- Проверить логи на warning/error
- Задокументировать найденные баги

---

## 📊 WEEK 3: ПРОЕКТ 2 - AI Agent Service

### **День 15-16: Gemini Client и Knowledge Base**

#### Задача 3.1: Создать Gemini API client wrapper
- Создать файл `services/gemini_client.py`
- Установить google-genai
- Реализовать класс GeminiClient:
  - `__init__()` - инициализация с API ключом из settings
  - `generate_response(system_prompt, conversation_history, temperature=0.7)` - генерация ответа с контекстом
  - `classify_json(prompt, temperature=0.1)` - классификация с JSON response
  - `transcribe_audio(audio_bytes, mime_type)` - транскрибация (для Voice Service)
- Для метода generate_response:
  - Принимать список словарей с ролями: [{"role": "user", "parts": [{"text": "..."}]}]
  - Настроить GenerateContentConfig с system_instruction
  - Обрабатывать ответ и возвращать только текст
  - Логировать использование токенов
- Для метода classify_json:
  - Настроить response_mime_type="application/json"
  - Парсить JSON ответ
  - Валидировать структуру (должен содержать isClient, confidence, reasoning)
- Обработка ошибок:
  - Rate limit (429) - ждать и повторить
  - Quota exceeded - логировать critical error
  - Invalid API key - завершить работу сервиса
- Добавить retry механизм для всех методов

#### Задача 3.2: Реализовать Knowledge Base Loader
- Создать файл `services/knowledge_loader.py`
- Установить PyPDF2 и pdfplumber
- Реализовать класс KnowledgeBaseLoader:
  - `__init__()` - указать путь к папке knowledge_base/
  - `load_all_pdfs()` - загрузка всех PDF файлов из папки
  - `extract_text_from_pdf(file_path)` - извлечение текста из PDF
  - `index_content()` - создание простого индекса для быстрого поиска
  - `search_knowledge(query)` - поиск релевантной информации
  - `get_full_knowledge()` - получение всей базы знаний как строка
- Логика extract_text:
  - Попробовать pdfplumber сначала (лучше для таблиц)
  - Если не получилось - использовать PyPDF2
  - Очистить текст от лишних символов
  - Сохранить структуру (заголовки, параграфы)
- Оптимизация:
  - Кэшировать загруженные PDF в памяти или Redis
  - При запуске сервиса загрузить все PDF один раз
  - Обновлять кэш только при изменении файлов

#### Задача 3.3: Подготовить промпты
- Создать файл `prompts/moderator_prompt.txt`:
  - Скопировать текст промпта из ТЗ
  - Добавить плейсхолдеры: {contact_name}, {full_name}, {business_name}, {conversation_history}
  - Проверить корректность JSON структуры в примере
- Создать файл `prompts/sales_agent_prompt.txt`:
  - Скопировать текст промпта из ТЗ
  - Добавить плейсхолдеры: {knowledge_base}, {conversation_history}, {new_message}, {current_datetime}
  - Убедиться, что логика СПИН-продаж понятно описана
- Создать файл `prompts/follow_up_prompt.txt`:
  - Скопировать текст промпта из ТЗ
  - Добавить плейсхолдеры: {touch_number}, {conversation_history}, {last_bot_message}, {last_client_message}, {follow_up_reason}, {hours_since_last_message}, {current_datetime}
  - Проверить стратегию для каждого касания (1-5)

#### Задача 3.4: Подготовить PDF базы знаний
- Создать папку `knowledge_base/`
- Поместить туда PDF файлы с информацией о продукте (получить от заказчика)
- Если файлов пока нет - создать временный product_info.pdf с тестовыми данными:
  - Название продукта/услуги
  - Описание
  - Цены
  - Условия
  - Преимущества
  - FAQ
- Протестировать загрузку:
  - Запустить knowledge_loader.load_all_pdfs()
  - Проверить, что текст извлекается корректно
  - Проверить кириллицу (русский язык)

---

### **День 17-18: Message Consumer и AI Moderator**

#### Задача 3.5: Создать Message Consumer Service
- Создать файл `services/message_consumer.py`
- Реализовать класс MessageConsumerService:
  - `__init__()` - инициализация QueueManager, БД, AI Moderator, AI Sales Agent
  - `start_consuming()` - подписка на очередь incoming_messages
  - `process_incoming_message(message_data)` - обработка одного сообщения
  - `get_or_create_contact(phone, contact_info)` - получение/создание контакта в БД
  - `save_message(contact_id, message_data)` - сохранение сообщения в БД
  - `route_to_handler(contact, message)` - маршрутизация по is_client
- Логика обработки:
  - Получить message из очереди
  - Извлечь phone_number и contact_info
  - Найти контакт в БД или создать новый (is_client=NULL)
  - Сохранить сообщение в таблицу messages
  - Проверить is_client контакта:
    - NULL → передать в AI Moderator для классификации
    - FALSE → логировать и пропустить (не отвечать)
    - TRUE → передать в AI Sales Agent для генерации ответа
  - Обновить last_message_at у контакта
  - Подтвердить обработку в очереди (ack)

#### Задача 3.6: Реализовать AI Moderator Service
- Создать файл `services/ai_moderator.py`
- Реализовать класс AIModeratorService:
  - `__init__()` - инициализация GeminiClient, БД
  - `classify_contact(contact_id)` - основной метод классификации
  - `get_conversation_history(contact_id, limit=20)` - получение последних 20 сообщений
  - `format_conversation_for_prompt(messages)` - форматирование в строку
  - `parse_classification_result(json_result)` - парсинг JSON от Gemini
  - `save_classification(contact_id, is_client, confidence, reasoning)` - сохранение в БД
- Логика классификации:
  - Загрузить промпт из prompts/moderator_prompt.txt
  - Получить последние 20 сообщений контакта из БД
  - Получить информацию о контакте (name, full_name, business_name)
  - Заполнить плейсхолдеры в промпте:
    - {contact_name} → contact.name
    - {full_name} → contact.full_name
    - {business_name} → contact.business_name
    - {conversation_history} → отформатированная история
  - Отправить промпт в Gemini через classify_json()
  - Распарсить JSON ответ
  - Извлечь: isClient (true/false/null), confidence (0.0-1.0), reasoning (строка)
  - Сохранить результат в таблицу contacts
  - Логировать решение с reasoning для отладки
- Валидация ответа:
  - Проверить, что isClient имеет корректное значение (true/false/null)
  - Проверить, что confidence в диапазоне 0-1
  - Если JSON невалидный - повторить запрос или вернуть null

#### Задача 3.7: Интеграция Moderator в Consumer
- Обновить `message_consumer.py`:
  - После сохранения сообщения проверить is_client контакта
  - Если is_client = NULL и сообщений >= 3:
    - Вызвать moderator.classify_contact(contact_id)
    - Получить обновленное значение is_client
    - Если теперь TRUE - передать в Sales Agent
- Протестировать:
  - Создать тестовый контакт с 3 сообщениями
  - Проверить, что классификация срабатывает
  - Проверить разные сценарии (клиент/не клиент/неопределенно)

---

### **День 19-20: AI Sales Agent**

#### Задача 3.8: Реализовать AI Sales Agent Service
- Создать файл `services/ai_sales_agent.py`
- Реализовать класс AISalesAgentService:
  - `__init__()` - инициализация GeminiClient, KnowledgeBaseLoader, QueueManager, БД
  - `generate_response(contact_id, new_message)` - основной метод генерации
  - `get_conversation_context(contact_id, limit=20)` - получение контекста
  - `format_context_for_gemini(messages)` - форматирование в структуру Gemini
  - `check_for_call_scheduling(response_text, contact)` - проверка упоминания созвона
  - `schedule_call(contact_id, datetime_str)` - создание записи в scheduled_calls
  - `publish_response(phone_number, response_text, reply_to_id)` - публикация в outgoing
- Логика генерации ответа:
  - Загрузить промпт из prompts/sales_agent_prompt.txt
  - Получить последние 20 сообщений контакта
  - Загрузить базу знаний через knowledge_loader.get_full_knowledge()
  - Получить текущую дату/время в Астане
  - Заполнить плейсхолдеры:
    - {knowledge_base} → полная база знаний
    - {conversation_history} → история в формате Gemini
    - {new_message} → текст нового сообщения
    - {current_datetime} → "5 октября 2025, 14:30 (время Астаны)"
  - Сформировать conversation history для Gemini:
    - Преобразовать сообщения в формат [{"role": "user/model", "parts": [{"text": "..."}]}]
  - Вызвать gemini_client.generate_response() с system_prompt и историей
  - Получить текст ответа
  - Сохранить ответ в messages с is_from_bot=True
  - Проверить, есть ли упоминание созвона в ответе
  - Опубликовать ответ в очередь outgoing_messages
- Обработка созвонов:
  - Парсить текст ответа на ключевые фразы: "записал на", "созвонимся", "позвоним"
  - Извлечь дату и время упоминаемого созвона
  - Проверить через timezone_helper.is_working_hours()
  - Если время рабочее - создать запись в scheduled_calls
  - Если время нерабочее - это ошибка промпта (не должно происходить)

#### Задача 3.9: Интеграция Sales Agent в Consumer
- Обновить `message_consumer.py`:
  - В методе route_to_handler() для is_client=TRUE:
    - Вызвать sales_agent.generate_response(contact, message)
- Тестирование:
  - Создать тестовый контакт с is_client=TRUE
  - Отправить сообщение "Сколько стоит ваш продукт?"
  - Проверить, что ответ сгенерировался
  - Проверить, что ответ попал в очередь outgoing_messages
  - Проверить, что ответ отправился через ПРОЕКТ 1
- Проверка качества ответов:
  - Отправить 10 разных вопросов
  - Оценить релевантность ответов
  - Проверить использование базы знаний
  - Проверить стиль общения (эмодзи, длина)

#### Задача 3.10: Тестирование созвонов
- Отправить сообщение "Хочу созвониться"
- Проверить ответ бота (должен спросить удобное время)
- Ответить "Завтра в 15:00"
- Проверить:
  - Бот подтвердил созвон
  - Запись создалась в scheduled_calls
  - Время попадает в рабочие часы (10-18)
- Протестировать нерабочее время:
  - Ответить "Завтра в 20:00"
  - Проверить, что бот предложил альтернативное время

---

### **День 21: Follow-up Scheduler**

#### Задача 3.11: Реализовать Follow-up Scheduler Service
- Создать файл `services/follow_up_scheduler.py`
- Реализовать класс FollowUpSchedulerService:
  - `__init__()` - инициализация GeminiClient, QueueManager, БД, timezone helper
  - `start_scheduler()` - основной цикл проверки
  - `check_contacts_for_followup()` - поиск контактов нуждающихся в follow-up
  - `should_start_followup(contact)` - логика определения нужен ли follow-up
  - `analyze_last_response(message_text)` - анализ ответа клиента (ДА/НЕТ/неопределенно)
  - `create_followup_chain(contact_id)` - создание цепочки касаний
  - `generate_followup_message(contact_id, touch_number)` - генерация сообщения
  - `send_followup(contact_id, message_text)` - отправка через очередь
- Логика определения follow-up:
  - Каждую минуту проверять контакты где:
    - is_client = TRUE
    - Последнее сообщение от бота (is_from_bot=True)
    - С момента последнего сообщения прошло >= 24 часа
    - Нет активной цепочки follow-up (is_completed=False)
  - Получить последнее сообщение клиента
  - Проанализировать текст на точные ответы:
    - ДА: ["да", "согласен", "готов", "давайте", "хорошо", "ок"]
    - НЕТ: ["нет", "не надо", "не интересно", "не сейчас", "откажусь"]
    - Игнор: если клиент вообще не ответил
    - Неопределенно: ["посмотрю", "подумаю", "может быть", "возможно"]
  - Если ДА или НЕТ - НЕ запускать follow-up
  - Если Игнор или Неопределенно - запустить follow-up
- Создание цепочки:
  - Создать запись в follow_ups с touch_number=1
  - Рассчитать next_touch_at = текущее время + 24 часа
  - is_completed = False
- Генерация сообщения:
  - Загрузить промпт из prompts/follow_up_prompt.txt
  - Получить историю переписки
  - Получить последнее сообщение бота
  - Получить последнее сообщение клиента
  - Рассчитать hours_since_last_message
  - Заполнить плейсхолдеры
  - Вызвать gemini_client.generate_response()
  - Сохранить в messages
  - Опубликовать в outgoing_messages

#### Задача 3.12: Реализовать логику касаний
- Добавить метод `process_touch(follow_up_record)`:
  - Получить запись из follow_ups где next_touch_at <= NOW и is_completed=False
  - Генерировать сообщение для текущего touch_number
  - Отправить через очередь
  - Обновить last_touch_at
  - Если touch_number < 5:
    - Увеличить touch_number на 1
    - Рассчитать next_touch_at по интервалам: [24, 72, 168, 336, 720] часов
  - Если touch_number = 5:
    - Установить is_completed = True
    - Установить stop_reason = 'completed_5_touches'
- Добавить метод `stop_followup(contact_id, reason)`:
  - Найти активную цепочку follow-up
  - Установить is_completed = True
  - Установить stop_reason = reason ('client_responded', 'client_said_yes', 'client_said_no')
- Обновить message_consumer.py:
  - После сохранения входящего сообщения от клиента:
    - Проверить есть ли активный follow-up
    - Проанализировать ответ клиента
    - Если ДА или НЕТ - остановить follow-up
    - Если продолжение разговора - остановить follow-up

#### Задача 3.13: Интеграция Scheduler в app.py
- Создать главный файл `app.py` для ПРОЕКТ 2:
  - Импортировать MessageConsumerService и FollowUpSchedulerService
  - Создать async main():
    - Запустить consumer.start_consuming()
    - Запустить scheduler.start_scheduler()
    - Использовать asyncio.gather()
  - Добавить graceful shutdown
- Протестировать:
  - Создать тестовый контакт
  - Бот отправляет сообщение
  - Клиент не отвечает 24 часа
  - Проверить, что пришло касание #1
  - Проверить логику остановки при ответе

---

## 📊 WEEK 4: Интеграция, тестирование, деплой

### **День 22-23: End-to-end тестирование**

#### Задача 4.1: Сквозное тестирование всей системы
- Подготовить тестовый сценарий:
  - Новый контакт пишет первый раз
  - Контакт классифицируется как клиент
  - Контакт получает ответ от sales agent
  - Контакт не отвечает 24 часа
  - Запускается follow-up
  - Контакт отвечает "Да"
  - Follow-up останавливается
  - Назначается созвон
- Выполнить сценарий в реальном режиме
- Проверить каждый шаг:
  - Логи обоих проектов
  - Записи в БД
  - Сообщения в очередях
  - Отправка в WhatsApp
- Зафиксировать время выполнения каждого шага
- Записать найденные баги

#### Задача 4.2: Тестирование edge cases
- Протестировать граничные случаи:
  - Контакт в whitelist (должен игнорироваться)
  - Голосовое сообщение (транскрибация + обработка)
  - Множественные сообщения подряд (5+ за минуту)
  - Очень длинное сообщение (1000+ символов)
  - Сообщение с эмодзи и спецсимволами
  - Контакт пишет в 23:00 (вне рабочих часов)
  - Gemini API недоступен (обработка ошибки)
  - RabbitMQ недоступен (recovery)
  - PostgreSQL недоступен (recovery)
- Для каждого случая:
  - Задокументировать поведение
  - Убедиться в корректной обработке
  - Исправить найденные проблемы

#### Задача 4.3: Нагрузочное тестирование
- Симулировать высокую нагрузку:
  - 100 разных контактов пишут одновременно
  - 50 голосовых сообщений за 5 минут
  - 200 follow-up касаний в один момент
- Измерить:
  - Время обработки одного сообщения
  - Потребление памяти
  - Потребление CPU
  - Размер очередей
  - Количество ошибок
- Проверить стабильность:
  - Сервисы не падают
  - Нет утечек памяти
  - Очереди не переполняются
- Оптимизировать узкие места

---

### **День 24: Финальная доработка промптов**

#### Задача 4.4: Улучшение промпта модератора
- Собрать примеры реальных классификаций
- Проанализировать ошибочные классификации
- Обновить moderator_prompt.txt:
  - Добавить больше примеров критериев
  - Уточнить edge cases
  - Добавить few-shot примеры (если нужно)
- Протестировать на 50 разных контактах
- Замерить точность классификации
- Итерировать до достижения 90%+ точности

#### Задача 4.5: Улучшение промпта sales agent
- Проанализировать качество ответов бота
- Собрать feedback от тестировщиков
- Обновить sales_agent_prompt.txt:
  - Скорректировать стиль общения
  - Улучшить логику СПИН-продаж
  - Добавить примеры хороших ответов
  - Уточнить правила назначения созвонов
- Протестировать на 30 разных диалогах
- Проверить соответствие бренду

#### Задача 4.6: Улучшение промпта follow-up
- Проанализировать эффективность касаний
- Обновить follow_up_prompt.txt:
  - Улучшить тексты для каждого касания
  - Добавить больше вариативности
  - Проверить тональность
- Протестировать все 5 касаний
- Убедиться, что каждое касание уникально

---

### **День 25-26: Деплой на Render.com**

#### Задача 4.7: Подготовка ПРОЕКТ 1 к деплою
- Создать Dockerfile для whatsapp-gateway:
  - Базовый образ python:3.11-slim
  - Копирование requirements.txt и установка зависимостей
  - Копирование исходного кода
  - CMD для запуска app.py
- Создать render.yaml:
  - Настроить web service
  - Указать healthCheckPath: /health
  - Добавить environment variables
  - Подключить PostgreSQL database
  - Подключить Redis/RabbitMQ
- Проверить локально через Docker:
  - docker build -t whatsapp-gateway .
  - docker run с переменными окружения
  - Убедиться, что все работает
- Создать .dockerignore:
  - Исключить .env, __pycache__, logs/, tests/

#### Задача 4.8: Деплой ПРОЕКТ 1 на Render
- Создать новый Web Service на Render.com
- Подключить Git репозиторий whatsapp-gateway
- Настроить environment variables:
  - WAPPI_TOKEN
  - WAPPI_PROFILE_ID
  - RABBITMQ_URL (или Redis URL)
  - DATABASE_URL
  - Все остальные из .env
- Запустить первый deploy
- Проверить логи на ошибки
- Проверить health endpoint
- Протестировать polling (должен работать каждые 5 сек)

#### Задача 4.9: Подготовка ПРОЕКТ 2 к деплою
- Создать Dockerfile для ai-agent-service:
  - Базовый образ python:3.11-slim
  - Установить системные зависимости для PDF (poppler-utils)
  - Копирование requirements.txt
  - Копирование исходного кода
  - Копирование prompts/ и knowledge_base/
  - CMD для запуска app.py
- Создать render.yaml аналогично ПРОЕКТ 1
- Проверить локально через Docker
- Создать .dockerignore

#### Задача 4.10: Деплой ПРОЕКТ 2 на Render
- Создать новый Web Service на Render.com
- Подключить Git репозиторий ai-agent-service
- Настроить environment variables:
  - GEMINI_API_KEY
  - RABBITMQ_URL
  - DATABASE_URL
  - Все настройки из .env
- Загрузить PDF файлы базы знаний (если нужно)
- Запустить deploy
- Проверить логи
- Проверить health endpoint
- Протестировать consumer (подписка на очередь)

#### Задача 4.11: Настройка БД на Render
- Создать две PostgreSQL базы на Render:
  - whatsapp-gateway-db
  - ai-agent-service-db
- Применить миграции к обеим БД:
  - Подключиться через psql
  - Выполнить CREATE TABLE скрипты
  - Создать индексы
  - Предзаполнить whitelist
- Проверить подключение из сервисов
- Настроить автоматический backup (daily)

#### Задача 4.12: Настройка очередей
- Создать RabbitMQ инстанс на CloudAMQP (или Redis на Render)
- Создать три очереди с настройками из ТЗ
- Обновить RABBITMQ_URL в обоих проектах
- Проверить подключение из обоих сервисов
- Протестировать публикацию и подписку

---

### **День 27: Мониторинг и логирование**

#### Задача 4.13: Настроить централизованное логирование
- Выбрать сервис для логов (опции: Papertrail, Logtail, Render Logs)
- Настроить отправку логов из обоих проектов
- Создать фильтры для разных уровней:
  - ERROR - критические ошибки
  - WARNING - важные события
  - INFO - обычная работа
- Настроить алерты:
  - Email при ERROR логах
  - Email при недоступности сервиса
  - Email при превышении квоты Gemini

#### Задача 4.14: Создать дашборд мониторинга
- Использовать встроенные метрики Render или внешний сервис
- Отслеживать метрики:
  - CPU usage обоих сервисов
  - Memory usage
  - Количество запросов в минуту
  - Размер очередей
  - Время отклика health endpoints
- Настроить алерты при превышении порогов:
  - CPU > 80%
  - Memory > 90%
  - Queue size > 1000
  - Health check failed

#### Задача 4.15: Документация для мониторинга
- Создать runbook в README:
  - Что делать при падении ПРОЕКТ 1
  - Что делать при падении ПРОЕКТ 2
  - Что делать при переполнении очередей
  - Что делать при исчерпании квоты Gemini
  - Контакты для экстренной связи
- Создать чек-лист проверки здоровья системы:
  - Health endpoints отвечают 200 OK
  - Polling работает (логи каждые 5 сек)
  - Сообщения обрабатываются (проверить БД)
  - Очереди не переполнены
  - Нет ERROR в логах за последний час

---

### **День 28: Финальное тестирование и документация**

#### Задача 4.16: Полное тестирование в продакшене
- Выполнить end-to-end тест на продакшен окружении:
  - Отправить сообщение с реального номера
  - Проверить весь цикл обработки
  - Проверить отправку ответа
  - Проверить созвон и follow-up
- Протестировать все сценарии из Задачи 4.2
- Исправить найденные баги в продакшене
- Задокументировать известные ограничения

#### Задача 4.17: Создать документацию для пользователя
- Создать USER_GUIDE.md:
  - Как система работает (общая схема)
  - Что происходит когда клиент пишет
  - Как работает классификация
  - Как работает follow-up
  - Как назначаются созвоны
  - Whitelist номеров
- Создать FAQ:
  - Почему бот не ответил на сообщение?
  - Как добавить номер в whitelist?
  - Как обновить базу знаний?
  - Как изменить промпты?
  - Как посмотреть статистику?

#### Задача 4.18: Создать техническую документацию
- Создать ARCHITECTURE.md:
  - Диаграмма архитектуры
  - Описание каждого компонента
  - Схема взаимодействия через очереди
  - Схема БД с описанием таблиц
- Создать DEPLOYMENT.md:
  - Инструкция по деплою на Render
  - Настройка переменных окружения
  - Применение миграций
  - Rollback процедура
- Создать API_REFERENCE.md:
  - Документация всех endpoints
  - Примеры запросов/ответов
  - Коды ошибок

#### Задача 4.19: Code review и рефакторинг
- Провести ревью кода обоих проектов:
  - Проверить соблюдение PEP 8
  - Проверить наличие docstrings
  - Проверить обработку ошибок
  - Удалить закомментированный код
  - Удалить неиспользуемые импорты
- Оптимизировать производительность:
  - Добавить кэширование где нужно
  - Оптимизировать SQL запросы
  - Добавить connection pooling для БД
- Улучшить читаемость:
  - Переименовать непонятные переменные
  - Разбить большие функции
  - Добавить комментарии к сложной логике

#### Задача 4.20: Передача проекта
- Подготовить репозитории к передаче:
  - Убедиться что .env не в Git
  - Все секреты в переменных окружения
  - README полный и понятный
- Создать видео-презентацию (10-15 минут):
  - Демонстрация работы системы
  - Обзор архитектуры
  - Показ основных компонентов
  - Демонстрация дашборда
- Провести handover сессию:
  - Пройтись по коду
  - Ответить на вопросы
  - Показать как менять настройки
  - Показать как обновлять промпты
- Предоставить доступы:
  - GitHub репозитории
  - Render.com проекты
  - RabbitMQ/Redis
  - PostgreSQL базы
  - Gemini API key (или инструкция как получить свой)

---

## 📋 ЧЕКЛИСТ ГОТОВНОСТИ К ЗАПУСКУ

### **Инфраструктура**
- [ ] PostgreSQL для ПРОЕКТ 1 создана и доступна
- [ ] PostgreSQL для ПРОЕКТ 2 создана и доступна
- [ ] RabbitMQ/Redis настроен и доступен
- [ ] Все три очереди созданы
- [ ] Миграции применены к обеим БД
- [ ] Whitelist предзаполнен тремя номерами
- [ ] Все переменные окружения заполнены

### **ПРОЕКТ 1: WhatsApp Gateway**
- [ ] Wappi API токен и profile_id валидны
- [ ] WappiClient работает (тестовая отправка успешна)
- [ ] Polling Service запущен и получает чаты каждые 5 сек
- [ ] Sender Service подписан на outgoing_messages
- [ ] Voice Transcription Service подписан на voice_transcription
- [ ] Health endpoint отвечает 200 OK
- [ ] Логи пишутся корректно
- [ ] Сервис задеплоен на Render

### **ПРОЕКТ 2: AI Agent Service**
- [ ] Gemini API ключ валиден
- [ ] GeminiClient работает (тестовый запрос успешен)
- [ ] PDF базы знаний загружены и парсятся
- [ ] Все три промпта заполнены и протестированы
- [ ] Message Consumer подписан на incoming_messages
- [ ] AI Moderator классифицирует контакты корректно
- [ ] AI Sales Agent генерирует адекватные ответы
- [ ] Follow-up Scheduler работает по расписанию
- [ ] Timezone helper корректно определяет рабочие часы
- [ ] Health endpoint отвечает 200 OK
- [ ] Сервис задеплоен на Render

### **Интеграция**
- [ ] Сообщения проходят через всю цепочку (ПРОЕКТ 1 → Очередь → ПРОЕКТ 2 → Очередь → ПРОЕКТ 1 → WhatsApp)
- [ ] Голосовые транскрибируются и обрабатываются
- [ ] Whitelist фильтрует номера
- [ ] Классификация работает автоматически
- [ ] Ответы отправляются в WhatsApp
- [ ] Follow-up запускается и останавливается корректно
- [ ] Созвоны назначаются только в рабочее время

### **Мониторинг**
- [ ] Логирование настроено
- [ ] Алерты настроены
- [ ] Дашборд мониторинга работает
- [ ] Runbook создан

### **Документация**
- [ ] README в обоих репозиториях
- [ ] USER_GUIDE.md создан
- [ ] ARCHITECTURE.md создан
- [ ] DEPLOYMENT.md создан
- [ ] API_REFERENCE.md создан
- [ ] Видео-презентация записана

---

## 🎯 КРИТЕРИИ ПРИЕМКИ ПРОЕКТА

### **Функциональные требования**
1. ✅ Система получает все сообщения из WhatsApp через Wappi API
2. ✅ Whitelist фильтрует три указанных номера
3. ✅ Голосовые сообщения транскрибируются на русском языке
4. ✅ Контакты классифицируются автоматически (isClient: true/false/null)
5. ✅ Клиенты получают ответы от AI sales agent
6. ✅ Ответы основаны на базе знаний из PDF
7. ✅ Follow-up запускается при игнорировании или неопределенном ответе
8. ✅ Follow-up останавливается при ответе "ДА" или "НЕТ"
9. ✅ Созвоны назначаются только в рабочее время (10:00-18:00 Астана)
10. ✅ Все компоненты работают через очереди (RabbitMQ/Redis)

### **Нефункциональные требования**
1. ✅ Время обработки одного сообщения < 10 секунд
2. ✅ Система обрабатывает минимум 100 сообщений в час
3. ✅ Uptime > 99% (максимум 7 часов downtime в месяц)
4. ✅ Все секреты в переменных окружения (не в коде)
5. ✅ Логи хранятся минимум 30 дней
6. ✅ Код покрыт комментариями и документацией
7. ✅ Есть health endpoints для мониторинга
8. ✅ Graceful shutdown при остановке сервисов

### **Качество AI**
1. ✅ Точность классификации контактов > 90%
2. ✅ Ответы sales agent релевантны и используют базу знаний
3. ✅ Стиль общения профессиональный и дружелюбный
4. ✅ Длина сообщений 2-4 предложения (не более)
5. ✅ Эмодзи используются умеренно (1-2 на сооб