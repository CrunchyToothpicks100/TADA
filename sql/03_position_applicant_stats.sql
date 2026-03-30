-- =============================================================================
-- 03_position_applicant_stats.sql
-- Per-position applicant counts and average days to finish.
-- =============================================================================

SELECT
    p.title                                                         AS position,
    co.title                                                        AS company,
    p.employment_type,
    COUNT(s.id)                                                     AS total_applicants,
    COUNT(s.id) FILTER (WHERE s.status = 'finished')               AS completed,
    -- EXTRACT(EPOCH FROM interval) converts the difference between finished_at and
    -- created_at into total seconds, then divides by 3600 to get hours.
    -- FILTER excludes unfinished submissions. ROUND(..., 1) gives one decimal place.
    ROUND(
        AVG(
            EXTRACT(EPOCH FROM (s.finished_at - s.created_at)) / 3600
        ) FILTER (WHERE s.finished_at IS NOT NULL),
        1
    )                                                               AS avg_hours_to_finish
FROM base_position p
JOIN base_company co       ON co.id = p.company_id
LEFT JOIN base_submission s ON s.position_id = p.id
WHERE p.is_active = TRUE
GROUP BY p.id, p.title, co.title, p.employment_type
HAVING COUNT(s.id) > 0
ORDER BY total_applicants DESC;
