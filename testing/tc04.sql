-- tc04
-- Validate Foreign Key Constraint on Submission 
INSERT INTO base_submission (external_id, candidate_id, status, payload, needs_claim, created_at)
VALUES (
    gen_random_uuid(),
    (SELECT MAX(id) + 999 FROM base_candidate),
    'new',
    '{}',
    false,
    NOW()
);
