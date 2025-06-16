from typing import Optional
from sqlmodel import Field, SQLModel


class UserEvaluationSummary(SQLModel, table=True):
    __tablename__ = "user_evaluation_summary"
    user_id: int = Field(primary_key=True)
    rechazadas: Optional[int]
    aprobadas: Optional[int]
    ediciones_pendientes: Optional[int]
    enviadas: Optional[int]
    actualizadas: Optional[int]


class CompanyUserEvaluation(SQLModel, table=True):
    __tablename__ = "company_users_evaluations"
    company_id: int = Field(primary_key=True)
    gerentes: Optional[int]
    evaluadores: Optional[int]
    evaluaciones_aprobadas: Optional[int]
    evaluaciones_rechazadas: Optional[int]


class ManagerSummary(SQLModel, table=True):
    __tablename__ = "manager_summary"
    user_id: int = Field(primary_key=True)
    company_id: int
    zonas_asignadas: int
    evaluadores_asignados: int
    active_campaigns: int


class SuperadminSummary(SQLModel, table=True):
    __tablename__ = "superadmin_summary"
    superadmin_id: int = Field(primary_key=True)
    total_empresas: int
    empresas_vigentes: int
    empresas_caducadas: int
    usuarios_totales: int
