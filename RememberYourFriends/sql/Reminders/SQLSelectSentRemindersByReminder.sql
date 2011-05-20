<params>
rid
order
reverse
limit
</params>

SELECT *
FROM sent_reminders
WHERE
  rid = <dtml-sqlvar rid type="int">
  
<dtml-if "order">
ORDER BY <dtml-var order>
<dtml-if "reverse">DESC<dtml-else>ASC</dtml-if>
</dtml-if>

<dtml-if "limit">
LIMIT <dtml-var "limit">
</dtml-if>