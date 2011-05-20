<params>
uid
</params>

DELETE FROM
  sent_invitations
WHERE
  uid = <dtml-sqlvar uid type="int">
  