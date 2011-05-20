<params>
passkey
</params>

SELECT *
FROM users
WHERE
  passkey = <dtml-sqlvar passkey type="string">
  AND
  inactive_date > NOW()