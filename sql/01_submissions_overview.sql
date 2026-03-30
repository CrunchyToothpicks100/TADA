-- =============================================================================
-- 01_submissions_overview.sql
-- Full submission details: candidate name, position, company, and status.
-- =============================================================================

SELECT
    c.first_name,
    c.last_name,
    c.email,
    p.title        AS position_title,
    co.title       AS company_name,
    s.status
FROM base_submission s
JOIN base_candidate c    ON c.id = s.candidate_id
JOIN base_position p     ON p.id = s.position_id
JOIN base_company co     ON co.id = p.company_id
WHERE s.status != 'discarded'
ORDER BY s.created_at DESC;
