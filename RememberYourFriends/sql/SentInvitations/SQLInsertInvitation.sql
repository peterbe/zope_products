<params>
siid
uid
email
name
periodicity
html_email
</params>

INSERT INTO sent_invitations (
siid, uid, email, name, periodicity, html_email)
VALUES (
<dtml-sqlvar siid type="int">,
<dtml-sqlvar uid type="int">,
<dtml-sqlvar email type="string">,
<dtml-sqlvar name type="string">,
<dtml-sqlvar periodicity type="string">,
<dtml-if "html_email">true<dtml-else>false</dtml-if>
)

