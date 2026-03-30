-- =============================================================================
-- 07_candidates_without_submissions.sql
-- Candidates who have a user account but have never finished an application.
-- Useful for identifying drop-off or unclaimed profiles.
-- =============================================================================

SELECT
    c.first_name,
    c.last_name,
    c.email,
    c.created_at,
    -- how many submissions they started (but never finished)
    (
        SELECT COUNT(*)
        FROM base_submission s
        WHERE s.candidate_id = c.id
    ) AS total_submissions_started
FROM base_candidate c
LEFT JOIN base_submission finished_sub
    ON finished_sub.candidate_id = c.id
   AND finished_sub.status = 'finished'
WHERE c.user_id IS NOT NULL        -- only registered candidates
  AND finished_sub.id IS NULL      -- no finished submission found
ORDER BY c.created_at;
