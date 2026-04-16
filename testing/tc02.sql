-- tc02
-- Validate Email Format Constraint
INSERT INTO base_candidate (external_id, email, first_name, last_name, phone, linkedin_url, bio)
VALUES (gen_random_uuid(), 'invalidemail.com', 'Bad', 'Email', '555-9999', '', '');