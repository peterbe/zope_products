<params>
first
</params>

SELECT
  *
FROM 
  sent_reminders

ORDER BY
  add_date
  <dtml-if "first">ASC<dtml-else>DESC</dtml-if>
 
LIMIT 1  