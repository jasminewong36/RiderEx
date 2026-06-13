-- RiderEx — Supabase Schema
-- Run this in the Supabase SQL Editor (https://supabase.com/dashboard → SQL Editor)

CREATE TABLE IF NOT EXISTS rides (
  id                  UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  ticket_id           TEXT,
  ride_id             TEXT,
  vehicle_id          TEXT,
  category            TEXT,
  priority            TEXT,
  safety_level        TEXT,
  nhtsa               BOOLEAN DEFAULT FALSE,
  rating              INTEGER,
  churn_risk          TEXT,
  refund_amount       NUMERIC DEFAULT 0,
  credit_amount       NUMERIC DEFAULT 0,
  good_ride           BOOLEAN DEFAULT FALSE,
  sentiment           TEXT,
  quality_score       INTEGER,
  review_decision     TEXT,
  requires_engineering BOOLEAN DEFAULT FALSE,
  engineering_team    TEXT,
  vehicle_action      TEXT,
  action_items        INTEGER DEFAULT 0,
  band_messages       INTEGER DEFAULT 0,
  key_phrases         TEXT[],
  -- Full agent outputs stored as JSONB for flexibility
  intake_data         JSONB,
  safety_data         JSONB,
  resolution_data     JSONB,
  review_data         JSONB,
  engineering_data    JSONB,
  created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast dashboard queries
CREATE INDEX IF NOT EXISTS idx_rides_category    ON rides(category);
CREATE INDEX IF NOT EXISTS idx_rides_priority    ON rides(priority);
CREATE INDEX IF NOT EXISTS idx_rides_safety      ON rides(safety_level);
CREATE INDEX IF NOT EXISTS idx_rides_created_at  ON rides(created_at DESC);

-- Enable Row Level Security (allow public read for dashboard, restrict writes to service role)
ALTER TABLE rides ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read" ON rides FOR SELECT USING (true);
CREATE POLICY "Allow service insert" ON rides FOR INSERT WITH CHECK (true);
