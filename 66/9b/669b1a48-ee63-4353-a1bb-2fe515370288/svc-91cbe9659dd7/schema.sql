CREATE TABLE IF NOT EXISTS items (
  id serial PRIMARY KEY,
  title text NOT NULL,
  price numeric NOT NULL DEFAULT 0,
  category text NOT NULL DEFAULT '其他',
  description text NOT NULL DEFAULT '',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS items_created_idx ON items(created_at DESC);
CREATE INDEX IF NOT EXISTS items_category_idx ON items(category);
