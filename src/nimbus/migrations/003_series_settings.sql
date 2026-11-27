ALTER TABLE series ADD COLUMN patch TEXT;
ALTER TABLE series ADD COLUMN record_type TEXT NOT NULL DEFAULT 'official';
ALTER TABLE games ADD COLUMN patch TEXT;
PRAGMA user_version = 3;
