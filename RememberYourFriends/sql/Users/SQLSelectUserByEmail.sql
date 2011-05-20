<params>
email
</params>

SELECT * 
FROM users
WHERE 
  email ILIKE <dtml-sqlvar email type="string">