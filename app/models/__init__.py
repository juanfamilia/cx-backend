from app.models.user_model import User
from app.models.company_model import Company

# Quality Framework (Service Quality model) — ver docs/METHODOLOGY.md
from app.models.industry_model import Industry
from app.models.framework_model import Framework, FrameworkDimension
from app.models.quality_competency_model import (
    QualityCompetency,
    CompetencyIndicator,
    CompetencyFrameworkRef,
)
from app.models.industry_template_model import IndustryTemplate
from app.models.company_competency_config_model import CompanyCompetencyConfig
