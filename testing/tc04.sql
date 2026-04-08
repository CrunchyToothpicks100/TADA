-- tc04
-- Validate Foreign Key Constraint on Submission 
INSERT INTO base_submission (candidate_id, status, created_at)
VALUES (
    (SELECT MAX(id) + 999 FROM base_candidate),
    'new',
    NOW()
);