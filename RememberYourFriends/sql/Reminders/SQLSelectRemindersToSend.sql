<params>
limit
order
</params>

SELECT 
  *,
  paused_date < NOW() AS paused
FROM reminders
WHERE
  (next_date::DATE + snooze) <= NOW()::DATE
  AND
  rid NOT IN (
    SELECT rid
    FROM sent_reminders
    WHERE
      add_date::DATE = NOW()::DATE
  )
  
<dtml-if "order">
ORDER BY <dtml-var order>
</dtml-if>
  
<dtml-if "limit">
LIMIT <dtml-var "limit">
</dtml-if>
    
    