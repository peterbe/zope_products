<params>
rid
snoozed
</params>
INSERT INTO sent_reminders (rid, snoozed)
VALUES (
<dtml-sqlvar rid type="int">, 
<dtml-sqlvar snoozed type="int">
)