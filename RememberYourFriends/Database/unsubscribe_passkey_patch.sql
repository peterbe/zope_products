BEGIN;

ALTER TABLE users
  ADD unsubscribe_passkey VARCHAR(250);

ALTER TABLE users
  ALTER unsubscribe_passkey SET DEFAULT '';

UPDATE users
  SET unsubscribe_passkey = '' WHERE unsubscribe_passkey IS NULL;

ALTER TABLE users 
  ALTER unsubscribe_passkey SET NOT NULL;

COMMIT;

