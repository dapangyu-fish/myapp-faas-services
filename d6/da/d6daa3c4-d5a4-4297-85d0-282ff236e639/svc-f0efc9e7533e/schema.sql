CREATE TABLE IF NOT EXISTS expenses (
    id serial PRIMARY KEY,
    amount numeric NOT NULL DEFAULT 0,
    category text NOT NULL DEFAULT '',
    note text NOT NULL DEFAULT '',
    created_at timestamptz NOT NULL DEFAULT now()
);
