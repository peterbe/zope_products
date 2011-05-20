<params>
uid
order_by
reverse
</params>

SELECT
 LOWER(si.email) IN (SELECT LOWER(u.email)
                  FROM users u
                  WHERE
                    u.uid != <dtml-sqlvar uid type="int">) AS signed_up,
 si.*,
 TO_CHAR(si.add_date, 'Day DD Mon') AS add_date_formatted,
 (add_date::DATE - NOW()::DATE) AS age_days
 
FROM 
  sent_invitations si 
  
WHERE
  si.uid = <dtml-sqlvar uid type="int">
  
<dtml-if "order_by">
ORDER BY 
  <dtml-var "order_by">
  <dtml-if "reverse">DESC<dtml-else>ASC</dtml-if>
</dtml-if>
