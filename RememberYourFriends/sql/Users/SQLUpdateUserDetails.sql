<params>
duid
first_name
last_name
sex
website
country
birthday
birthmonth
birthyear
</params>

UPDATE user_details 
SET
  first_name = <dtml-sqlvar first_name type="string">,
  last_name = <dtml-sqlvar last_name type="string">,
  sex = <dtml-sqlvar sex type="string">,
  website = <dtml-sqlvar website type="string">,
  country = <dtml-sqlvar country type="string">,
  birthday = <dtml-sqlvar birthday type="int">,
  birthmonth = <dtml-sqlvar birthmonth type="int">,
  birthyear = <dtml-sqlvar birthyear type="int">,  
  
  modify_date = NOW()
  
WHERE
  duid = <dtml-sqlvar duid type="int">