<params>
rid
uid
name
email
periodicity
birthday
birthmonth
birthyear
</params>

INSERT INTO reminders (
rid, uid, name, email, next_date, periodicity,
birthday, birthmonth, birthyear
) VALUES (
<dtml-sqlvar rid type="int">,
<dtml-sqlvar uid type="int">,
<dtml-sqlvar name type="string">,
<dtml-sqlvar email type="string">,
NOW() + <dtml-sqlvar periodicity type="string">,
<dtml-sqlvar periodicity type="string">,
<dtml-if "birthday"><dtml-sqlvar birthday type="int"><dtml-else>NULL</dtml-if>,
<dtml-if "birthmonth"><dtml-sqlvar birthmonth type="int"><dtml-else>NULL</dtml-if>,
<dtml-if "birthyear"><dtml-sqlvar birthyear type="int"><dtml-else>NULL</dtml-if>

)
