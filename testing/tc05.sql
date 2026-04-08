-- tc05
-- Validate Cascade Delete Behavior
-- Create test candidate
INSERT INTO base_candidate (email, first_name, last_name, phone)
VALUES ('cascade@test.com', 'Cascade', 'Test', '555-0000');

-- Create submission tied to that candidate (fields not included are allowed to be null and blank in models.py)
INSERT INTO base_submission (candidate_id, status, created_at)
VALUES (
    (SELECT id FROM base_candidate WHERE email = 'cascade@test.com'),
    'new',
    NOW()
);

-- Delete candidate
DELETE FROM base_candidate WHERE email = 'cascade@test.com';

-- Verify cascade
SELECT * FROM base_submission
WHERE candidate_id NOT IN (SELECT id FROM base_candidate);