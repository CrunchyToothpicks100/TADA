-- tc01
-- Validate NOT NULL Constraint on Candidate Email
INSERT INTO base_candidate (email, first_name, last_name, phone)
VALUES (NULL, 'Test', 'User', '555-9999');