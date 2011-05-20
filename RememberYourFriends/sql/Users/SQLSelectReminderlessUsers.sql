<params>
order
</params>

SELECT
  u.*,
  TO_CHAR(u.add_date, 'DD Mon') AS add_date_formatted
  
FROM
  users u
  
WHERE
  (SELECT COUNT(r.rid)
   FROM reminders r
   WHERE r.uid = u.uid) = 0
   