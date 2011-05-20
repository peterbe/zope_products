<params>
uid
</params>

SELECT 
 u.*,
 TO_CHAR(u.add_date, 'Day DD Mon') AS add_date_formatted,
 TO_CHAR(u.modify_date, 'Day DD Mon') AS modify_date_formatted,
 d.duid,
 d.first_name, 
 d.last_name,
 d.country,
 d.website,
 d.sex,
 d.birthday,
 d.birthmonth,
 d.birthyear,
 (SELECT COUNT(r.rid)
  FROM reminders r
  WHERE r.uid = u.uid) AS count_reminders,
  
 (SELECT COUNT(sr.srid)
  FROM sent_reminders sr, reminders r
  WHERE
    r.rid=sr.rid AND r.uid = u.uid) AS count_sent_reminders,
    
 (SELECT COUNT(si.siid)
  FROM sent_invitations si
  WHERE si.uid = u.uid) AS count_sent_invitations,
  
 (SELECT COUNT(si.siid)
  FROM sent_invitations si
  WHERE si.uid = u.uid
    AND si.clicked_link = true) AS count_sent_invitations_clicked 
 
FROM 
  users u
  
LEFT OUTER JOIN
  user_details d
  ON 
  u.uid = d.uid
  
WHERE
  u.uid = <dtml-sqlvar uid type="int">
