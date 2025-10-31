"""
Database Seeder Script
Populates database with initial data for development and testing
"""

import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db_session
from app.models.company_model import CompanyCreate
from app.models.user_model import UserCreate
from app.models.zone_model import ZoneCreate
from app.models.campaign_model import CampaignCreate
from app.models.prompt_manager_model import PromptManagerCreate
from app.models.theme_model import CompanyThemeCreate, DEFAULT_THEME
from app.models.intelligence_model import Tag

from app.services.company_services import create_company
from app.services.users_services import create_user
from app.services.zone_services import create_zone
from app.services.campaign_services import create_campaign
from app.services.prompt_manager_services import create_prompt
from app.services.theme_services import create_company_theme


async def seed_companies(session: AsyncSession):
    """Seed initial companies"""
    print("🏢 Seeding companies...")
    
    companies = [
        {
            "name": "Banco Nacional",
            "email": "contacto@banconacional.com",
            "phone": "+1809-555-0100",
            "address": "Av. 27 de Febrero, Santo Domingo",
            "state": "Distrito Nacional",
            "country": "DO"
        },
        {
            "name": "Retail SuperStore",
            "email": "info@retailsuper.com",
            "phone": "+1809-555-0200",
            "address": "Plaza Central, Santiago",
            "state": "Santiago",
            "country": "DO"
        },
        {
            "name": "Hotel Paradise",
            "email": "reservas@hotelparadise.com",
            "phone": "+1809-555-0300",
            "address": "Zona Colonial, Santo Domingo",
            "state": "Distrito Nacional",
            "country": "DO"
        }
    ]
    
    created_companies = []
    for company_data in companies:
        company = await create_company(session, CompanyCreate(**company_data))
        created_companies.append(company)
        print(f"  ✓ Created: {company.name}")
    
    return created_companies


async def seed_users(session: AsyncSession, companies: list):
    """Seed initial users"""
    print("\n👥 Seeding users...")
    
    users = [
        # Superadmin
        {
            "email": "superadmin@sieteic.com",
            "password": "Admin2025!",
            "first_name": "Super",
            "last_name": "Admin",
            "role": 0,
            "company_id": companies[0].id,
            "gender": "male"
        },
        # Banco Nacional - Admin
        {
            "email": "admin@banconacional.com",
            "password": "BancoAdmin2025!",
            "first_name": "Carlos",
            "last_name": "Rodríguez",
            "role": 1,
            "company_id": companies[0].id,
            "gender": "male"
        },
        # Banco Nacional - Manager
        {
            "email": "manager@banconacional.com",
            "password": "BancoManager2025!",
            "first_name": "María",
            "last_name": "Pérez",
            "role": 2,
            "company_id": companies[0].id,
            "gender": "female"
        },
        # Banco Nacional - Shoppers
        {
            "email": "shopper1@banconacional.com",
            "password": "Shopper2025!",
            "first_name": "Juan",
            "last_name": "Martínez",
            "role": 3,
            "company_id": companies[0].id,
            "gender": "male"
        },
        {
            "email": "shopper2@banconacional.com",
            "password": "Shopper2025!",
            "first_name": "Ana",
            "last_name": "González",
            "role": 3,
            "company_id": companies[0].id,
            "gender": "female"
        },
        # Retail - Admin
        {
            "email": "admin@retailsuper.com",
            "password": "RetailAdmin2025!",
            "first_name": "Pedro",
            "last_name": "Santos",
            "role": 1,
            "company_id": companies[1].id,
            "gender": "male"
        },
        # Hotel - Admin
        {
            "email": "admin@hotelparadise.com",
            "password": "HotelAdmin2025!",
            "first_name": "Laura",
            "last_name": "Díaz",
            "role": 1,
            "company_id": companies[2].id,
            "gender": "female"
        }
    ]
    
    created_users = []
    for user_data in users:
        user = await create_user(session, UserCreate(**user_data))
        created_users.append(user)
        print(f"  ✓ Created: {user.email} (Role {user.role})")
    
    return created_users


