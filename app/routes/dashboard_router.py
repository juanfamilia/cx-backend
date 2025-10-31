from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.services.user_evaluation_summary_services import (
    get_company_users_evaluations,
    get_manager_summary,
    get_superadmin_summary,
    get_user_evaluation_summary,
)
from app.services.dashboard_widgets_services import (
    get_nps_trend_data,
    get_status_breakdown_data,
    get_top_evaluators_data,
    get_companies_summary_data,
    get_manager_campaigns_data,
    get_shopper_campaigns_data,
    get_evaluation_by_month_data,
    get_ioc_ird_ces_averages,
)
from app.services.export_services import (
    export_dashboard_to_excel,
    generate_pdf_report,
    prepare_export_data,
)
from app.utils.deps import check_company_payment_status, get_auth_user
from datetime import datetime


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
    dependencies=[Depends(get_auth_user), Depends(check_company_payment_status)],
)


@router.get("/")
async def get_dashboard(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """Get role-based dashboard summary"""
    match request.state.user.role:
        case 0:
            superadmin_summary = await get_superadmin_summary(session)
            return superadmin_summary

        case 1:
            company_users_evaluations = await get_company_users_evaluations(
                session, request.state.user.company_id
            )
            return company_users_evaluations

        case 2:
            manager_summary = await get_manager_summary(
                session, request.state.user.company_id
            )
            return manager_summary

        case 3:
            user_evaluation_summary = await get_user_evaluation_summary(
                session, request.state.user.id
            )
            return user_evaluation_summary


# Widget Data Endpoints

@router.get("/widgets/nps-trend")
async def get_nps_trend_widget(
    request: Request,
    session: AsyncSession = Depends(get_db),
    days: int = Query(default=30, le=365),
):
    """Get NPS trend data for chart widget"""
    company_id = request.state.user.company_id if request.state.user.role != 0 else None
    data = await get_nps_trend_data(session, company_id, days)
    return data


@router.get("/widgets/status-breakdown")
async def get_status_breakdown_widget(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """Get evaluation status breakdown for pie chart"""
    company_id = request.state.user.company_id if request.state.user.role != 0 else None
    data = await get_status_breakdown_data(session, company_id)
    return data


@router.get("/widgets/top-evaluators")
async def get_top_evaluators_widget(
    request: Request,
    session: AsyncSession = Depends(get_db),
    limit: int = Query(default=5, le=20),
):
    """Get top evaluators by evaluation count"""
    company_id = request.state.user.company_id if request.state.user.role != 0 else None
    data = await get_top_evaluators_data(session, company_id, limit)
    return data


@router.get("/widgets/companies-summary")
async def get_companies_summary_widget(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """Get companies summary (superadmin only)"""
    if request.state.user.role != 0:
        return {"error": "Unauthorized"}
    
    data = await get_companies_summary_data(session)
    return data


@router.get("/widgets/manager-campaigns")
async def get_manager_campaigns_widget(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """Get campaigns for manager"""
    data = await get_manager_campaigns_data(session, request.state.user.id)
    return data


@router.get("/widgets/shopper-campaigns")
async def get_shopper_campaigns_widget(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """Get active campaigns for shopper"""
    data = await get_shopper_campaigns_data(session, request.state.user.id)
    return data


@router.get("/widgets/evaluations-by-month")
async def get_evaluations_by_month_widget(
    request: Request,
    session: AsyncSession = Depends(get_db),
    months: int = Query(default=6, le=24),
):
    """Get evaluation count by month for bar chart"""
    company_id = request.state.user.company_id if request.state.user.role != 0 else None
    data = await get_evaluation_by_month_data(session, company_id, months)
    return data


@router.get("/widgets/kpi-averages")
async def get_kpi_averages_widget(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """Get average IOC, IRD, CES scores"""
    company_id = request.state.user.company_id if request.state.user.role != 0 else None
    data = await get_ioc_ird_ces_averages(session, company_id)
    return data


# Export Endpoints

@router.get("/export/excel")
async def export_dashboard_excel(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """Export dashboard data to Excel format"""
    
    # Get dashboard data based on role
    dashboard_data = await get_dashboard(request, session)
    
    # Prepare data for export
    export_data = prepare_export_data(dashboard_data, request.state.user.role)
    
    # Get company name
    company_name = "Siete CX"
    if request.state.user.company_id and hasattr(request.state.user, 'company'):
        company_name = request.state.user.company.name
    
    # Generate Excel file
    excel_buffer = export_dashboard_to_excel(
        export_data,
        company_name=company_name,
        report_title=f"Dashboard Report - {datetime.now().strftime('%Y-%m-%d')}"
    )
    
    # Return as downloadable file
    filename = f"dashboard_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    return StreamingResponse(
        excel_buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/pdf")
async def export_dashboard_pdf(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """Export dashboard data to PDF format"""
    
    # Get dashboard data based on role
    dashboard_data = await get_dashboard(request, session)
    
    # Prepare data for export
    export_data = prepare_export_data(dashboard_data, request.state.user.role)
    
    # Get company name
    company_name = "Siete CX"
    if request.state.user.company_id and hasattr(request.state.user, 'company'):
        company_name = request.state.user.company.name
    
    # Generate PDF (returns HTML for now, can be converted to PDF with external tool)
    pdf_buffer = generate_pdf_report(
        export_data,
        company_name=company_name,
        report_title=f"Dashboard Report - {datetime.now().strftime('%Y-%m-%d')}"
    )
    
    # Return as downloadable file
    filename = f"dashboard_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="text/html",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
