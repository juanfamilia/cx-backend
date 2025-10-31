# 👤 GUÍA PARA USUARIO - CÓMO PROBAR LAS NUEVAS FUNCIONALIDADES

**Para:** Juan (Emprendedor/Owner Siete CX)  
**Tiempo:** 30-45 minutos  
**Requisito:** Tu dev debe implementar primero (ver GUIA_DESARROLLADOR.md)

---

## 🎯 QUÉ VOY A PODER HACER DESPUÉS DE LA IMPLEMENTACIÓN:

1. ✅ Ver **insights automáticos** que me alertan de problemas
2. ✅ **Personalizar mi dashboard** con widgets
3. ✅ **Exportar reportes** a Excel
4. ✅ Recibir **notificaciones por email** cuando termina un análisis
5. ✅ **Personalizar la marca** (logo, colores) por empresa
6. ✅ Crear **prompts personalizados** para cada industria

---

## 📋 CHECKLIST DE PRUEBAS

### ✅ PRUEBA 1: Insights Automáticos (Lo más importante)

**¿Qué hace?**
Te alerta automáticamente cuando detecta:
- Cliente en riesgo de irse (IRD alto)
- Proceso muy complicado para el cliente (CES alto)
- Oportunidad de venta perdida (IOC bajo)
- Problemas de calidad
- Comentarios críticos

**Cómo probarlo:**

1. **Login** en la plataforma como Admin
2. Ve a la sección **"Intelligence"** o **"Insights"** (nuevo menú)
3. Deberías ver algo como:

```
🚨 INSIGHTS ACTIVOS

[CRÍTICO] Comentarios Críticos Detectados
Evaluación #123 - Hace 5 minutos
"Se detectaron 2 frases críticas..."
→ Ver detalles

[ALTO] Alto Riesgo de Deserción - Score: 85
Evaluación #124 - Hace 10 minutos
"Cliente muestra señales de insatisfacción..."
→ Ver detalles

[MEDIO] Alto Esfuerzo del Cliente - Score: 70
Evaluación #125 - Hace 15 minutos
→ Ver detalles
```

4. **Click en "Ver detalles"** de cualquier insight
5. Deberías ver:
   - Descripción completa
   - Métricas (IOC, IRD, CES)
   - Acciones sugeridas
   - Link a la evaluación

**✅ Funciona si:** Ves insights generados automáticamente después de analizar evaluaciones

---

### ✅ PRUEBA 2: Auto-Etiquetado

**¿Qué hace?**
Cada evaluación se etiqueta automáticamente según lo que detecta.

**Cómo probarlo:**

1. Ve a **"Evaluaciones"**
2. Abre cualquier evaluación **completada**
3. Deberías ver etiquetas como:

```
Evaluación #123
Status: Completed

Etiquetas:
🔴 churn-risk          (cliente en riesgo)
🟠 complex-process     (proceso complicado)
🟢 positive-feedback   (feedback positivo)
```

**✅ Funciona si:** Todas las evaluaciones tienen etiquetas automáticas

---

### ✅ PRUEBA 3: Dashboard Personalizable

**¿Qué hace?**
Cada usuario puede elegir qué widgets ver en su dashboard.

**Cómo probarlo:**

1. Ve a **"Dashboard"**
2. Busca botón **"Configurar Dashboard"** o **"⚙️"**
3. Deberías poder:
   - Añadir widgets (NPS Trend, Status, Top Evaluadores)
   - Mover widgets (drag & drop)
   - Cambiar tamaño
   - Guardar configuración

4. Prueba añadir **"NPS Trend"**:
   - Debería mostrar gráfico de línea con tendencia de NPS últimos 30 días

5. Prueba añadir **"Status Breakdown"**:
   - Debería mostrar gráfico circular (pie chart) con:
     * Completed: X evaluaciones
     * Pending: Y evaluaciones
     * Analyzing: Z evaluaciones

**✅ Funciona si:** Puedes personalizar y guardar tu dashboard

---

### ✅ PRUEBA 4: Exportar a Excel

**¿Qué hace?**
Descargar reportes en Excel con múltiples hojas.

**Cómo probarlo:**

