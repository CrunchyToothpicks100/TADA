-- tc07
-- Validate Enum Constraint (Submission Status)
INSERT INTO base_submission (external_id, candidate_id, status, payload, needs_claim, created_at)
VALUES (
    gen_random_uuid(),
    (SELECT id FROM base_candidate WHERE email = 'john.doe@example.com'),
    'invalid_status',
    '{}',
    false,
    NOW()
);