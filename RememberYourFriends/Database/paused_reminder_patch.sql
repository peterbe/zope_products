BEGIN;

ALTER TABLE reminders
  ADD paused BOOLEAN;

ALTER TABLE reminders
  ALTER paused SET DEFAULT false;

UPDATE reminders
  SET paused = false WHERE paused IS NULL;

ALTER TABLE reminders 
  ALTER paused SET NOT NULL;

COMMIT;

