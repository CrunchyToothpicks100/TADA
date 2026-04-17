-- tc10
-- Validate Multi-Choice Uniqueness
-- Get an existing multi-answer (Globex Data Scientist case)
-- First insert
WITH target_answer AS (
    SELECT a.id
    FROM base_answer a
    JOIN base_submission s ON a.submission_id = s.id
    JOIN base_candidate c ON s.candidate_id = c.id
    WHERE c.email = 'carlos.r@example.com'
    LIMIT 1
),
target_choice AS (
    SELECT id FROM base_questionchoice WHERE value = 'tensorflow'
)
INSERT INTO base_answerchoice (answer_id, choice_id)
SELECT ta.id, tc.id FROM target_answer ta, target_choice tc;

-- Duplicate insert (should fail)
WITH target_answer AS (
    SELECT a.id
    FROM base_answer a
    JOIN base_submission s ON a.submission_id = s.id
    JOIN base_candidate c ON s.candidate_id = c.id
    WHERE c.email = 'carlos.r@example.com'
    LIMIT 1
),
target_choice AS (
    SELECT id FROM base_questionchoice WHERE value = 'tensorflow'
)
INSERT INTO base_answerchoice (answer_id, choice_id)
SELECT ta.id, tc.id FROM target_answer ta, target_choice tc;
