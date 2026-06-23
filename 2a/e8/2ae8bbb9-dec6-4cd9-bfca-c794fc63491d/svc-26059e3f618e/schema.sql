-- 打卡社区 FaaS schema：公开 feed + 点赞 + 评论 + 自助同步显示名
-- 规则：UUID 主键；身份 author_id / owner_id = myapp_auth.current_user()（组内假名，不可伪造）

CREATE TABLE IF NOT EXISTS profiles (
  owner_id     text PRIMARY KEY,
  display_name text NOT NULL DEFAULT '',
  updated_at   timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS checkins (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  author_id     text NOT NULL,
  content       text NOT NULL,
  like_count    integer NOT NULL DEFAULT 0,
  comment_count integer NOT NULL DEFAULT 0,
  created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS likes (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  checkin_id  uuid NOT NULL,
  owner_id    text NOT NULL,
  created_at  timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT likes_uniq UNIQUE (checkin_id, owner_id)
);

CREATE TABLE IF NOT EXISTS comments (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  checkin_id  uuid NOT NULL,
  author_id   text NOT NULL,
  body        text NOT NULL,
  created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_checkins_created  ON checkins (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_checkins_author   ON checkins (author_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_likes_checkin     ON likes (checkin_id);
CREATE INDEX IF NOT EXISTS idx_likes_owner       ON likes (owner_id);
CREATE INDEX IF NOT EXISTS idx_comments_checkin  ON comments (checkin_id, created_at);
