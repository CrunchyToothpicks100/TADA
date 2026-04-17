-- tc05
-- Validate Cascade Delete Behavior
-- Create test candidate
INSERT INTO base_candidate (external_id, email, first_name, last_name, phone, linkedin_url, bio, created_at)
VALUES (gen_random_uuid(), 'cascade@test.com', 'Cascade', 'Test', '555-0000', '', '', NOW());

-- Create submission tied to that candidate
INSERT INTO base_submission (external_id, candidate_id, status, payload, needs_claim, created_at)
VALUES (
    gen_random_uuid(),
    (SELECT id FROM base_candidate WHERE email = 'cascade@test.com'),
    'new',
    '{}',
    false,
    NOW()
);

-- Delete candidate
DELETE FROM base_candidate WHERE email = 'cascade@test.com';

-- Verify cascade
SELECT * FROM base_submission
WHERE candidate_id NOT IN (SELECT id FROM base_candidate);
