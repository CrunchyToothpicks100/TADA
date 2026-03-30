-- =============================================================================
-- 05_staff_per_company.sql
-- Staff roster per company: username, email, role, and join date.
-- =============================================================================

SELECT
    co.title                                    AS company,
    u.username,
    u.email,
    CASE WHEN cs.is_admin THEN 'Admin'
         ELSE 'Staff' END                       AS role,
    cs.created_at                               AS joined_at
FROM base_companystaff cs
JOIN base_company co   ON co.id = cs.company_id
JOIN auth_user u       ON u.id = cs.user_id
WHERE co.is_active = TRUE
  AND u.is_active = TRUE
ORDER BY co.title, cs.is_admin DESC, u.username;
