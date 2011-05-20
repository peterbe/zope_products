<params>
uid
email
</params>

SELECT 
  *,
  (add_date::DATE - NOW()::DATE) AS age_days
  
FROM sent_invitations
WHERE
  email ILIKE <dtml-sqlvar email type="string">
  <dtml-if "uid">
  AND
  uid = <dtml-sqlvar uid type="int">
  </dtml-if>