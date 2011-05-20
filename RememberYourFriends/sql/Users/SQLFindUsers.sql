<params>
uid
email
passkey
first_name
last_name
order_by
reverse
</params>

SELECT 
 u.*,
 TO_CHAR(u.add_date, 'Day DD Mon') AS add_date_formatted,
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

<dtml-if "uid or email or passkey or first_name or last_name">
WHERE
  1 = 0
  
  <dtml-if "uid">
    OR
    u.uid = <dtml-sqlvar uid type="int">
  </dtml-if>
 
  <dtml-if "email">
    OR 
    u.email ILIKE <dtml-sqlvar email type="string">
  </dtml-if>
  
  <dtml-if "passkey">
    OR 
    u.passkey ILIKE <dtml-sqlvar passkey type="string">
  </dtml-if>
  
  <dtml-if "first_name">
    OR 
    d.first_name ILIKE <dtml-sqlvar first_name type="string">
  </dtml-if>
  
  <dtml-if "last_name">
    OR 
    d.last_name ILIKE <dtml-sqlvar last_name type="string">
  </dtml-if>

</dtml-if>
  
<dtml-if "order_by">
ORDER BY <dtml-var "order_by">
<dtml-if "reverse">DESC<dtml-else>ASC</dtml-if>
</dtml-if>