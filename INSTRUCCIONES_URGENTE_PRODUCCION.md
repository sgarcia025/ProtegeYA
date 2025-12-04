# 🚨 SOLUCIÓN URGENTE - Broker no ve leads (PRODUCCIÓN)

## Situación Confirmada

Basado en las imágenes compartidas:
- ✅ **Admin dashboard**: Ve 1 lead asignado a "Estuardo Carrillo"
- ❌ **Broker dashboard**: Estuardo ve "0 leads asignados"
- ✅ **Broker**: 1/20 leads (indica que hay 1 lead asignado)
- ❌ **Problema**: El lead está asignado a un `broker_id` incorrecto en la base de datos

---

## ✅ SOLUCIÓN INMEDIATA (3 pasos)

### Paso 1: Hacer Deploy
Asegúrate de que los cambios más recientes estén en producción (ya lo hiciste ✅)

### Paso 2: Ejecutar Diagnóstico Mejorado
1. Ve a: `https://admin.protegeagt.com/configuration`
2. Login como admin
3. **Scroll down** hasta "Mantenimiento del Sistema"
4. **Click en el botón ROJO: "🔧 Diagnosticar y Reparar"**
5. **ESPERA** a que termine (aparecerá un reporte)

**IMPORTANTE**: El nuevo código ahora hace:
- ✅ Detecta leads asignados a `broker_id` inexistentes
- ✅ **REASIGNA AUTOMÁTICAMENTE** al broker correcto
- ✅ Asigna leads sin asignar a brokers que tienen 0 leads
- ✅ Te muestra un reporte detallado

### Paso 3: Verificar Resultados
En el reporte del diagnóstico verás:

**Si funcionó correctamente:**
```
✅ Correcciones Aplicadas:
• Lead [ID] (Cliente: [Nombre]) reasignado de broker inexistente 'xxx' a Estuardo Carrillo
```

**Luego:**
1. Pide a Estuardo que cierre sesión completamente
2. Que vuelva a hacer login
3. Que revise su dashboard → Debe ver el lead ahora

---

## 🔍 Si el botón no funciona o necesitas alternativa

### Opción A: Usar la API directamente

```bash
# 1. Login como admin
TOKEN=$(curl -s -X POST "https://admin.protegeagt.com/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"TU_EMAIL_ADMIN","password":"TU_PASSWORD"}' \
  | jq -r '.access_token')

# 2. Ejecutar diagnóstico y reparación
curl -X POST "https://admin.protegeagt.com/api/admin/fix-broker-leads" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  | jq '.'
```

### Opción B: Usar el script Python (si tienes acceso SSH)

```bash
# En el servidor de producción
cd /app/backend
python force_reassign_leads.py
```

Este script:
- Busca al broker por email (`amaseguros.gt@gmail.com`)
- Encuentra todos los leads en la BD
- Identifica leads asignados a `broker_id` inexistentes
- Los reasigna automáticamente al broker correcto
- Te muestra un resumen completo

---

## 📊 ¿Qué esperar ver en el diagnóstico?

**Estado ANTES del fix:**
```
Broker: Estuardo Carrillo
  Email: amaseguros.gt@gmail.com
  Leads asignados: 0
  Status: no_leads
  Issue: No tiene leads asignados
```

**Después del fix:**
```
✅ Correcciones Aplicadas:
• Lead abc-123 (Cliente: [nombre]) reasignado a Estuardo Carrillo

Broker: Estuardo Carrillo
  Leads asignados: 1
  Status: ok
  Leads: [nombre del cliente]
```

---

## ⚠️ Causas Comunes de este Problema

Este problema ocurre cuando:

1. **Broker ID cambió**: El broker fue eliminado y recreado, cambiando su `id` interno
2. **Migración de datos**: Los datos se movieron de una BD a otra con diferentes IDs
3. **Asignación manual incorrecta**: El lead se asignó con un `broker_id` que no corresponde al broker actual
4. **Múltiples instancias del mismo broker**: Hay registros duplicados en la BD

---

## ✅ Verificación Post-Fix

Después de ejecutar el diagnóstico, verifica:

### 1. En el Admin Dashboard
- Ve a: `https://admin.protegeagt.com/leads`
- Busca el lead asignado a Estuardo
- Debe seguir mostrándose correctamente

### 2. En el Broker Dashboard
```bash
# Login del broker
curl -X POST "https://admin.protegeagt.com/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"amaseguros.gt@gmail.com","password":"ProtegeYa2025!"}' \
  | jq -r '.access_token'

# Copiar el token y verificar KPIs
curl -X GET "https://admin.protegeagt.com/api/reports/kpi" \
  -H "Authorization: Bearer [TOKEN]" \
  | jq '.total_assigned_leads'

# Debe devolver: 1 (o más)
```

### 3. En la UI del Broker
- Estuardo hace login en `https://admin.protegeagt.com`
- Dashboard debe mostrar: "1 Lead Asignado" (no 0)
- Click en "Mis Leads" → Debe ver el lead

---

## 🆘 Si TODAVÍA no funciona después del fix

**Comparte esta información:**

1. **Screenshot completo** de los resultados del diagnóstico
2. **Ejecuta este comando** y comparte el resultado:
```bash
# Login del broker
curl -X GET "https://admin.protegeagt.com/api/debug/broker-leads" \
  -H "Authorization: Bearer [TOKEN_DEL_BROKER]" \
  | jq '.'
```

3. **Información del navegador**: ¿El broker probó hacer hard refresh (Ctrl+Shift+R)?

---

## 📝 Resumen de Cambios Técnicos

**Lo que el nuevo código hace automáticamente:**

1. **Detecta leads huérfanos**:
   - Busca leads asignados a `broker_id` que no existen
   - Los reasigna al broker activo

2. **Balancea asignación**:
   - Si un broker tiene 0 leads pero hay leads sin asignar
   - Asigna automáticamente hasta 5 leads a ese broker

3. **Reporta detalladamente**:
   - Muestra qué se encontró
   - Muestra qué se corrigió
   - Muestra el estado final de cada broker

**Endpoints disponibles:**
- `POST /api/admin/fix-broker-leads` - Diagnóstico automático con reparación
- `POST /api/admin/sync-broker-users` - Sincronización de usuarios
- `GET /api/debug/broker-leads` - Diagnóstico detallado (para brokers)

---

**¡El fix ya está en el código! Solo necesitas ejecutarlo desde el admin dashboard.**

**Última actualización**: 2025-12-04 02:00
**Versión**: 3.0 - Con reasignación automática
