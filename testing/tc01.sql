-- tc01
-- Validate NOT NULL Constraint on Candidate Email
INSERT INTO base_candidate (external_id, email, first_name, last_name, phone)
VALUES (gen_random_uuid(), NULL, 'Test', 'User', '555-9999');