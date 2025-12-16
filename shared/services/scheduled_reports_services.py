"""
Scheduled Reports Service
Generates and sends periodic digest emails to company admins
Can be triggered by Railway Cron Jobs or external scheduler
"""
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func

from shared.models.company_model import Company
from shared.models.user_model import User
from shared.models.intelligence_model import Insight
from shared.models.evaluation_model import Evaluation
from shared.services.notification_integration_services import email_service


class ScheduledReportsService:
    """Service for generating and sending scheduled reports"""
    
    async def generate_weekly_digest(
        self,
        session: AsyncSession,
        company_id: int
    ) -> dict:
        """
        Generate weekly digest data for a company
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # Get company info
        company_query = select(Company).where(Company.id == company_id)
        company_result = await session.execute(company_query)
        company = company_result.scalars().first()
        
        if not company:
            return {}
        
        # Count evaluations this week
        eval_query = select(func.count(Evaluation.id)).where(
            Evaluation.campaigns_id.in_(
                select(Evaluation.campaigns_id).where(
                    Evaluation.created_at >= start_date,
                    Evaluation.created_at <= end_date
                )
            )
        )
        # Simplified: just count recent evaluations
        eval_count_query = select(func.count(Evaluation.id)).where(
            Evaluation.created_at >= start_date,
            Evaluation.deleted_at == None
        )
        eval_result = await session.execute(eval_count_query)
        total_evaluations = eval_result.scalar() or 0
        
        # Count insights by severity
        insight_query = select(
            Insight.severity,
            func.count(Insight.id).label("count")
        ).where(
            Insight.company_id == company_id,
            Insight.created_at >= start_date,
            Insight.deleted_at == None
        ).group_by(Insight.severity)
        
        insight_result = await session.execute(insight_query)
        insight_data = insight_result.all()
        
        insights_by_severity = {
            "critical": 0, "high": 0, "medium": 0, "low": 0
        }
        total_insights = 0
        for row in insight_data:
            insights_by_severity[row.severity] = row.count
            total_insights += row.count
        
        # Count unread insights
        unread_query = select(func.count(Insight.id)).where(
            Insight.company_id == company_id,
            Insight.is_read == False,
            Insight.deleted_at == None
        )
        unread_result = await session.execute(unread_query)
        unread_insights = unread_result.scalar() or 0
        
        # Get top 5 recent critical/high insights
        top_insights_query = select(Insight).where(
            Insight.company_id == company_id,
            Insight.severity.in_(["critical", "high"]),
            Insight.created_at >= start_date,
            Insight.deleted_at == None
        ).order_by(Insight.created_at.desc()).limit(5)
        
        top_insights_result = await session.execute(top_insights_query)
        top_insights = top_insights_result.scalars().all()
        
        return {
            "company_name": company.name,
            "period_start": start_date.strftime("%Y-%m-%d"),
            "period_end": end_date.strftime("%Y-%m-%d"),
            "total_evaluations": total_evaluations,
            "total_insights": total_insights,
            "unread_insights": unread_insights,
            "insights_by_severity": insights_by_severity,
            "top_insights": [
                {
                    "title": i.title,
                    "severity": i.severity,
                    "description": i.description[:100] + "..." if len(i.description) > 100 else i.description
                }
                for i in top_insights
            ]
        }
    
    async def send_weekly_digest_email(
        self,
        session: AsyncSession,
        company_id: int
    ) -> int:
        """
        Send weekly digest email to all admins/managers of a company
        Returns number of emails sent
        """
        digest = await self.generate_weekly_digest(session, company_id)
        
        if not digest:
            return 0
        
        # Get admin/manager users
        users_query = select(User).where(
            User.company_id == company_id,
            User.role.in_([1, 2]),
            User.deleted_at == None
        )
        users_result = await session.execute(users_query)
        users = users_result.scalars().all()
        
        sent_count = 0
        for user in users:
            try:
                html_content = self._build_digest_html(digest, user.first_name)
                
                await email_service.send_email(
                    to_email=user.email,
                    subject=f"📊 Resumen Semanal - {digest['company_name']} | Siete CX",
                    html_content=html_content
                )
                sent_count += 1
                print(f"✅ Digest enviado a {user.email}")
            except Exception as e:
                print(f"❌ Error enviando digest a {user.email}: {e}")
        
        return sent_count
    
    async def send_all_companies_digest(
        self,
        session: AsyncSession
    ) -> dict:
        """
        Send weekly digest to ALL companies (for cron job)
        Returns summary of sent emails
        """
        companies_query = select(Company).where(Company.deleted_at == None)
        companies_result = await session.execute(companies_query)
        companies = companies_result.scalars().all()
        
        results = {
            "companies_processed": 0,
            "emails_sent": 0,
            "errors": []
        }
        
        for company in companies:
            try:
                sent = await self.send_weekly_digest_email(session, company.id)
                results["companies_processed"] += 1
                results["emails_sent"] += sent
            except Exception as e:
                results["errors"].append(f"{company.name}: {str(e)}")
        
        return results
    
    def _build_digest_html(self, digest: dict, user_name: str) -> str:
        """Build HTML email content for digest"""
        
        severity_colors = {
            "critical": "#dc2626",
            "high": "#f97316", 
            "medium": "#eab308",
            "low": "#3b82f6"
        }
        
        insights_html = ""
        for insight in digest.get("top_insights", []):
            color = severity_colors.get(insight["severity"], "#6b7280")
            insights_html += f"""
            <div style="border-left: 4px solid {color}; padding: 12px; margin: 8px 0; background: #f9fafb;">
                <div style="font-weight: bold; color: {color}; text-transform: uppercase; font-size: 12px;">
                    {insight['severity']}
                </div>
                <div style="font-weight: 600; margin: 4px 0;">{insight['title']}</div>
                <div style="color: #6b7280; font-size: 14px;">{insight['description']}</div>
            </div>
            """
        
        if not insights_html:
            insights_html = "<p style='color: #6b7280;'>No hay insights críticos esta semana. ¡Excelente trabajo!</p>"
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f3f4f6; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%); padding: 32px; text-align: center;">
                    <h1 style="color: white; margin: 0; font-size: 24px;">📊 Resumen Semanal</h1>
                    <p style="color: rgba(255,255,255,0.9); margin: 8px 0 0 0;">{digest['company_name']}</p>
                    <p style="color: rgba(255,255,255,0.7); margin: 4px 0 0 0; font-size: 14px;">
                        {digest['period_start']} - {digest['period_end']}
                    </p>
                </div>
                
                <!-- Content -->
                <div style="padding: 32px;">
                    <p style="color: #374151; font-size: 16px;">Hola <strong>{user_name}</strong>,</p>
                    <p style="color: #6b7280;">Aquí está el resumen de actividad de tu equipo esta semana:</p>
                    
                    <!-- Stats Grid -->
                    <div style="display: flex; flex-wrap: wrap; gap: 16px; margin: 24px 0;">
                        <div style="flex: 1; min-width: 120px; background: #f0f9ff; padding: 16px; border-radius: 8px; text-align: center;">
                            <div style="font-size: 28px; font-weight: bold; color: #3b82f6;">{digest['total_evaluations']}</div>
                            <div style="color: #6b7280; font-size: 14px;">Evaluaciones</div>
                        </div>
                        <div style="flex: 1; min-width: 120px; background: #fef3c7; padding: 16px; border-radius: 8px; text-align: center;">
                            <div style="font-size: 28px; font-weight: bold; color: #f59e0b;">{digest['total_insights']}</div>
                            <div style="color: #6b7280; font-size: 14px;">Insights</div>
                        </div>
                        <div style="flex: 1; min-width: 120px; background: #fee2e2; padding: 16px; border-radius: 8px; text-align: center;">
                            <div style="font-size: 28px; font-weight: bold; color: #ef4444;">{digest['unread_insights']}</div>
                            <div style="color: #6b7280; font-size: 14px;">Sin Leer</div>
                        </div>
                    </div>
                    
                    <!-- Insights by Severity -->
                    <h3 style="color: #374151; margin: 24px 0 16px 0;">Insights por Severidad</h3>
                    <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                        <span style="background: #fee2e2; color: #dc2626; padding: 4px 12px; border-radius: 16px; font-size: 14px;">
                            🔴 Críticos: {digest['insights_by_severity']['critical']}
                        </span>
                        <span style="background: #ffedd5; color: #f97316; padding: 4px 12px; border-radius: 16px; font-size: 14px;">
                            🟠 Altos: {digest['insights_by_severity']['high']}
                        </span>
                        <span style="background: #fef9c3; color: #eab308; padding: 4px 12px; border-radius: 16px; font-size: 14px;">
                            🟡 Medios: {digest['insights_by_severity']['medium']}
                        </span>
                        <span style="background: #dbeafe; color: #3b82f6; padding: 4px 12px; border-radius: 16px; font-size: 14px;">
                            🔵 Bajos: {digest['insights_by_severity']['low']}
                        </span>
                    </div>
                    
                    <!-- Top Insights -->
                    <h3 style="color: #374151; margin: 24px 0 16px 0;">Insights Prioritarios</h3>
                    {insights_html}
                    
                    <!-- CTA -->
                    <div style="text-align: center; margin: 32px 0;">
                        <a href="https://app.sieteic.com/intelligence" 
                           style="background: #3b82f6; color: white; padding: 12px 32px; border-radius: 8px; text-decoration: none; font-weight: 600; display: inline-block;">
                            Ver Dashboard Completo →
                        </a>
                    </div>
                </div>
                
                <!-- Footer -->
                <div style="background: #f9fafb; padding: 24px; text-align: center; border-top: 1px solid #e5e7eb;">
                    <p style="color: #9ca3af; font-size: 12px; margin: 0;">
                        Este es un correo automático de Siete CX.<br>
                        © {datetime.now().year} Siete IC. Todos los derechos reservados.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """


# Singleton
scheduled_reports_service = ScheduledReportsService()
