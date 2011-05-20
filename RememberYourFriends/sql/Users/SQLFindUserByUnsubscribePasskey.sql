<params>
passkey
</params>

SELECT *
FROM users 
WHERE
  unsubscribe_passkey ILIKE <dtml-sqlvar passkey type="string">