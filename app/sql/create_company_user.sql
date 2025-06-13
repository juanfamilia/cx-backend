CREATE USER empresa_2_user WITH PASSWORD 'SbuurmNw44cKBEZ*';

-- Permitir conexión a la base
GRANT CONNECT ON DATABASE railway TO empresa_2_user;

-- Permitir uso del esquema público
GRANT USAGE ON SCHEMA public TO empresa_2_user;

-- Dar acceso a las tablas
GRANT SELECT ON
  users,
  companies,
  payments,
  survey_forms,
  survey_sections,
  survey_aspects,
  campaigns,
  campaign_users,
  campaign_zones,
  evaluations,
  evaluation_answers,
  user_zones,
  zones
TO empresa_2_user;

-- Establecer la variable automáticamente
ALTER ROLE empresa_2_user SET app.company_id = '2';

-- Revocar acceso a datos sensibles
REVOKE SELECT (hashed_password) ON users FROM empresa_2_user;

-- (Opcional) Revocar escritura si no la necesitas
REVOKE INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public FROM empresa_2_user;