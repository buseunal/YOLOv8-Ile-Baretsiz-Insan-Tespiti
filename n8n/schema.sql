-- Kask ihlali olaylarının saklandığı tablo
CREATE TABLE IF NOT EXISTS violations (
  id             SERIAL PRIMARY KEY,
  camera_id      TEXT        NOT NULL,
  violation_type TEXT        NOT NULL,
  confidence     NUMERIC(4,3) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  detected_at    TIMESTAMP   NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_violations_detected_at ON violations (detected_at);