async def seed_zones(session: AsyncSession):
    """Seed geographical zones"""
    print("\n🗺️ Seeding zones...")
    
    zones = [
        {"name": "Zona Metro Santo Domingo", "country": "DO", "state": "Distrito Nacional", "city": "Santo Domingo"},
        {"name": "Zona Norte Santiago", "country": "DO", "state": "Santiago", "city": "Santiago"},
        {"name": "Zona Este La Romana", "country": "DO", "state": "La Romana", "city": "La Romana"},
        {"name": "Zona Sur San Cristóbal", "country": "DO", "state": "San Cristóbal", "city": "San Cristóbal"},
    ]
    
    created_zones = []
    for zone_data in zones:
        zone = await create_zone(session, ZoneCreate(**zone_data))
        created_zones.append(zone)
        print(f"  ✓ Created: {zone.name}")
    
    return created_zones


async def seed_campaigns(session: AsyncSession, companies: list):
    """Seed sample campaigns"""
    print("\n📋 Seeding campaigns...")
    
    now = datetime.now()
    
    campaigns = [
        {
            "name": "Q1 2025 - Evaluación Sucursales",
            "description": "Evaluación trimestral de calidad de atención en sucursales bancarias",
            "start_date": now,
            "end_date": now + timedelta(days=90),
            "company_id": companies[0].id
        },
        {
            "name": "Mystery Shopping Retail Enero",
            "description": "Evaluación de experiencia de compra en tiendas retail",
            "start_date": now,
            "end_date": now + timedelta(days=30),
            "company_id": companies[1].id
        },
        {
            "name": "Auditoría Hospitalidad 2025",
            "description": "Evaluación de servicio al huésped en hoteles",
            "start_date": now,
            "end_date": now + timedelta(days=180),
            "company_id": companies[2].id
        }
    ]
    
    created_campaigns = []
    for campaign_data in campaigns:
        campaign = await create_campaign(session, CampaignCreate(**campaign_data))
        created_campaigns.append(campaign)
        print(f"  ✓ Created: {campaign.name}")
    
    return created_campaigns


async def seed_prompts(session: AsyncSession, companies: list):
    """Seed custom AI prompts"""
    print("\n🤖 Seeding AI prompts...")
    
    banking_prompt = """
Eres un analista especializado en experiencia bancaria y servicios financieros.
Debes evaluar interacciones siguiendo estándares de la industria bancaria dominicana.

Aspectos clave a evaluar:
- Cumplimiento normativo (identificación, KYC)
- Seguridad en manejo de información
- Conocimiento de productos bancarios
- Cross-selling ético
- Tiempo de espera y eficiencia
- Cortesía y profesionalismo

Enfócate en:
1. Vista Ejecutiva: Narrativa para directores de sucursal
2. Vista Operativa: KPIs específicos de banca (IOC, IRD, CES, Compliance Score)
"""
    
    retail_prompt = """
Eres un analista especializado en retail y experiencia de compra.
Evalúa interacciones en tiendas físicas siguiendo mejores prácticas del sector.

Aspectos clave:
- Saludo y bienvenida
- Conocimiento de producto
- Técnicas de venta
- Manejo de objeciones
- Merchandising y presentación
- Proceso de pago

Enfócate en:
1. Vista Ejecutiva: Insights para gerentes de tienda
2. Vista Operativa: KPIs de retail (Sales Effectiveness, Product Knowledge, Store Presentation)
"""
    
    prompts = [
        {
            "company_id": companies[0].id,
            "prompt_name": "Análisis Bancario Especializado",
            "prompt_type": "dual_analysis",
            "system_prompt": banking_prompt,
            "is_active": True,
            "metadata": {"industry": "banking", "language": "es"}
        },
        {
            "company_id": companies[1].id,
            "prompt_name": "Análisis Retail Especializado",
            "prompt_type": "dual_analysis",
            "system_prompt": retail_prompt,
            "is_active": True,
            "metadata": {"industry": "retail", "language": "es"}
        }
    ]
    
    for prompt_data in prompts:
        prompt = await create_prompt(session, PromptManagerCreate(**prompt_data))
        print(f"  ✓ Created: {prompt.prompt_name}")


