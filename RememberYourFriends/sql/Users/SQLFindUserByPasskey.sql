<params>
passkey
</params>

SELECT *
FROM users 
WHERE
  passkey ILIKE <dtml-sqlvar passkey type="string">