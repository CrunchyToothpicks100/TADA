INSERT INTO base_submission (candidate_id, status, created_at)
VALUES (
    (SELECT id FROM base_candidate WHERE email = 'john.doe@example.com'),
    'invalid_status',
    NOW()
);