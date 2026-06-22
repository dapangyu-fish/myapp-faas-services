CREATE TABLE IF NOT EXISTS bookmarks (
  id serial PRIMARY KEY,
  title text NOT NULL,
  url text NOT NULL,
  tag text NOT NULL DEFAULT '',
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS bookmarks_created_at_idx ON bookmarks (created_at DESC);
CREATE INDEX IF NOT EXISTS bookmarks_tag_idx ON bookmarks (tag);
