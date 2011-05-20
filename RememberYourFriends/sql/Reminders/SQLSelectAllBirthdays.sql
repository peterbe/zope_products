<params>
days_offset
</params>

SELECT

  r.*,
  DATE (TO_CHAR(NOW(), 'YYYY')||'-'||r.birthmonth::TEXT||'-'||r.birthday::TEXT) 
  AS birthday_this_year,
  
  (DATE (TO_CHAR(NOW(), 'YYYY')||'-'||r.birthmonth::TEXT||'-'||r.birthday::TEXT) - DATE(NOW()))
  AS days_till,
  
  (DATE (TO_CHAR(NOW(), 'YYYY')||'-'||birthmonth::TEXT||'-'||birthday::TEXT) - DATE(NOW())) = 0
  AS birthday_today
  
  
FROM
  reminders r,
  users u
  
WHERE
  u.uid = r.uid
  AND
  r.birthday IS NOT NULL
  AND
  r.birthmonth IS NOT NULL
  AND
  (DATE (TO_CHAR(NOW(), 'YYYY')||'-'||r.birthmonth::TEXT||'-'||r.birthday::TEXT) - DATE(NOW())) = <dtml-sqlvar days_offset type="int">
  
  
  
  