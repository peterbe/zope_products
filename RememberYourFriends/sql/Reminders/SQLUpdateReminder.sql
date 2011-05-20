<params>
rid
name
email
periodicity
birthday
birthmonth
birthyear
</params>

UPDATE reminders 
SET
  name = <dtml-sqlvar name type="string">,
  email = <dtml-sqlvar email type="string">,
  periodicity = <dtml-sqlvar periodicity type="string">,
  birthday = <dtml-if "birthday"><dtml-sqlvar birthday type="int"><dtml-else>NULL</dtml-if>,
  birthmonth = <dtml-if "birthmonth"><dtml-sqlvar birthmonth type="int"><dtml-else>NULL</dtml-if>,
  birthyear = <dtml-if "birthyear"><dtml-sqlvar birthyear type="int"><dtml-else>NULL</dtml-if>,
  
  modify_date = NOW()

WHERE
  rid = <dtml-sqlvar rid type="int">
