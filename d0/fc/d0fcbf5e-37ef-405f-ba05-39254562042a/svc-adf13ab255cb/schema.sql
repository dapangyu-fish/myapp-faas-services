CREATE TABLE IF NOT EXISTS messages (
  id serial PRIMARY KEY,
  name text NOT NULL,
  content text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS messages_created_at_idx ON messages(created_at DESC);
