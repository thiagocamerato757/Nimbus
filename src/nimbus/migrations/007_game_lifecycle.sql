ALTER TABLE games ADD COLUMN winner TEXT CHECK (winner IN ('A', 'B'));
ALTER TABLE games ADD COLUMN voided INTEGER NOT NULL DEFAULT 0;
PRAGMA user_version = 7;
