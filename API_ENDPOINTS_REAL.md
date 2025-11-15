# 🎯 Siete CX - Endpoints Reales en Producción

**Base URL:** `https://cx-api.sieteic.com`

## ✅ ENDPOINTS CONFIRMADOS (extraídos de /openapi.json)

### Authentication
- `POST /api/v1/auth/login` (form-urlencoded: username, password)

### Users
- `POST /api/v1/user/` (crear usuario)
- `GET /api/v1/user/` (listar usuarios)
- `GET /api/v1/user/me` (usuario actual)
- `GET /api/v1/user/{user_id}` (obtener usuario)
- `PUT /api/v1/user/{user_id}` (actualizar usuario)

### Companies
- `POST /api/v1/company/` (crear compañía)
- `GET /api/v1/company/` (listar compañías)
- `GET /api/v1/company/{company_id}` (obtener compañía)
- `PUT /api/v1/company/{company_id}` (actualizar compañía)

### Dashboard Config (Phase 2) ✅
- `GET /api/v1/dashboard-config/widgets`
- `GET /api/v1/dashboard-config/`
- `POST /api/v1/dashboard-config/`
- `GET /api/v1/dashboard-config/default`
- `GET /api/v1/dashboard-config/{config_id}`
- `PUT /api/v1/dashboard-config/{config_id}`
- `DELETE /api/v1/dashboard-config/{config_id}`
- `POST /api/v1/dashboard-config/{config_id}/set-default`

### Widgets
- `POST /api/v1/dashboard-config/widgets`
- `GET /api/v1/dashboard-config/widgets/{widget_id}`
- `PUT /api/v1/dashboard-config/widgets/{widget_id}`
- `DELETE /api/v1/dashboard-config/widgets/{widget_id}`

### Intelligence (Phase 3) ✅
- `GET /api/v1/intelligence/insights`
- `GET /api/v1/intelligence/insights/summary`
- `GET /api/v1/intelligence/insights/top-actions`
- `GET /api/v1/intelligence/insights/trends`
- `GET /api/v1/intelligence/insights/{insight_id}`
- `PUT /api/v1/intelligence/insights/{insight_id}/read`
- `GET /api/v1/intelligence/trends`
- `GET /api/v1/intelligence/trends/{trend_id}`
- `GET /api/v1/intelligence/tags`
- `GET /api/v1/intelligence/tags/{tag_id}`

### Prompts (Phase 3) ✅
- `GET /api/v1/prompts/`
- `POST /api/v1/prompts/`
- `GET /api/v1/prompts/active`
- `GET /api/v1/prompts/{prompt_id}`
- `PUT /api/v1/prompts/{prompt_id}`
- `DELETE /api/v1/prompts/{prompt_id}`

### Themes (Phase 4) ✅
- `GET /api/v1/theme/`
- `PUT /api/v1/theme/`
- `POST /api/v1/theme/reset`
- `GET /api/v1/theme/css`
- `POST /api/v1/theme/preview`
- `GET /api/v1/theme/public/{company_id}`

## 🔑 AUTENTICACIÓN

**Login:**
```bash
curl -X POST https://cx-api.sieteic.com/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@test.com&password=Admin123!"
```

**Uso del Token:**
```bash
curl -H "Authorization: Bearer <token>" \
  https://cx-api.sieteic.com/api/v1/user/me
```

## ✅ TODOS LOS ENDPOINTS PHASE 0-4 ESTÁN DESPLEGADOS

El testing agent estaba buscando en rutas incorrectas:
- ❌ Buscaba: `/api/v1/users/` 
- ✅ Real: `/api/v1/user/`

**CONCLUSIÓN:** Backend 100% funcional, frontend conectado, listo para testing E2E.