1. En **"Dashboard"**, busca botón **"Exportar"** o **"📥"**
2. Click en **"Exportar a Excel"**
3. Debería descargarse archivo: `dashboard_report_YYYYMMDD_HHMMSS.xlsx`
4. Abre el archivo Excel
5. Deberías ver hojas:
   - **Summary:** Métricas principales
   - **Monthly Evaluations:** Evaluaciones por mes
   - **Top Evaluators:** Ranking de evaluadores
   - **Report Info:** Metadata del reporte

**✅ Funciona si:** Excel se descarga y tiene las hojas con datos

---

### ✅ PRUEBA 5: Notificaciones por Email

**¿Qué hace?**
Te envía email cuando termina el análisis de una evaluación.

**Cómo probarlo:**

1. Pídele a un **Shopper** que suba una evaluación
2. Espera que el análisis termine (~2-5 minutos)
3. El Shopper debería recibir email:

```
De: Siete CX <noreply@sieteic.com>
Asunto: ✅ Análisis Completado

Hola [Nombre],

Tu evaluación #123 para la campaña "Q1 2025"
ha sido analizada por nuestro sistema de IA.

Análisis disponible:
• Vista Ejecutiva con insights
• Vista Operativa con KPIs
• Recomendaciones

[Ver Análisis Completo]
```

**✅ Funciona si:** Llega email (revisa spam si no aparece)

---

### ✅ PRUEBA 6: Marca Personalizada (White-label)

**¿Qué hace?**
Cada empresa puede tener su logo, colores, nombre personalizado.

**Cómo probarlo:**

1. Login como **Admin**
2. Ve a **"Configuración"** → **"Marca"** o **"Theme"**
3. Deberías ver formulario:

```
🎨 PERSONALIZAR MARCA

Logo de la empresa:
[Subir logo]  logo.png

Nombre personalizado:
[Portal CX Bancario]

Color primario:
[🎨] #0066cc

Color secundario:
[🎨] #003d7a

[Vista Previa]  [Guardar]
```

4. Cambia el **color primario** a azul
5. Click **"Vista Previa"**
6. Deberías ver la plataforma con tu color
7. Click **"Guardar"**
8. **Cierra sesión y vuelve a entrar**
9. La plataforma debería tener tu color nuevo

**✅ Funciona si:** Los colores cambian al guardar

---

### ✅ PRUEBA 7: Prompts Personalizados (Avanzado)

**¿Qué hace?**
Crear prompts de IA específicos para cada industria.

**Cómo probarlo:**

1. Login como **Admin**
2. Ve a **"Configuración"** → **"Prompts IA"**
3. Click **"Crear Nuevo Prompt"**
4. Llena formulario:

```
Nombre: Análisis Bancario Especializado
Tipo: Dual Analysis
Activo: ✓

Prompt del sistema:
[Eres un analista especializado en experiencia
bancaria. Evalúa siguiendo normativas del sector...]

[Guardar]
```

5. Haz que un Shopper suba evaluación
6. El análisis debería usar TU prompt personalizado

**✅ Funciona si:** El análisis refleja tu prompt personalizado

---

## 📊 RESUMEN DE VERIFICACIÓN:

| Funcionalidad | Estado | Notas |
|---------------|--------|-------|
| Insights Automáticos | ⬜ | Probado: Sí / No |
| Auto-Etiquetado | ⬜ | Probado: Sí / No |
| Dashboard Personalizable | ⬜ | Probado: Sí / No |
| Exportar Excel | ⬜ | Probado: Sí / No |
| Notificaciones Email | ⬜ | Probado: Sí / No |
| Marca Personalizada | ⬜ | Probado: Sí / No |
| Prompts Personalizados | ⬜ | Probado: Sí / No |

---

## 🐛 SI ALGO NO FUNCIONA:

**Anota:**
1. ¿Qué funcionalidad?
2. ¿Qué hiciste?
3. ¿Qué esperabas?
4. ¿Qué pasó en realidad?
5. Screenshot si es posible

**Y pásalo a tu dev** para que revise.

---

## 🎯 CREDENCIALES DE PRUEBA:

Después de correr el seeder, usa:

```
Superadmin:
Email: superadmin@sieteic.com
Password: Admin2025!

Admin (Banco Nacional):
Email: admin@banconacional.com
Password: BancoAdmin2025!

Shopper:
Email: shopper1@banconacional.com
Password: Shopper2025!
```

---

## 📞 ¿DUDAS?

Si algo no funciona o no entiendes cómo probar algo, anótalo y pregúntame.

**¡Éxito probando las nuevas funcionalidades!** 🚀
