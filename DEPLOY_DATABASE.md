# 🗄️ Deploy Database Schema to Neon.tech

## 📋 Overview

You need to create tables in your Neon.tech PostgreSQL databases before the services can run.

---

## 🚀 **Method 1: Auto-Deploy via Docker (Recommended)**

### **Step 1: Make sure .env files are configured**

Both `.env` files should have your Neon.tech DATABASE_URL:

**ai-agent-service/.env:**
```env
DATABASE_URL="postgresql://neondb_owner:npg_SwrTZs7Goz3E@ep-sparkling-unit-ag1o345l-pooler.c-2.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
```

**whatsapp-gateway/.env:**
```env
DATABASE_URL="postgresql://your_neon_gateway_db_url_here?sslmode=require&channel_binding=require"
```

### **Step 2: Start Docker Compose**
```bash
cd c:\projects\whatsappAI
docker-compose up -d
```

### **Step 3: Run Database Initialization**
```bash
# Initialize AI Agent database
docker-compose exec ai-agent-service python init_db.py

# Initialize WhatsApp Gateway database (if separate)
docker-compose exec whatsapp-gateway python init_db.py
```

### **Step 4: Verify Tables Created**
```bash
# Check AI Agent service logs
docker-compose logs ai-agent-service | grep -i "database"

# Or connect to Neon.tech console and check tables
```

---

## 🛠️ **Method 2: Manual SQL Deployment**

If `init_db.py` doesn't work, run SQL manually:

### **Step 1: Go to Neon.tech Console**
1. Login to https://console.neon.tech
2. Select your database
3. Click "SQL Editor"

### **Step 2: Run the Schema Script**

Copy the contents of `deploy_schema.sql` and paste into SQL Editor:

```sql
-- Run this in your Neon.tech SQL Editor
-- (See deploy_schema.sql for full script)

-- AI Agent Service Tables
CREATE TABLE contacts (...);
CREATE TABLE messages (...);
CREATE TABLE follow_ups (...);
CREATE TABLE scheduled_calls (...);

-- WhatsApp Gateway Tables (if separate DB)
CREATE TABLE message_logs (...);
CREATE TABLE whitelist (...);

-- Whitelist data
INSERT INTO whitelist (phone_number, note) VALUES
    ('77752837306', 'Личный номер 1'),
    ('77018855588', 'Личный номер 2'),
    ('77088098009', 'Личный номер 3')
ON CONFLICT DO NOTHING;
```

### **Step 3: Verify Tables**
```sql
-- Check tables were created
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public';

-- Should show:
-- contacts
-- messages
-- follow_ups
-- scheduled_calls
-- message_logs
-- whitelist
```

---

## 🔍 **Method 3: Local Python Script**

Run directly from your machine:

### **Step 1: Install dependencies**
```bash
cd ai-agent-service
pip install -r requirements.txt
```

### **Step 2: Set environment variable**
```bash
# Windows
set DATABASE_URL="postgresql://neondb_owner:npg_SwrTZs7Goz3E@..."

# Linux/Mac
export DATABASE_URL="postgresql://neondb_owner:npg_SwrTZs7Goz3E@..."
```

### **Step 3: Run init script**
```bash
python init_db.py
```

---

## ✅ **Verification Checklist**

After deployment, verify:

### **AI Agent Service Database**
- [ ] `contacts` table created
- [ ] `messages` table created
- [ ] `follow_ups` table created
- [ ] `scheduled_calls` table created
- [ ] All indexes created
- [ ] Foreign keys set up

### **WhatsApp Gateway Database** (if separate)
- [ ] `message_logs` table created
- [ ] `whitelist` table created
- [ ] Whitelist has 3 default numbers
- [ ] All indexes created

---

## 🧪 **Test Database Connection**

### **From Docker:**
```bash
# Test AI Agent DB connection
docker-compose exec ai-agent-service python -c "
from config.database import engine
print('Testing connection...')
connection = engine.connect()
result = connection.execute('SELECT COUNT(*) FROM contacts')
print(f'Contacts table accessible: {result.scalar()}')
connection.close()
print('✅ Database connection OK!')
"
```

### **From Neon.tech Console:**
```sql
-- Test query
SELECT
    'contacts' as table_name, COUNT(*) as count FROM contacts
UNION ALL
SELECT 'messages', COUNT(*) FROM messages
UNION ALL
SELECT 'follow_ups', COUNT(*) FROM follow_ups
UNION ALL
SELECT 'whitelist', COUNT(*) FROM whitelist;
```

---

## 🐛 **Troubleshooting**

### **Error: "relation does not exist"**
→ Tables not created. Run `init_db.py` or SQL script again.

### **Error: "connection refused"**
→ Check DATABASE_URL is correct and Neon.tech database is active.

### **Error: "SSL required"**
→ Make sure URL has `?sslmode=require` and is quoted in `.env`

### **Error: "permission denied"**
→ Check database user has CREATE TABLE permissions.

---

## 📊 **Expected Database Structure**

### **AI Agent Service:**
```
neondb
├── contacts (main contact records)
├── messages (conversation history)
├── follow_ups (5-touch sequences)
└── scheduled_calls (call appointments)
```

### **WhatsApp Gateway:**
```
whatsapp_gateway
├── message_logs (all messages)
└── whitelist (ignored numbers)
```

---

## 🎯 **Quick Deploy Commands**

**All-in-one deployment:**
```bash
# 1. Start services
docker-compose up -d

# 2. Initialize databases
docker-compose exec ai-agent-service python init_db.py
docker-compose exec whatsapp-gateway python init_db.py

# 3. Check services
docker-compose ps
curl http://localhost:8000/health
curl http://localhost:8001/health

# 4. View logs
docker-compose logs -f
```

---

## ✅ **Success Indicators**

You'll know it worked when:
- ✅ `docker-compose logs` shows "Database initialized"
- ✅ Neon.tech console shows all tables
- ✅ Services start without database errors
- ✅ Health endpoints return 200 OK
- ✅ Whitelist has 3 entries

---

## 🚀 **After Database Deploy**

Once tables are created:
1. ✅ Services will start successfully
2. ✅ Messages will be stored
3. ✅ AI classification will work
4. ✅ Follow-ups will be tracked
5. ✅ System is fully operational!

**Next step:** Test by sending a WhatsApp message! 📱
