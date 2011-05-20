<params>
rid
interval
reset_next_date
</params>

UPDATE reminders
SET

  <dtml-if "reset_next_date">
  next_date = NOW(),
  </dtml-if>

  snooze = date_part('day', interval <dtml-sqlvar interval type="string">),
  modify_date = NOW()
  
WHERE 
  rid = <dtml-sqlvar rid type="int">
  