async def seed_themes(session: AsyncSession, companies: list):
    """Seed company themes"""
    print("\n🎨 Seeding company themes...")
    
    themes = [
        {
            "company_id": companies[0].id,
            "company_name_override": "Portal CX Bancario",
            "primary_color": "#003d7a",
            "secondary_color": "#0066cc",
            "accent_color": "#00a86b",
            **DEFAULT_THEME
        },
        {
            "company_id": companies[1].id,
            "company_name_override": "Retail Quality Portal",
            "primary_color": "#d32f2f",
            "secondary_color": "#f44336",
            "accent_color": "#ff6b6b",
            **DEFAULT_THEME
        },
        {
            "company_id": companies[2].id,
            "company_name_override": "Hospitality CX Platform",
            "primary_color": "#1976d2",
            "secondary_color": "#2196f3",
            "accent_color": "#64b5f6",
            **DEFAULT_THEME
        }
    ]
    
    for theme_data in themes:
        theme = await create_company_theme(session, CompanyThemeCreate(**theme_data))
        print(f"  ✓ Created theme for company {theme.company_id}")


async def seed_tags(session: AsyncSession):
    """Seed standard tags"""
    print("\n🏷️ Seeding tags...")
    
    tags = [
        {"name": "churn-risk", "category": "issue", "color": "#ef4444"},
        {"name": "satisfied-customer", "category": "quality", "color": "#10b981"},
        {"name": "complex-process", "category": "performance", "color": "#f59e0b"},
        {"name": "simple-process", "category": "quality", "color": "#10b981"},
        {"name": "sales-success", "category": "opportunity", "color": "#8b5cf6"},
        {"name": "missed-opportunity", "category": "issue", "color": "#f59e0b"},
        {"name": "excellent-quality", "category": "quality", "color": "#10b981"},
        {"name": "needs-improvement", "category": "issue", "color": "#f59e0b"},
        {"name": "positive-feedback", "category": "quality", "color": "#10b981"},
        {"name": "negative-feedback", "category": "issue", "color": "#f59e0b"},
        {"name": "critical-issue", "category": "compliance", "color": "#ef4444"},
    ]
    
    for tag_data in tags:
        tag = Tag(**tag_data)
        session.add(tag)
    
    await session.commit()
    print(f"  ✓ Created {len(tags)} standard tags")


async def main():
    """Run all seeders"""
    print("\n" + "="*50)
    print("🌱 SIETE CX DATABASE SEEDER")
    print("="*50 + "\n")
    
    async with get_db_session() as session:
        try:
            # Seed in order
            companies = await seed_companies(session)
            users = await seed_users(session, companies)
            zones = await seed_zones(session)
            campaigns = await seed_campaigns(session, companies)
            await seed_prompts(session, companies)
            await seed_themes(session, companies)
            await seed_tags(session)
            
            print("\n" + "="*50)
            print("✅ SEEDING COMPLETE!")
            print("="*50)
            print("\n📊 Summary:")
            print(f"  • {len(companies)} companies")
            print(f"  • {len(users)} users")
            print(f"  • {len(zones)} zones")
            print(f"  • {len(campaigns)} campaigns")
            print(f"  • AI prompts configured")
            print(f"  • Themes configured")
            print(f"  • Standard tags created")
            
            print("\n🔐 Test Credentials:")
            print("  Superadmin: superadmin@sieteic.com / Admin2025!")
            print("  Admin (Banco): admin@banconacional.com / BancoAdmin2025!")
            print("  Shopper: shopper1@banconacional.com / Shopper2025!")
            
        except Exception as e:
            print(f"\n❌ Error during seeding: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
