-- Duplicate insert (this record should already exist from sample data, should fail)
INSERT INTO base_companystaff (user_id, company_id, is_admin, created_at)
VALUES (
    (SELECT id FROM auth_user WHERE username = 'alice.admin@example.com'),
    (SELECT id FROM base_company WHERE slug = 'acme-corp'),
    false,
    NOW()
);