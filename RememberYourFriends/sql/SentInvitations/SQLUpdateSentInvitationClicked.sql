<params>
siid
clicked
</params>

UPDATE sent_invitations
SET
  clicked_link = <dtml-if "clicked">true<dtml-else>false</dtml-if>

WHERE
  siid = <dtml-sqlvar siid type="int">