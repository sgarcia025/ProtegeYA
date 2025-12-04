# 🚨 PROBLEMA CRÍTICO: Frontend y Backend usan BD DIFERENTES

## 🎯 Problema Confirmado

Tu imagen muestra:
- **URL del login**: `admin.protegeyagt.com`
- **URL de la API**: `protegeyacrm.emergent.host` ❌

**Esto significa:**
- El **admin dashboard** está consultando la BD de `protegeyagt.com`
- El **broker dashboard** está consultando la BD de `protegeyacrm.emergent.host`
- Son **DOS BASES DE DATOS DIFERENTES**

Por eso:
- ✅ Admin ve 1 lead asignado (está en BD1)
- ❌ Broker ve 0 leads (consulta BD2 donde no hay datos)

---

## ✅ SOLUCIÓN INMEDIATA

### Opción 1: Verificar Variables de Entorno en Emergent

1. Ve a tu proyecto en Emergent
2. Busca la sección de **"Variables de Entorno"** o **"Environment Variables"**
3. Busca la variable `REACT_APP_BACKEND_URL`
4. **Debe estar configurada como:** `https://admin.protegeagt.com`
5. **NO debe ser:** `https://protegeyacrm.emergent.host`

### Opción 2: Verificar el archivo .env en producción

El archivo `/app/frontend/.env` en producción debe tener:

```bash
REACT_APP_BACKEND_URL=https://admin.protegeagt.com
```

**NO debe tener:**
```bash
REACT_APP_BACKEND_URL=https://protegeyacrm.emergent.host
```

---

## 🔧 Cómo Corregirlo

### Si usas Emergent Dashboard:

1. **Ve a tu proyecto** en Emergent
2. **Settings** o **Variables de Entorno**
3. **Edita** `REACT_APP_BACKEND_URL`
4. **Cambia** de `protegeyacrm.emergent.host` a `admin.protegeagt.com`
5. **Guarda** los cambios
6. **Re-deploy** la aplicación

### Si tienes acceso al servidor:

```bash
# En el servidor de producción
cd /app/frontend

# Edita el archivo .env
nano .env

# Cambia la línea a:
REACT_APP_BACKEND_URL=https://admin.protegeagt.com

# Guarda y reinicia el frontend
sudo supervisorctl restart frontend
```

---

## 📋 Verificación

Después de hacer el cambio:

### 1. Verifica que el frontend use la URL correcta

```bash
# Abre el navegador en modo incógnito
# Ve a: https://admin.protegeagt.com
# Abre DevTools (F12)
# Ve a la pestaña "Network"
# Intenta hacer login
# Verifica que las llamadas API vayan a: admin.protegeagt.com/api/...
# NO deben ir a: protegeyacrm.emergent.host
```

### 2. Verifica que el broker vea sus leads

```bash
# Login del broker: amaseguros.gt@gmail.com
# Dashboard debe mostrar: 1 Lead Asignado
# NO: 0 Leads
```

---

## 🔍 Por qué pasó esto

Posibles causas:

1. **Múltiples deploys**: Deployaste en diferentes momentos con diferentes configuraciones
2. **Variables de entorno incorrectas**: La variable `REACT_APP_BACKEND_URL` quedó con un valor antiguo
3. **Cache de build**: El build del frontend está usando una versión vieja del `.env`
4. **Dominio temporal**: `protegeyacrm.emergent.host` puede ser un dominio temporal que Emergent asigna automáticamente

---

## ⚠️ IMPORTANTE

**Este problema NO se puede resolver desde el código.**

Es un problema de **configuración de infraestructura**. Necesitas:

1. ✅ Asegurar que `REACT_APP_BACKEND_URL` apunte a `admin.protegeagt.com`
2. ✅ Re-deployar el frontend con la configuración correcta
3. ✅ Limpiar cache del navegador después del deploy

**Todos los fixes que hice anteriormente funcionarán DESPUÉS de corregir esta configuración.**

---

## 🆘 Si no tienes acceso a las variables de entorno

**Contacta al soporte de Emergent** y pídeles que:

1. Verifiquen la variable `REACT_APP_BACKEND_URL` en tu proyecto
2. La cambien a: `https://admin.protegeagt.com`
3. Re-desplieguen el frontend

O alternativamente:

**Usa el dominio temporal como URL principal:**
- Cambia TODOS los accesos a usar: `https://protegeyacrm.emergent.host`
- Pero esto significaría que tendrías que actualizar DNS, certificados, etc.

---

## ✅ Checklist Post-Fix

Después de corregir la URL:

- [ ] Frontend hace llamadas API a `admin.protegeagt.com/api/...`
- [ ] NO hace llamadas a `protegeyacrm.emergent.host`
- [ ] El broker puede hacer login exitosamente
- [ ] El broker VE sus leads asignados (1 lead)
- [ ] El admin sigue viendo los leads correctamente

---

**Este es el problema raíz. Una vez corregido, todo funcionará correctamente.**

**Última actualización**: 2025-12-04 02:15
