<params>
uid
</params>

UPDATE users
SET 
  last_login_time = NOW()
  
WHERE
  uid = <dtml-sqlvar uid type="int">