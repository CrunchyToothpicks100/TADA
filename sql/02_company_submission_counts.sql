-- =============================================================================
-- 02_company_submission_counts.sql
-- How many submissions each company has received, broken down by status.
-- =============================================================================

SELECT
    co.title                                                        AS company,
    COUNT(s.id)                                                     AS total_submissions,
    COUNT(s.id) FILTER (WHERE s.status = 'new')                    AS new_count,
    COUNT(s.id) FILTER (WHERE s.status = 'finished')               AS finished_count,
    COUNT(s.id) FILTER (WHERE s.status = 'discarded')              AS discarded_count
FROM base_company co
LEFT JOIN base_position p  ON p.company_id = co.id
LEFT JOIN base_submission s ON s.position_id = p.id
WHERE co.is_active = TRUE
GROUP BY co.id, co.title
ORDER BY total_submissions DESC;
