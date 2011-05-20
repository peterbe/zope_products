<params>
rid
pause
</params>

UPDATE reminders
SET
  paused_date = <dtml-if "pause">NOW()<dtml-else>'infinity'</dtml-if>,
  modify_date = NOW()
  
WHERE
  rid = <dtml-sqlvar rid type="int">
  