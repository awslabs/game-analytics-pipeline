SELECT app_version,
    -- Cast the user rate to a decimal with two places after the dot, representing the user rate as a percentage.
    CAST(tx_users AS DECIMAL(10, 2)) AS rate_impacted_users,
    -- Cast the crash-free session rate to a decimal with two places after the dot, representing the rate as a percentage.
    CAST(tx_crash_free_sessions AS DECIMAL(10, 2)) AS rate_crash_free_sessions
FROM (
        SELECT json_extract_scalar(app_info, '$.app_version') as app_version,
            -- Calculate the rate of users affected by app exceptions. Count the distinct user IDs with exceptions,
            -- divide by the total distinct user IDs, multiply by 100 to convert to a percentage, and use floating-point division.
            (
                COUNT(
                    DISTINCT CASE
                        WHEN event_name = 'app_exception' THEN json_extract_scalar(user, '$.user_id')
                    END
                ) * 1.0 / COUNT(DISTINCT json_extract_scalar(user, '$.user_id'))
            ) * 100 AS tx_users,
            -- Calculate the crash-free session rate. Subtract the ratio of sessions with app exceptions from 1,
            -- multiply by 100 to convert to a percentage, and ensure floating-point division.
            (
                1.0 - (
                    COUNT(
                        DISTINCT CASE
                            WHEN event_name = 'app_exception' THEN json_extract_scalar(user, '$.session_id')
                        END
                    ) * 1.0 / COUNT(
                        DISTINCT json_extract_scalar(user, '$.session_id')
                    )
                )
            ) * 100 AS tx_crash_free_sessions
        FROM raw_events
        WHERE -- Filter records to include only those of the specific application (given in a function's parameter).
            application_name = '%%APPLICATION_NAME%%' -- Filter records to include only those on the current date.
            AND date(
                date_parse(CONCAT(year, '-', month, '-', day), '%Y-%m-%d')
            ) = current_date -- Filter records to include only those in the last hour.
            AND from_unixtime(event_timestamp) >= date_add('hour', -1, current_timestamp)
        GROUP BY json_extract_scalar(app_info, '$.app_version')
        HAVING count(
                distinct json_extract_scalar(user, '$.session_id')
            ) > 250
    )