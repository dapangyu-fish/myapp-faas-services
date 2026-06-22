CREATE TABLE IF NOT EXISTS expenses (
  id serial PRIMARY KEY,
  amount numeric(12,2) NOT NULL DEFAULT 0,
  category text NOT NULL DEFAULT '其他',
  note text NOT NULL DEFAULT '',
  created_at timestamptz NOT NULL DEFAULT now()
);
