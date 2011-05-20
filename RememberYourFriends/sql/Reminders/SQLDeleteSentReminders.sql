<params>
rid
</params>

DELETE FROM sent_reminders
WHERE
  rid = <dtml-sqlvar rid type="int">