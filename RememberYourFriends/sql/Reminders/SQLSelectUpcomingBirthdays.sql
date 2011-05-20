<params>
uid
sort
</params>


SELECT 
  *,
  DATE (TO_CHAR(NOW(), 'YYYY')||'-'||birthmonth::TEXT||'-'||birthday::TEXT)
  AS birthday_this_year,
  
  (DATE (TO_CHAR(NOW(), 'YYYY')||'-'||birthmonth::TEXT||'-'||birthday::TEXT) - NOW()) 
  AS days_till,
  
  (DATE (TO_CHAR(NOW(), 'YYYY')||'-'||birthmonth::TEXT||'-'||birthday::TEXT) - DATE(NOW())) = 0
  AS birthday_today
  
  
  
FROM
  reminders
  
WHERE
  uid = <dtml-sqlvar uid type="int">
  AND
  birthday IS NOT NULL
  AND
  birthmonth IS NOT NULL
  AND
--  (DATE (TO_CHAR(NOW(), 'YYYY')||'-'||birthmonth::TEXT||'-'||birthday::TEXT) - DATE(NOW())) >= INTERVAL '1 day'
  (DATE (TO_CHAR(NOW(), 'YYYY')||'-'||birthmonth::TEXT||'-'||birthday::TEXT) - DATE(NOW())) >= 0
  AND
  (DATE (TO_CHAR(NOW(), 'YYYY')||'-'||birthmonth::TEXT||'-'||birthday::TEXT) - DATE(NOW())) <= INTERVAL '3 months'
  

ORDER BY birthday_this_year