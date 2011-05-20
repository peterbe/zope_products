<params>
uid
</params>

SELECT *
FROM users
WHERE
  uid = <dtml-sqlvar uid type="int">