"""
Analysis Notification Orchestrator
Connects evaluation analysis completion with notification systems
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from shared.models.evaluation_model import Evaluation
from shared.models.evaluation_analysis_model import EvaluationAnalysis
from shared.models.campaign_model import Campaign
from shared.models.user_model import User
from shared.models.company_model import Company
from shared.services.notification_integration_services import notification_orchestrator
from shared.services.webhook_services import integration_orchestrator, slack_service
from shared.services.intelligence_services import generate_insights_from_analysis, auto_tag_evaluation


class AnalysisNotificationOrchestrator:
    """
    Orchestrates all post-analysis actions:
    1. Generate insights from analysis
    2. Auto-tag evaluation
    3. Send email/SMS notifications
    4. Send Slack/webhook notifications
    """
    
    async def on_analysis_complete(
        self,
        session: AsyncSession,
        evaluation_id: int,
        analysis: EvaluationAnalysis
    ):
        """
        Called when an evaluation analysis is completed.
        Triggers all notification and insight generation flows.
        """
        
        # Get evaluation with related data
        eval_query = select(Evaluation).where(Evaluation.id == evaluation_id)
        eval_result = await session.execute(eval_query)
        evaluation = eval_result.scalars().first()
        
        if not evaluation:
            print(f"❌ Evaluation {evaluation_id} not found")
            return
        
        # Get campaign
        campaign_query = select(Campaign).where(Campaign.id == evaluation.campaigns_id)
        campaign_result = await session.execute(campaign_query)
        campaign = campaign_result.scalars().first()
        
        if not campaign:
            print(f"❌ Campaign for evaluation {evaluation_id} not found")
            return
        
        company_id = campaign.company_id
        
        # Get evaluator (user who created the evaluation)
        user_query = select(User).where(User.id == evaluation.user_id)
        user_result = await session.execute(user_query)
        evaluator = user_result.scalars().first()
        
        # Get company for webhook settings
        company_query = select(Company).where(Company.id == company_id)
        company_result = await session.execute(company_query)
        company = company_result.scalars().first()
        
        # 1. Generate insights from analysis
        print(f"📊 Generating insights for evaluation {evaluation_id}...")
        insights = await generate_insights_from_analysis(
            session=session,
            evaluation_id=evaluation_id,
            analysis=analysis,
            company_id=company_id
        )
        print(f"   ✅ Generated {len(insights)} insights")
        
        # 2. Auto-tag evaluation
        print(f"🏷️ Auto-tagging evaluation {evaluation_id}...")
        tags = await auto_tag_evaluation(
            session=session,
            evaluation_id=evaluation_id,
            analysis=analysis
        )
        print(f"   ✅ Applied {len(tags)} tags")
        
        # 3. Send notifications to evaluator
        if evaluator:
            print(f"📧 Sending notifications to {evaluator.email}...")
            await notification_orchestrator.notify_evaluation_complete(
                session=session,
                user_id=evaluator.id,
                user_email=evaluator.email,
                user_name=f"{evaluator.first_name} {evaluator.last_name}",
                user_phone=None,  # Add phone field to User model if needed
                evaluation_id=evaluation_id,
                campaign_name=campaign.name,
                preferences={"email": True, "sms": False, "in_app": True}
            )
            print("   ✅ Notifications sent")
        
        # 4. Check for critical insights and notify admins
        critical_insights = [i for i in insights if hasattr(i, 'severity') and i.severity in ['critical', 'high']]
        
        if critical_insights and company:
            print(f"🚨 Found {len(critical_insights)} critical insights, notifying admins...")
            
            # Get company admins
            admins_query = select(User).where(
                User.company_id == company_id,
                User.role.in_([1, 2]),  # Admin and Manager
                User.deleted_at.is_(None)
            )
            admins_result = await session.execute(admins_query)
            admins = admins_result.scalars().all()
            
            for insight in critical_insights:
                # Notify each admin
                for admin in admins:
                    await notification_orchestrator.notify_critical_insight(
                        session=session,
                        user_id=admin.id,
                        user_email=admin.email,
                        user_name=f"{admin.first_name} {admin.last_name}",
                        user_phone=None,
                        insight_title=insight.title if hasattr(insight, 'title') else "Insight Crítico",
                        insight_description=insight.description if hasattr(insight, 'description') else "",
                        preferences={"email": True, "sms": False, "in_app": True}
                    )
                
                # Send to Slack if configured
                if company.slack_webhook_url:
                    await slack_service.send_critical_alert(
                        title=insight.title if hasattr(insight, 'title') else "Insight Crítico",
                        description=insight.description if hasattr(insight, 'description') else "",
                        severity=insight.severity if hasattr(insight, 'severity') else "high",
                        evaluation_id=evaluation_id,
                        webhook_url=company.slack_webhook_url
                    )
            
            print(f"   ✅ Admin notifications sent")
        
        # 5. Send webhook if configured
        if company and company.webhook_url:
            print(f"🔗 Sending webhook to {company.webhook_url}...")
            from shared.services.webhook_services import webhook_service
            
            success, status_code, error = await webhook_service.send_evaluation_complete_webhook(
                url=company.webhook_url,
                evaluation_id=evaluation_id,
                campaign_id=campaign.id,
                evaluator_id=evaluation.user_id,
                score=0.0,  # Add score from analysis if available
                company_id=company_id,
                secret=company.webhook_secret
            )
            
            if success:
                print("   ✅ Webhook sent successfully")
            else:
                print(f"   ❌ Webhook failed: {error}")
        
        print(f"✨ Analysis notification orchestration complete for evaluation {evaluation_id}")
        
        return {
            "insights_generated": len(insights),
            "tags_applied": len(tags),
            "notifications_sent": True
        }


# Singleton instance
analysis_notification_orchestrator = AnalysisNotificationOrchestrator()
