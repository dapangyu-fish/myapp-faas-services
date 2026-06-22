CREATE TABLE IF NOT EXISTS bookmarks (
    id serial PRIMARY KEY,
    title text NOT NULL,
    url text NOT NULL,
    tag text NOT NULL DEFAULT '',
    created_at timestamptz NOT NULL DEFAULT now()
);
