<params>
uid
</params>

DELETE FROM users
WHERE
  uid = <dtml-sqlvar uid type="int">