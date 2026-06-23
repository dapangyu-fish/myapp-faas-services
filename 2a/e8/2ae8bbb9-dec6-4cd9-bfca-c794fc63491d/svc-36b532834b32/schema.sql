-- 多用户论坛：主题帖 + 评论 + 用户显示名
-- 主键一律 UUID（不可枚举）；写入把 author_id / owner_id 强制成当前调用者的组内假名
-- （myapp_auth.current_user()，不可伪造）；展示昵称时 LEFT JOIN profiles 一起带出来。

CREATE TABLE IF NOT EXISTS profiles (
  owner_id     text PRIMARY KEY,
  display_name text NOT NULL DEFAULT '',
  updated_at   timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS threads (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  author_id  text NOT NULL,
  title      text NOT NULL,
  body       text NOT NULL DEFAULT '',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS comments (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  thread_id  uuid NOT NULL,
  author_id  text NOT NULL,
  body       text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_threads_created  ON threads (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_threads_author   ON threads (author_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_comments_thread  ON comments (thread_id, created_at);
CREATE INDEX IF NOT EXISTS idx_comments_author  ON comments (author_id, created_at DESC);