from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from shared.models.user_evaluation_summary_model import (
    CompanyUserEvaluation,
    ManagerSummary,
    SuperadminSummary,
    UserEvaluationSummary,
)
from app.utils.exeptions import NotFoundException


async def get_user_evaluation_summary(
    session: AsyncSession, user_id: int
) -> UserEvaluationSummary:
    
    from sqlalchemy import text
    
    query = text("""
        SELECT 
            user_id,
            rechazadas,
            aprobadas,
            ediciones_pendientes,
            enviadas,
            actualizadas
        FROM user_evaluation_summary
        WHERE user_id = :user_id
        LIMIT 1
    """)
    
    result = await session.execute(query, {"user_id": user_id})
    row = result.fetchone()
    
    if not row:
        raise NotFoundException("Summary not found")
    
    summary = UserEvaluationSummary(
        user_id=row[0],
        rechazadas=row[1],
        aprobadas=row[2],
        ediciones_pendientes=row[3],
        enviadas=row[4],
        actualizadas=row[5]
    )

    return summary


async def get_company_users_evaluations(
    session: AsyncSession, company_id: int
) -> CompanyUserEvaluation:
    
    # Query directo a la VIEW usando text SQL para evitar problemas de reflexión
    from sqlalchemy import text
    
    query = text("""
        SELECT 
            company_id,
            gerentes,
            evaluadores,
            evaluaciones_aprobadas,
            evaluaciones_rechazadas
        FROM company_users_evaluations
        WHERE company_id = :company_id
        LIMIT 1
    """)
    
    result = await session.execute(query, {"company_id": company_id})
    row = result.fetchone()
    
    if not row:
        raise NotFoundException("Data not found")
    
    # Convertir el resultado a objeto CompanyUserEvaluation
    summary = CompanyUserEvaluation(
        company_id=row[0],
        gerentes=row[1],
        evaluadores=row[2],
        evaluaciones_aprobadas=row[3],
        evaluaciones_rechazadas=row[4]
    )

    return summary


async def get_manager_summary(session: AsyncSession, company_id: int) -> ManagerSummary:
    
    from sqlalchemy import text
    
    query = text("""
        SELECT 
            user_id,
            company_id,
            zonas_asignadas,
            evaluadores_asignados,
            active_campaigns
        FROM manager_summary
        WHERE company_id = :company_id
        LIMIT 1
    """)
    
    result = await session.execute(query, {"company_id": company_id})
    row = result.fetchone()
    
    if not row:
        raise NotFoundException("Data not found")
    
    summary = ManagerSummary(
        user_id=row[0],
        company_id=row[1],
        zonas_asignadas=row[2],
        evaluadores_asignados=row[3],
        active_campaigns=row[4]
    )

    return summary


async def get_superadmin_summary(session: AsyncSession) -> SuperadminSummary:
    
    from sqlalchemy import text
    
    query = text("""
        SELECT 
            superadmin_id,
            total_empresas,
            empresas_vigentes,
            empresas_caducadas,
            usuarios_totales
        FROM superadmin_summary
        LIMIT 1
    """)
    
    result = await session.execute(query)
    row = result.fetchone()
    
    if not row:
        raise NotFoundException("Data not found")
    
    summary = SuperadminSummary(
        superadmin_id=row[0],
        total_empresas=row[1],
        empresas_vigentes=row[2],
        empresas_caducadas=row[3],
        usuarios_totales=row[4]
    )

    return summary
