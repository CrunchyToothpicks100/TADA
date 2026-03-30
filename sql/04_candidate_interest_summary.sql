-- =============================================================================
-- 04_candidate_interest_summary.sql
-- Candidates with their interest labels and average interest strength.
-- Only includes candidates who have submitted at least one finished application.
-- =============================================================================

SELECT
    c.first_name,
    c.last_name,
    c.email,
    COUNT(i.id)                     AS interest_count,
    ROUND(AVG(i.strength_1_to_10), 2) AS avg_interest_strength,
    MAX(i.strength_1_to_10)         AS strongest_interest,
    MIN(i.strength_1_to_10)         AS weakest_interest
FROM base_candidate c
JOIN base_candidateinterest i ON i.candidate_id = c.id
WHERE EXISTS (
    SELECT 1
    FROM base_submission s
    WHERE s.candidate_id = c.id
      AND s.status = 'finished'
)
GROUP BY c.id, c.first_name, c.last_name, c.email
ORDER BY avg_interest_strength DESC;
