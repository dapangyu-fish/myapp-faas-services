-- 小红书风格「笔记 + 评论 + 点赞」FaaS 后端 schema
-- 规则：用 UUID 主键（不要用自增主键）；公开内容公开可读，写入记作者的组内假名
-- （author_id / owner_id = myapp_auth.current_user()，不可伪造）。
-- 部署期由属主角色执行；运行时角色只有数据读写权限（不能改表结构）。
-- 表按领域拆开：内容(posts/comments/post_likes) + 身份(profiles)。

-- ── 身份 ──
-- 用户在本服务的显示名：自助设置，函数强制 owner_id = current_user()（改不了别人的）。
-- display_name 由客户端用用户的真实平台昵称同步进来。
CREATE TABLE IF NOT EXISTS profiles (
  owner_id     text PRIMARY KEY,
  display_name text NOT NULL DEFAULT '',
  updated_at   timestamptz NOT NULL DEFAULT now()
);

-- ── 笔记（posts）──
-- 类似小红书「笔记」：标题 + 正文（纯文本）
CREATE TABLE IF NOT EXISTS posts (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  author_id    text NOT NULL,
  title        text NOT NULL,
  body         text NOT NULL DEFAULT '',
  like_count   integer NOT NULL DEFAULT 0,
  comment_count integer NOT NULL DEFAULT 0,
  created_at   timestamptz NOT NULL DEFAULT now()
);

-- ── 评论（含楼中楼：parent_id 自引用）──
CREATE TABLE IF NOT EXISTS comments (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  post_id    uuid NOT NULL,
  parent_id  uuid,                              -- NULL=顶层评论；非NULL=楼中楼回复某条评论
  author_id  text NOT NULL,
  body       text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- ── 点赞（去重：一人一帖一条；liked_by_me 查询用）──
CREATE TABLE IF NOT EXISTS post_likes (
  post_id    uuid NOT NULL,
  user_id    text NOT NULL,                     -- 当前调用者组内假名
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT post_likes_pk PRIMARY KEY (post_id, user_id)
);

-- 索引：覆盖所有 WHERE/JOIN 路径
CREATE INDEX IF NOT EXISTS idx_posts_author    ON posts (author_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_posts_created   ON posts (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_comments_post   ON comments (post_id, created_at);
CREATE INDEX IF NOT EXISTS idx_comments_parent ON comments (parent_id);
CREATE INDEX IF NOT EXISTS idx_likes_user      ON post_likes (user_id);
