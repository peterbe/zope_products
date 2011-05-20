<params>
uid
</params>

SELECT COUNT(rid) AS count
FROM reminders
WHERE
  uid = <dtml-sqlvar uid type="int">