CREATE TABLE IF NOT EXISTS listings (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    region TEXT NOT NULL,
    monthly_rent INTEGER NOT NULL DEFAULT 0,
    room_type TEXT NOT NULL DEFAULT '套房',
    ping_size REAL,
    description TEXT DEFAULT '',
    is_rented BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_listings_region ON listings(region);
CREATE INDEX IF NOT EXISTS idx_listings_rent ON listings(monthly_rent);
CREATE INDEX IF NOT EXISTS idx_listings_rented ON listings(is_rented);
