<params>
duid
uid
</params>

INSERT INTO user_details(duid, uid)
VALUES (
<dtml-sqlvar duid type="int">, 
<dtml-sqlvar uid type="int">
)