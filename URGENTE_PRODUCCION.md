# 🚨 SOLUCIÓN URGENTE: Broker no ve leads en PRODUCCIÓN

## Problema Identificado
El broker `amaseguros.gt@gmail.com` puede hacer login pero ve **0 Leads Asignados** aunque el admin ve leads asignados a él.

---

## ✅ SOLUCIÓN INMEDIATA

### Paso 1: Verificar que hiciste el deploy
Asegúrate de que los cambios más recientes están en producción.

### Paso 2: Ejecutar el endpoint de sincronización en PRODUCCIÓN

**Opción A: Desde el Admin Dashboard (MÁS FÁCIL)**

1. Ir a: `https://admin.protegeagt.com`
2. Login como admin
3. Ir a: **Configuración del Sistema** (Configuration)
4. Hacer scroll hasta **"🔧 Mantenimiento del Sistema"**
5. Click en **"Sincronizar Brokers"**
6. Ver los resultados

**Opción B: Usar cURL (RÁPIDO)**

```bash
# 1. Login como admin
curl -X POST "https://admin.protegeagt.com/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@protegeya.com","password":"TU_PASSWORD_ADMIN"}' \
  | jq -r '.access_token'

# COPIAR EL TOKEN QUE TE DEVUELVE

# 2. Ejecutar sincronización
curl -X POST "https://admin.protegeagt.com/api/admin/sync-broker-users" \
  -H "Authorization: Bearer [PEGAR_TOKEN_AQUÍ]" \
  -H "Content-Type: application/json" \
  | jq '.'
```

### Paso 3: Diagnosticar el broker específico

Después de sincronizar, ejecuta el diagnóstico:

```bash
# 1. Login como el broker
curl -X POST "https://admin.protegeagt.com/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"amaseguros.gt@gmail.com","password":"ProtegeYa2025!"}' \
  | jq -r '.access_token'

# COPIAR EL TOKEN

# 2. Verificar los KPIs
curl -X GET "https://admin.protegeagt.com/api/reports/kpi" \
  -H "Authorization: Bearer [TOKEN_BROKER]" \
  | jq '.'

# 3. Diagnóstico detallado
curl -X GET "https://admin.protegeagt.com/api/debug/broker-leads" \
  -H "Authorization: Bearer [TOKEN_BROKER]" \
  | jq '.'
```

### Paso 4: Verificar resultados

La respuesta de `/api/debug/broker-leads` te dirá:
- ✅ Si el broker está correctamente configurado
- ✅ Cuántos leads tiene asignados
- ✅ Información de los leads
- ❌ Si hay algún problema de configuración

---

## 🔍 DIAGNÓSTICO ADICIONAL (Si aún no funciona)

### Si tienes acceso SSH al servidor de producción:

```bash
# Conectar al servidor de producción
ssh usuario@servidor-produccion

# Ir al directorio del backend
cd /app/backend

# Ejecutar script de diagnóstico
python fix_production_broker.py
```

Este script te dirá exactamente qué está mal con el broker `amaseguros.gt@gmail.com`.

---

## 📋 CHECKLIST DE VERIFICACIÓN

- [ ] Los cambios están deployados en producción
- [ ] Ejecutaste la sincronización de brokers
- [ ] La sincronización reportó éxito
- [ ] El broker puede hacer login
- [ ] Ejecutaste el endpoint de diagnóstico `/api/debug/broker-leads`
- [ ] Verificaste que el broker tiene leads asignados en la BD

---

## 🆘 SI NADA FUNCIONA

Si después de todos estos pasos el broker SIGUE sin ver sus leads:

### Verificación Manual en la Base de Datos

```javascript
// Conectar a MongoDB de producción

// 1. Buscar el broker
db.brokers.findOne({email: "amaseguros.gt@gmail.com"})
// Anotar el "id" del broker

// 2. Verificar usuario en auth_users
db.auth_users.findOne({email: "amaseguros.gt@gmail.com"})
// Verificar que el "id" coincida con el "user_id" del broker

// 3. Contar leads asignados
db.leads.count({assigned_broker_id: "[ID_DEL_BROKER_AQUÍ]"})

// 4. Ver los leads
db.leads.find({assigned_broker_id: "[ID_DEL_BROKER_AQUÍ]"})
```

### Posibles Causas

1. **El broker no tiene leads asignados realmente**
   - Solución: Asignar leads desde el admin dashboard

2. **El user_id del broker no coincide con el id en auth_users**
   - Solución: Ejecutar `python sync_broker_users.py`

3. **Cache del navegador**
   - Solución: Pedir al broker que haga Ctrl+Shift+R (hard refresh)

4. **Token expirado**
   - Solución: Pedir al broker que cierre sesión y vuelva a entrar

---

## 📞 INFORMACIÓN PARA SOPORTE

Si me contactas, comparte:

1. **Respuesta completa** del endpoint `/api/admin/sync-broker-users`
2. **Respuesta completa** del endpoint `/api/debug/broker-leads`
3. **Screenshot** del admin dashboard mostrando leads asignados al broker
4. **Screenshot** del dashboard del broker mostrando "0 leads"
5. **Salida** del script `fix_production_broker.py` si lo ejecutaste

---

**Última actualización**: 2025-12-04
**Ambiente**: PRODUCCIÓN (admin.protegeagt.com)
