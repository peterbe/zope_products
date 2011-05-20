<params>
uid
passkey
</params>

UPDATE users
SET
  unsubscribe_passkey = <dtml-sqlvar passkey type="string">,
  modify_date = NOW()
  
WHERE
  uid = <dtml-sqlvar uid type="int">