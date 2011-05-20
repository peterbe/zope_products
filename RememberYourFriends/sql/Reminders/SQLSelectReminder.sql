<params>
rid
</params>

SELECT 
  *,
  paused_date < NOW() AS paused,
  ((next_date + (snooze::char||' days')::interval)::DATE - NOW()::DATE) AS age_days,
  (TO_CHAR((next_date + (snooze::char||' days')::interval), 'YYYY')::INT - TO_CHAR(NOW(), 'YYYY')::INT) AS age_years,
  TO_CHAR((next_date + (snooze::char||' days')::interval), 'HH24:MI am') AS next_date_day_formatted,
  TO_CHAR((next_date + (snooze::char||' days')::interval), 'Day DD Mon') AS next_date_week_formatted,
  TO_CHAR((next_date + (snooze::char||' days')::interval), 'DD Mon') AS next_date_month_formatted,  
  TO_CHAR((next_date + (snooze::char||' days')::interval), 'DD/MM/YY') AS next_date_year_formatted
  
FROM reminders
WHERE
  rid = <dtml-sqlvar rid type="int">