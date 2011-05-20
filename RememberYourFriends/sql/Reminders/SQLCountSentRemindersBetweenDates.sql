<params>
start_date
end_date
</params>

SELECT
  COUNT(*) AS count

FROM 
  sent_reminders
  
WHERE
  add_date >= <dtml-sqlvar start_date type="string">
  AND
  add_date < <dtml-sqlvar end_date type="string"> 
  