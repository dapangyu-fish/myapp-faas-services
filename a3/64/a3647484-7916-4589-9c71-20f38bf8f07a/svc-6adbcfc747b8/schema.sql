-- 云社区 论坛后端 schema（公开内容论坛：板块/主题/楼中楼回复 + 用户显示名）
-- 规则：UUID 主键（禁自增）；公开内容公开可读，写入记作者的组内假名
-- (author_id/owner_id = myapp_auth.current_user()，不可伪造)。
-- 部署期由属主角色执行；运行时角色只有数据读写权限。

CREATE TABLE IF NOT EXISTS zones (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name        text NOT NULL UNIQUE,
  intro       text NOT NULL DEFAULT '',
  owner_id    text NOT NULL,
  created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS topics (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  zone_id     uuid NOT NULL,
  author_id   text NOT NULL,
  title       text NOT NULL,
  body        text NOT NULL DEFAULT '',
  reply_count integer NOT NULL DEFAULT 0,
  created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS replies (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  topic_id    uuid NOT NULL,
  parent_id   uuid,
  author_id   text NOT NULL,
  body        text NOT NULL,
  created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS profiles (
  owner_id     text PRIMARY KEY,
  display_name text NOT NULL DEFAULT '',
  updated_at   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_zones_name      ON zones (name);
CREATE INDEX IF NOT EXISTS idx_topics_zone     ON topics (zone_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_topics_author   ON topics (author_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_replies_topic   ON replies (topic_id, created_at);
CREATE INDEX IF NOT EXISTS idx_replies_parent  ON replies (parent_id);
