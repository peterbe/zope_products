<params>
rid
</params>

SELECT COUNT(srid) AS count
FROM sent_reminders
WHERE
  rid = <dtml-sqlvar rid type="int">