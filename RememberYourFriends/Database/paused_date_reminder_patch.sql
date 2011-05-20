BEGIN;

ALTER TABLE reminders
  DROP COLUMN paused;

ALTER TABLE reminders
  ADD paused_date TIMESTAMP;

ALTER TABLE reminders
  ALTER paused_date SET DEFAULT 'infinity';

UPDATE reminders
  SET paused_date = 'infinity' WHERE paused_date IS NULL;

ALTER TABLE reminders 
  ALTER paused_date SET NOT NULL;

COMMIT;

