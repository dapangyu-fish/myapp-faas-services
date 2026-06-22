CREATE TABLE IF NOT EXISTS expenses (
  id serial PRIMARY KEY,
  amount numeric(12,2) NOT NULL DEFAULT 0,
  note text NOT NULL DEFAULT '',
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS expenses_created_idx ON expenses(created_at DESC);
