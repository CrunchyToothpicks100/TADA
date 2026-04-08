-- tc09
-- Validate Unique Answer per Question per Submission
-- First insert (may already exist depending on seed)
INSERT INTO base_answer (submission_id, question_id, created_at)
VALUES (
    (SELECT s.id
     FROM base_submission s
     JOIN base_candidate c ON s.candidate_id = c.id
     WHERE c.email = 'john.doe@example.com'
     LIMIT 1),
    (SELECT id FROM base_question LIMIT 1),
    NOW()
);

-- Duplicate insert (should fail)
INSERT INTO base_answer (submission_id, question_id, created_at)
VALUES (
    (SELECT s.id
     FROM base_submission s
     JOIN base_candidate c ON s.candidate_id = c.id
     WHERE c.email = 'john.doe@example.com'
     LIMIT 1),
    (SELECT id FROM base_question LIMIT 1),
    NOW()
);