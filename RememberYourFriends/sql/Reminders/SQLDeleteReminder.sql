<params>
rid
</params>

DELETE FROM reminders
WHERE
  rid = <dtml-sqlvar rid type="int">