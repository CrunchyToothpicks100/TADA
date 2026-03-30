-- =============================================================================
-- 08_top_interests_by_company.sql
-- Most common candidate interests among applicants per company.
-- =============================================================================

SELECT
    co.title                        AS company,
    i.label                         AS interest,
    COUNT(DISTINCT c.id)            AS candidate_count,
    ROUND(AVG(i.strength_1_to_10), 2) AS avg_strength
FROM base_company co
JOIN base_position p        ON p.company_id = co.id
JOIN base_submission s      ON s.position_id = p.id
JOIN base_candidate c       ON c.id = s.candidate_id
JOIN base_candidateinterest i ON i.candidate_id = c.id
WHERE co.is_active = TRUE
  AND s.status IN ('new', 'finished')
GROUP BY co.id, co.title, i.label
HAVING COUNT(DISTINCT c.id) >= 1
ORDER BY co.title, candidate_count DESC;
