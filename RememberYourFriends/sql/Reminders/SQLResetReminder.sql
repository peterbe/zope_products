<params>
rid
</params>

UPDATE reminders
SET
  next_date = NOW() + periodicity::TEXT::INTERVAL,
  snooze = 0
  
WHERE
  rid = <dtml-sqlvar rid type="int">
  