#!/bin/bash

# 🚀 SCRIPT PARA GUARDAR TODOS LOS CAMBIOS DE PHASE 0-4 EN GITHUB
# Ejecutar desde: /app/cx-backend

set -e  # Detener si hay error

echo "================================================"
echo "📦 GUARDANDO CAMBIOS DE PHASE 0-4 EN GITHUB"
echo "================================================"
echo ""

# 1. Verificar que estamos en cx-backend
if [ ! -d "app/models" ]; then
    echo "❌ ERROR: Debes ejecutar este script desde /app/cx-backend"
    exit 1
fi

# 2. Verificar estado actual
echo "📊 Estado actual del repositorio:"
git status --short
echo ""

# 3. Cambiar al branch correcto
echo "🌿 Cambiando a branch phase0-4-enhancements1..."
git checkout phase0-4-enhancements1 || git checkout -b phase0-4-enhancements1
echo ""

# 4. Agregar TODOS los archivos nuevos y modificados
echo "➕ Agregando todos los archivos..."

# Archivos modificados
git add app/models/company_model.py
git add app/models/user_model.py
git add app/routes/dashboard_router.py
git add app/routes/main.py
git add app/services/extract_audio_services.py
git add app/services/openai_services.py

# Archivos NUEVOS - Models
git add app/models/dashboard_config_model.py
git add app/models/intelligence_model.py
git add app/models/prompt_manager_model.py
git add app/models/theme_model.py

# Archivos NUEVOS - Services
git add app/services/dashboard_config_services.py
git add app/services/dashboard_widgets_services.py
git add app/services/export_services.py
git add app/services/intelligence_services.py
git add app/services/notification_integration_services.py
git add app/services/prompt_manager_services.py
git add app/services/theme_services.py

# Archivos NUEVOS - Routes
git add app/routes/dashboard_config_router.py
git add app/routes/intelligence_router.py
git add app/routes/prompt_manager_router.py
git add app/routes/theme_router.py

# Archivos NUEVOS - Migrations
git add app/migrations/versions/20251030224948_add_prompt_manager_table.py

# Archivos NUEVOS - Seeder
git add app/seeder/seed_database.py

# Archivos NUEVOS - Tests
git add tests/

# Archivos NUEVOS - Docs
git add docs/

# Archivos NUEVOS - GitHub Actions
git add .github/

# Requirements (puede tener cambios)
git add requirements.txt

echo "✅ Archivos agregados"
echo ""

# 5. Ver qué se va a commitear
echo "📝 Archivos que se van a guardar:"
git status --short
echo ""

# 6. Hacer commit
echo "💾 Creando commit..."
git commit -m "feat: Phase 0-4 - Prompts, Dashboards, Intelligence, Notifications, Themes

- Add Prompt Manager system (company-specific AI prompts)
- Add Dashboard configuration with widgets and KPIs
- Add Intelligence Engine (auto-tagging, scoring, NPS inference)
- Add Omnichannel notifications (SendGrid, Twilio, in-app)
- Add White-label theming system
- Add Excel/PDF export functionality
- Add comprehensive documentation
- Add GitHub Actions workflow
- Add initial test infrastructure
- Add database seeder

Backend implementation complete - Ready for frontend integration"

echo "✅ Commit creado"
echo ""

# 7. Push a GitHub
echo "🚀 Subiendo a GitHub..."
git push origin phase0-4-enhancements1

echo ""
echo "================================================"
echo "✅ ¡TODO GUARDADO EN GITHUB!"
echo "================================================"
echo ""
echo "🔗 Ver en: https://github.com/juanfamilia/cx-backend/tree/phase0-4-enhancements1"
echo ""
echo "📋 Próximos pasos:"
echo "1. Verificar en GitHub que todos los archivos están"
echo "2. Crear proyecto Staging en Railway"
echo "3. Seguir la GUIA_RAPIDA_DEPLOYMENT.md"
echo ""
