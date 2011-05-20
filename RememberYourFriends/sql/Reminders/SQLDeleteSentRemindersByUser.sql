<params>
uid
</params>

DELETE FROM sent_reminders
WHERE
  rid  IN (SELECT rid
           FROM reminders
           WHERE uid = <dtml-sqlvar uid type="int">)
           