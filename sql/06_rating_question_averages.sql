-- =============================================================================
-- 06_rating_question_averages.sql
-- Average rating score per question, across all finished submissions.
-- =============================================================================

SELECT
    q.prompt,
    COALESCE(co.title, '(global)')              AS company,
    COALESCE(p.title,  '(all positions)')       AS position,
    COUNT(a.id)                                 AS response_count,
    ROUND(AVG(a.int_value), 2)                  AS avg_rating,
    MIN(a.int_value)                            AS min_rating,
    MAX(a.int_value)                            AS max_rating
FROM base_answer a
JOIN base_question q        ON q.id = a.question_id
JOIN base_submission s      ON s.id = a.submission_id
LEFT JOIN base_company co   ON co.id = q.company_id
LEFT JOIN base_position p   ON p.id = q.position_id
WHERE q.question_type = 'rating'
  AND s.status = 'finished'
  AND a.int_value IS NOT NULL
GROUP BY q.id, q.prompt, co.title, p.title
ORDER BY avg_rating DESC;
