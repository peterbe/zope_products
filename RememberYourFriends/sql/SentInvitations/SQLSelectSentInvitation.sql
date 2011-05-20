<params>
siid
</params>

SELECT *
FROM 
  sent_invitations
WHERE
  siid = <dtml-sqlvar siid type="int">