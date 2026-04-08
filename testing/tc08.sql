-- tc08
-- Validate Interest Strength Range
INSERT INTO base_candidateinterest (candidate_id, label, strength_1_to_10, created_at)
VALUES (
    (SELECT id FROM base_candidate WHERE email = 'john.doe@example.com'),
    'Invalid Strength',
    15,
    NOW()
);