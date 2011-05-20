<params>
uid
email
passkey
temporary_passkey
name
html_emails
</params>

INSERT INTO users
(uid, email, passkey, temporary_passkey, name, html_emails)
VALUES (
<dtml-sqlvar uid type="int">,
<dtml-sqlvar email type="string">,
<dtml-sqlvar passkey type="string">,
<dtml-sqlvar temporary_passkey type="string">,
<dtml-sqlvar name type="string">,
<dtml-if "html_emails">true<dtml-else>false</dtml-if>
)