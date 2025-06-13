CREATE POLICY rls_users
ON users
FOR SELECT
USING (company_id = current_setting('app.company_id')::int);

CREATE POLICY rls_companies
ON companies
FOR SELECT
USING (id = current_setting('app.company_id')::int);

CREATE POLICY rls_payments
ON payments
FOR SELECT
USING (company_id = current_setting('app.company_id')::int);

CREATE POLICY rls_survey_forms
ON survey_forms
FOR SELECT
USING (company_id = current_setting('app.company_id')::int);

CREATE POLICY rls_survey_sections ON survey_sections
FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM survey_forms
    WHERE survey_forms.id = survey_sections.form_id
    AND survey_forms.company_id = current_setting('app.empresa_id')::int
  )
);

CREATE POLICY rls_survey_aspects ON survey_aspects
FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM survey_sections s
    JOIN survey_forms f ON s.form_id = f.id
    WHERE s.id = survey_aspects.section_id
    AND f.company_id = current_setting('app.empresa_id')::int
  )
);

CREATE POLICY rls_campaigns
ON campaigns
FOR SELECT
USING (company_id = current_setting('app.company_id')::int);

CREATE POLICY rls_campaign_users
ON campaign_users
FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM campaigns
    WHERE campaigns.id = campaign_users.campaign_id
    AND campaigns.company_id = current_setting('app.empresa_id')::int
  )
);

CREATE POLICY rls_campaign_zones
ON campaign_zones
FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM campaigns
    WHERE campaigns.id = campaign_zones.campaign_id
    AND campaigns.company_id = current_setting('app.empresa_id')::int
  )
);

CREATE POLICY rls_evaluations
ON evaluations
FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM users
    WHERE users.id = evaluations.user_id
    AND users.company_id = current_setting('app.empresa_id')::int
  )
);

CREATE POLICY rls_evaluation_answers
ON evaluation_answers
FOR SELECT
USING (
  EXISTS (
    SELECT 1
    FROM evaluations e
    JOIN users u ON e.user_id = u.id
    WHERE e.id = evaluation_answers.evaluation_id
    AND u.company_id = current_setting('app.empresa_id')::int
  )
);

CREATE POLICY rls_user_zones ON user_zones
FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM users
    WHERE users.id = user_zones.user_id
    AND users.company_id = current_setting('app.empresa_id')::int
  )
);