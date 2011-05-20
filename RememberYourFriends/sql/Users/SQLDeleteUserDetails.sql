<params>
uid
</params>

DELETE FROM
  user_details
WHERE 
  uid = <dtml-sqlvar uid type="int">