# 🔧 SOLUCIÓN: Brokers no ven leads asignados en Producción

## Problema Identificado
El broker puede hacer login, pero no ve los leads que el admin le ha asignado. Esto ocurre porque el usuario del broker no existe correctamente en la colección `auth_users` de la base de datos de producción.

---

## ✅ SOLUCIÓN RÁPIDA (API Endpoint)

He creado un endpoint de administración que sincroniza automáticamente todos los usuarios de brokers. Sigue estos pasos:

### Paso 1: Hacer Login como Admin

En tu navegador o Postman, haz una petición POST a:

```
URL: https://admin.protegeagt.com/api/auth/login
Método: POST
Headers: Content-Type: application/json
Body:
{
  "email": "admin@protegeya.com",
  "password": "[TU_PASSWORD_ADMIN]"
}
```

**Respuesta esperada:**
```json
{
  "access_token": "eyJhbGc...[TOKEN_LARGO]",
  "token_type": "bearer",
  "user": {...}
}
```

**Copia el `access_token`** para el siguiente paso.

### Paso 2: Ejecutar Sincronización de Brokers

Ahora ejecuta el endpoint de sincronización:

```
URL: https://admin.protegeagt.com/api/admin/sync-broker-users
Método: POST
Headers: 
  - Content-Type: application/json
  - Authorization: Bearer [PEGA_EL_TOKEN_AQUÍ]
Body: (vacío)
```

**Respuesta esperada:**
```json
{
  "success": true,
  "message": "Broker user synchronization completed",
  "results": {
    "brokers_checked": 1,
    "users_created": 1,  // o 0 si ya existía
    "passwords_fixed": 0,
    "errors": [],
    "brokers": [
      {
        "name": "Estuardo Carrillo",
        "email": "broker@example.com",
        "user_id": "...",
        "status": "user_created",  // o "ok" si ya existía
        "temp_password": "ProtegeYa2025!",  // solo si fue creado
        "leads_assigned": 2
      }
    ]
  },
  "note": "Brokers with new/fixed passwords should use: ProtegeYa2025!"
}
```

### Paso 3: Verificar el Resultado

Revisa la respuesta:

- **`"status": "ok"`** → El broker ya estaba bien configurado
- **`"status": "user_created"`** → Se creó el usuario del broker
- **`"status": "password_fixed"`** → Se regeneró la contraseña
- **`"leads_assigned": X`** → Cuántos leads tiene asignados el broker

### Paso 4: Informar al Broker

Si el status fue `"user_created"` o `"password_fixed"`, informa al broker:

```
Email: [email del broker según la respuesta]
Password temporal: ProtegeYa2025!

IMPORTANTE: Debe cambiar esta contraseña al hacer login.
```

### Paso 5: Probar el Login del Broker

El broker debe:
1. Ir a: `https://admin.protegeagt.com`
2. Hacer login con:
   - Email: su email registrado
   - Password: ProtegeYa2025!
3. Ir a "Mis Leads"
4. Verificar que ve todos sus leads asignados

---

## 🚀 COMANDOS CURL (Alternativa)

Si prefieres usar curl desde la terminal:

```bash
# Paso 1: Login como admin
ADMIN_TOKEN=$(curl -X POST "https://admin.protegeagt.com/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@protegeya.com","password":"[TU_PASSWORD]"}' \
  | jq -r '.access_token')

# Paso 2: Sincronizar brokers
curl -X POST "https://admin.protegeagt.com/api/admin/sync-broker-users" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" | jq '.'
```

---

## 🔄 PREVENCIÓN FUTURA

Para evitar este problema después de futuros deploys:

### Opción A: Ejecutar después de cada deploy

Después de hacer deploy a producción, ejecuta el endpoint de sincronización (Pasos 1 y 2 de arriba).

### Opción B: Script automático (si tienes acceso SSH)

Si tienes acceso SSH al servidor de producción:

```bash
cd /app/backend
python sync_broker_users.py
```

---

## ❓ Troubleshooting

### Error: "Invalid credentials" al hacer login como admin
- Verifica que el email y password del admin sean correctos
- Prueba resetear la contraseña del admin desde la base de datos

### Error: "Unauthorized" al ejecutar sincronización
- El token expiró (24 horas de validez)
- Vuelve a hacer login (Paso 1) para obtener un nuevo token

### El broker sigue sin ver leads después de sincronizar
1. Verifica que la respuesta mostró `"leads_assigned": X` donde X > 0
2. Pide al broker que cierre sesión completamente
3. Pide al broker que haga login nuevamente
4. Si el problema persiste, revisa los logs del backend en producción

### "Leads Asignados: 0" en el resultado de sincronización
- Esto significa que efectivamente no hay leads asignados a ese broker en la base de datos
- Verifica en el admin dashboard si los leads están asignados al broker correcto
- Puede que los leads estén asignados a un broker_id diferente

---

## 📞 Soporte

Si el problema persiste después de ejecutar estos pasos, proporciona:
1. La respuesta completa del endpoint `/api/admin/sync-broker-users`
2. Screenshot del admin dashboard mostrando los leads asignados
3. Screenshot del broker dashboard mostrando "0 leads"
4. Email del broker afectado

---

**Última actualización**: 2025-12-03
**Versión**: 1.0
