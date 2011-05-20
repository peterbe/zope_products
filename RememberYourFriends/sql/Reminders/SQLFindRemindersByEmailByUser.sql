<params>
email
uid
</params>


SELECT 
  *
  
FROM
  reminders
  
WHERE
  uid = <dtml-sqlvar uid type="int">
  AND
  email ILIKE <dtml-sqlvar email type="string">