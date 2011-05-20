<params>
uid
</params>

DELETE FROM 
  reminders
WHERE 
  uid = <dtml-sqlvar uid type="int">