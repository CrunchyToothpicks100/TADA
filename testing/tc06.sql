DELETE FROM base_position
WHERE id = (
    SELECT p.id
    FROM base_position p
    JOIN base_company c ON p.company_id = c.id
    WHERE p.title = 'Backend Engineer'
      AND c.slug = 'acme-corp'
    LIMIT 1
);