-- ============================================
-- WhatsApp AI Agent System - Database Schema
-- Deploy this to your Neon.tech databases
-- ============================================

-- ============================================
-- AI AGENT SERVICE DATABASE SCHEMA
-- ============================================

-- Contacts Table
CREATE TABLE IF NOT EXISTS contacts (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255),
    full_name VARCHAR(255),
    business_name VARCHAR(255),
    is_client BOOLEAN DEFAULT NULL,
    classification_confidence FLOAT,
    classification_reasoning TEXT,
    last_message_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for contacts
CREATE INDEX IF NOT EXISTS idx_contacts_phone ON contacts(phone_number);
CREATE INDEX IF NOT EXISTS idx_contacts_is_client ON contacts(is_client);
CREATE INDEX IF NOT EXISTS idx_is_client_updated ON contacts(is_client, updated_at);

-- Messages Table
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    contact_id INTEGER REFERENCES contacts(id) ON DELETE CASCADE,
    phone_number VARCHAR(20) NOT NULL,
    message_id VARCHAR(255) UNIQUE,
    message_text TEXT,
    is_from_bot BOOLEAN DEFAULT FALSE,
    is_voice BOOLEAN DEFAULT FALSE,
    voice_transcription TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for messages
CREATE INDEX IF NOT EXISTS idx_messages_contact_id ON messages(contact_id);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_contact_timestamp ON messages(contact_id, timestamp);

-- Follow-ups Table
CREATE TABLE IF NOT EXISTS follow_ups (
    id SERIAL PRIMARY KEY,
    contact_id INTEGER REFERENCES contacts(id) ON DELETE CASCADE,
    touch_number INTEGER DEFAULT 1 NOT NULL,
    next_touch_at TIMESTAMP WITH TIME ZONE,
    last_touch_at TIMESTAMP WITH TIME ZONE,
    is_completed BOOLEAN DEFAULT FALSE,
    stop_reason VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT check_touch_number_range CHECK (touch_number >= 1 AND touch_number <= 5)
);

-- Create indexes for follow_ups
CREATE INDEX IF NOT EXISTS idx_follow_ups_next_touch ON follow_ups(next_touch_at);
CREATE INDEX IF NOT EXISTS idx_next_touch_incomplete ON follow_ups(next_touch_at, is_completed);

-- Scheduled Calls Table
CREATE TABLE IF NOT EXISTS scheduled_calls (
    id SERIAL PRIMARY KEY,
    contact_id INTEGER REFERENCES contacts(id) ON DELETE CASCADE,
    scheduled_at TIMESTAMP WITH TIME ZONE NOT NULL,
    timezone VARCHAR(50) DEFAULT 'Asia/Almaty' NOT NULL,
    status VARCHAR(50) DEFAULT 'scheduled' NOT NULL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for scheduled_calls
CREATE INDEX IF NOT EXISTS idx_scheduled_calls_time ON scheduled_calls(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_scheduled_status ON scheduled_calls(scheduled_at, status);

-- ============================================
-- WHATSAPP GATEWAY DATABASE SCHEMA
-- (Run this in your WhatsApp Gateway database if separate)
-- ============================================

-- Message Logs Table
CREATE TABLE IF NOT EXISTS message_logs (
    id SERIAL PRIMARY KEY,
    message_id VARCHAR(255) UNIQUE NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    direction VARCHAR(10) NOT NULL,
    message_text TEXT,
    is_voice BOOLEAN DEFAULT FALSE,
    wappi_status VARCHAR(50),
    queue_status VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for message_logs
CREATE INDEX IF NOT EXISTS idx_message_logs_phone ON message_logs(phone_number);
CREATE INDEX IF NOT EXISTS idx_message_logs_created ON message_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_phone_created ON message_logs(phone_number, created_at);
CREATE INDEX IF NOT EXISTS idx_direction_status ON message_logs(direction, queue_status);

-- Whitelist Table
CREATE TABLE IF NOT EXISTS whitelist (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    note TEXT,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for whitelist
CREATE INDEX IF NOT EXISTS idx_whitelist_phone ON whitelist(phone_number);

-- Insert default whitelist numbers
INSERT INTO whitelist (phone_number, note) VALUES
    ('77752837306', 'Личный номер 1'),
    ('77018855588', 'Личный номер 2'),
    ('77088098009', 'Личный номер 3')
ON CONFLICT (phone_number) DO NOTHING;

-- ============================================
-- Verification Queries
-- ============================================

-- Check tables were created
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- Check whitelist populated
SELECT * FROM whitelist;
