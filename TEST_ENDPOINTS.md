# Test de Endpoints Principales - Siete CX

Reemplaza `YOUR_RAILWAY_URL` con tu URL de Railway.

## 1. Health Check ✅
```bash
curl https://YOUR_RAILWAY_URL/api/v1/health
```

**Esperado:** `{"status":"healthy","version":"1.0.0"}`

---

## 2. Crear una Compañía
```bash
curl -X POST https://YOUR_RAILWAY_URL/api/v1/companies \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Empresa Demo",
    "subdomain": "demo",
    "contact_email": "contacto@demo.com"
  }'
```

**Esperado:** Respuesta con ID de compañía creada

---

## 3. Crear un Usuario
```bash
curl -X POST https://YOUR_RAILWAY_URL/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@demo.com",
    "password": "Admin123!",
    "full_name": "Admin Demo",
    "company_id": 1,
    "role": "admin"
  }'
```

**Esperado:** Usuario creado exitosamente

---

## 4. Login
```bash
curl -X POST https://YOUR_RAILWAY_URL/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@demo.com",
    "password": "Admin123!"
  }'
```

**Esperado:** Token JWT
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

---

## 5. Listar Widgets (requiere autenticación)
```bash
# Primero guarda tu token
TOKEN="tu-token-aqui"

curl https://YOUR_RAILWAY_URL/api/v1/dashboards/widgets \
  -H "Authorization: Bearer $TOKEN"
```

**Esperado:** Lista de widgets disponibles

---

## 6. Obtener Dashboard Config del Usuario
```bash
curl https://YOUR_RAILWAY_URL/api/v1/dashboards/configs \
  -H "Authorization: Bearer $TOKEN"
```

**Esperado:** Configuración de dashboard del usuario

---

## 7. Listar Insights
```bash
curl https://YOUR_RAILWAY_URL/api/v1/intelligence/insights \
  -H "Authorization: Bearer $TOKEN"
```

**Esperado:** Lista de insights (vacía si no hay datos aún)

---

## 8. Ver Tema de Compañía
```bash
curl https://YOUR_RAILWAY_URL/api/v1/themes \
  -H "Authorization: Bearer $TOKEN"
```

**Esperado:** Configuración de tema (colores, logos, etc.)

---

## Próximos Tests

Una vez que estos endpoints funcionen, puedes:
- Crear campañas
- Crear evaluaciones
- Subir audio para análisis AI
- Generar insights automáticos
- Configurar dashboards personalizados

---

## Si algo falla:

1. **500 Error:** Revisa logs de Railway
2. **404 Error:** Verifica que la ruta tenga `/api/v1/`
3. **401 Error:** Token expirado o inválido
4. **Database Error:** Migraciones no ejecutadas
