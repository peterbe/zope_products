<params>
limit
</params>

SELECT 
  u.uid,
  u.email,
  ud.first_name,
  ud.last_name,
  (SELECT COUNT(sr.srid)
   FROM sent_reminders sr, reminders r
   WHERE
     r.rid=sr.rid
     AND
     r.uid=u.uid) AS count_sent_reminders,

  (SELECT COUNT(sr.srid)
   FROM sent_reminders sr, reminders r
   WHERE
     r.rid=sr.rid
     AND
     r.uid=u.uid
     AND
     sr.add_date < (NOW() - INTERVAL '1 month')
     ) AS count_sent_reminders_last_month
   
FROM
  users u
  
LEFT OUTER JOIN
  user_details ud
  ON
  u.uid = ud.uid
  
ORDER BY   
  count_sent_reminders DESC
  
  
<dtml-if "limit">
LIMIT <dtml-var "limit">
</dtml-if>