-- 客服工单系统 schema
-- 规则：UUID 主键（禁自增）；每条数据记 owner；写入强制 current_user() 不可伪造

-- 工单
CREATE TABLE IF NOT EXISTS tickets (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id        text NOT NULL,
  title           text NOT NULL,
  description     text NOT NULL DEFAULT '',
  status          text NOT NULL DEFAULT 'open',
  unread_count    int NOT NULL DEFAULT 0,
  last_message_at timestamptz,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now()
);

-- 消息
CREATE TABLE IF NOT EXISTS messages (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  ticket_id  uuid NOT NULL,
  sender_id  text NOT NULL,
  body       text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- 用户显示名
CREATE TABLE IF NOT EXISTS profiles (
  owner_id     text PRIMARY KEY,
  display_name text NOT NULL DEFAULT '',
  updated_at   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tickets_owner   ON tickets (owner_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tickets_status  ON tickets (owner_id, status);
CREATE INDEX IF NOT EXISTS idx_messages_ticket ON messages (ticket_id, created_at ASC);
