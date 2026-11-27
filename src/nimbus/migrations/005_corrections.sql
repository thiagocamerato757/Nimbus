ALTER TABLE games ADD COLUMN edit_history TEXT NOT NULL DEFAULT '[]';
PRAGMA user_version = 5;
