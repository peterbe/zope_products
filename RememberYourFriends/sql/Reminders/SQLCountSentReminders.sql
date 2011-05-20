<params>
uid
</params>

SELECT
  COUNT(sr.srid) AS count
  
FROM
  sent_reminders sr,
  reminders r
  
WHERE
  r.rid = sr.rid
  AND
  r.uid = <dtml-sqlvar uid type="int">
  
