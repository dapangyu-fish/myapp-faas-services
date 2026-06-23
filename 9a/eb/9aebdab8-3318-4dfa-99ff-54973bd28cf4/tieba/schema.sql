-- 贴吧 FaaS 后端 schema（公开论坛 + 好友 + 私信）
-- 规则：UUID 主键；author_id/owner_id = myapp_auth.current_user() 的组内假名（不可伪造）；
-- 好友/私信只在本服务组内、用组内假名互通（跨 App 不可关联，符合假名隔离）。

-- ── 论坛 ──
CREATE TABLE IF NOT EXISTS boards (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name        text NOT NULL UNIQUE,
  intro       text NOT NULL DEFAULT '',
  owner_id    text NOT NULL,
  created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS threads (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  board_id    uuid NOT NULL,
  author_id   text NOT NULL,
  title       text NOT NULL,
  body        text NOT NULL DEFAULT '',
  reply_count integer NOT NULL DEFAULT 0,
  created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS posts (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  thread_id   uuid NOT NULL,
  parent_id   uuid,
  author_id   text NOT NULL,
  body        text NOT NULL,
  created_at  timestamptz NOT NULL DEFAULT now()
);

-- ── 身份 ──
CREATE TABLE IF NOT EXISTS profiles (
  owner_id     text PRIMARY KEY,
  display_name text NOT NULL DEFAULT '',
  updated_at   timestamptz NOT NULL DEFAULT now()
);

-- ── 社交 ──
CREATE TABLE IF NOT EXISTS friendships (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  requester_id  text NOT NULL,
  addressee_id  text NOT NULL,
  status        text NOT NULL DEFAULT 'pending',
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT friendships_status_chk CHECK (status IN ('pending','accepted')),
  CONSTRAINT friendships_pair_uniq UNIQUE (requester_id, addressee_id)
);

CREATE TABLE IF NOT EXISTS messages (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  sender_id     text NOT NULL,
  recipient_id  text NOT NULL,
  body          text NOT NULL,
  created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_boards_name      ON boards (name);
CREATE INDEX IF NOT EXISTS idx_threads_board    ON threads (board_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_threads_author   ON threads (author_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_posts_thread     ON posts (thread_id, created_at);
CREATE INDEX IF NOT EXISTS idx_posts_parent     ON posts (parent_id);
CREATE INDEX IF NOT EXISTS idx_friend_requester ON friendships (requester_id);
CREATE INDEX IF NOT EXISTS idx_friend_addressee ON friendships (addressee_id, status);
CREATE INDEX IF NOT EXISTS idx_messages_pair    ON messages (sender_id, recipient_id, created_at);
