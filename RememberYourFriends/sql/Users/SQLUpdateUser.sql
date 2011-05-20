<params>
uid
html_emails
</params>

UPDATE users
SET
  html_emails = <dtml-if "html_emails">true<dtml-else>false</dtml-if>,
  modify_date = NOW()
WHERE
  uid = <dtml-sqlvar uid type="int">