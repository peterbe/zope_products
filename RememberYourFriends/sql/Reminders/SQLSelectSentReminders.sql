<params>
uid
offset
limit
</params>

SELECT
  sr.srid,
  sr.add_date AS sent_date,
  TO_CHAR(sr.add_date, 'Day DD Month YYYY') AS sent_date_formatted,
  r.*,
  TO_CHAR(r.next_date, 'Day DD Month YYYY') AS next_date_formatted
  
FROM
  sent_reminders sr,
  reminders r
  
WHERE
  r.rid = sr.rid
  AND
  r.uid = <dtml-sqlvar uid type="int">
  
  
ORDER BY
  sr.add_date DESC
  
LIMIT <dtml-var limit>
OFFSET <dtml-var offset>
  
  