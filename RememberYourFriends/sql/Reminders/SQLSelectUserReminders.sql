<params>
uid
order
reverse
only_with_email
include_invite_option
</params>

SELECT 
  *,
  (SELECT COUNT(sr.srid)
   FROM sent_reminders sr
   WHERE sr.rid = reminders.rid) AS count_sent_reminders,
  paused_date < NOW() AS paused,
  ((next_date::DATE + snooze) - NOW()::DATE) AS age_days,
  (TO_CHAR(next_date, 'YYYY')::INT - TO_CHAR(NOW(), 'YYYY')::INT) AS age_year,
  TO_CHAR(next_date, 'HH24:MI am') AS next_date_day_formatted,
  TO_CHAR(next_date, 'Day DD Mon') AS next_date_week_formatted,  
  TO_CHAR(next_date, 'DD Mon') AS next_date_month_formatted,
  TO_CHAR(next_date, 'DD/MM/YY') AS next_date_year_formatted
  
  <dtml-if "include_invite_option">
  , email <> '' AND LOWER(email) NOT IN (
           (SELECT LOWER(si.email)
            FROM sent_invitations si 
            WHERE
              (si.add_date::DATE - NOW()::DATE) < 1
            ) UNION (
             SELECT LOWER(u.email)
             FROM users u
             WHERE
               u.uid != <dtml-sqlvar uid type="int">
            )
            ) AS is_invitable
  </dtml-if>
            
FROM reminders
WHERE
  uid = <dtml-sqlvar uid type="int">
  
  <dtml-if "only_with_email">
  AND email <> ''
  </dtml-if>
  
<dtml-if "order">
ORDER BY <dtml-var "order">
<dtml-if "reverse">DESC<dtml-else>ASC</dtml-if>
</dtml-if>