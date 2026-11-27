ALTER TABLE games ADD COLUMN first_selection_holder TEXT CHECK(first_selection_holder IN ('A', 'B'));
ALTER TABLE games ADD COLUMN first_selection_choice TEXT CHECK(first_selection_choice IN ('side', 'draft_position'));
PRAGMA user_version = 9;
