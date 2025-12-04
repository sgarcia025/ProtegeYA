# INSTRUCCIONES PARA REPARAR ACCESO DE BROKERS EN PRODUCCIÓN

## PROBLEMA
Los brokers tienen leads asignados en la base de datos, pero no pueden verlos en su dashboard porque su usuario no existe en la colección `auth_users`.

## SÍNTOMAS
- El admin puede ver los leads asignados al broker
- El broker puede hacer login (o no puede)
- El broker ve "0 Leads Asignados" en su dashboard
- Los leads aparecen correctamente en el admin dashboard

## SOLUCIÓN

### Opción 1: Ejecutar script automático (RECOMENDADO)

1. Conectarte al servidor de producción por SSH o terminal

2. Ejecutar el script de sincronización:
```bash
cd /app/backend
python sync_broker_users.py
```

3. El script hará:
   - Verificar todos los brokers en la base de datos
   - Crear usuarios faltantes en `auth_users`
   - Regenerar contraseñas si están corruptas
   - Reportar el estado de cada broker

4. Si el script crea o repara usuarios, mostrará:
   ```
   Email: [email del broker]
   Password: ProtegeYa2025!
   ```
   **IMPORTANTE**: El broker debe cambiar esta contraseña temporal al hacer login

### Opción 2: Ejecutar script de diagnóstico primero

Si quieres ver qué está mal antes de reparar:

```bash
cd /app/backend
python debug_broker_leads.py
```

Este script mostrará:
- Todos los brokers en el sistema
- Si tienen usuarios asociados
- Cuántos leads tienen asignados
- Si hay discrepancias

### Opción 3: Reparación manual desde MongoDB

Si no puedes ejecutar los scripts:

1. Conectar a MongoDB
2. Buscar el broker:
   ```javascript
   db.brokers.find({email: "broker@protegeya.com"})
   ```

3. Anotar el `user_id` del broker

4. Verificar si existe el usuario:
   ```javascript
   db.auth_users.findOne({id: "[USER_ID_DEL_BROKER]"})
   ```

5. Si no existe, crear el usuario:
   ```javascript
   db.auth_users.insertOne({
     id: "[USER_ID_DEL_BROKER]",
     email: "broker@protegeya.com",
     password: "$2b$12$[HASH_BCRYxPT]",  // Hash de "ProtegeYa2025!"
     role: "broker",
     name: "Nombre del Broker",
     active: true,
     created_at: new Date().toISOString(),
     updated_at: new Date().toISOString()
   })
   ```

## PREVENCIÓN

### Después de cada deploy

Es importante ejecutar el script de sincronización después de cada deploy para prevenir este problema:

```bash
cd /app/backend && python sync_broker_users.py
```

### Al crear nuevos brokers

El código actual (server.py) ya tiene la lógica para crear usuarios automáticamente al registrar brokers, pero si se crean brokers manualmente en la base de datos, asegúrate de:

1. Crear el documento en `brokers` collection
2. Crear el documento correspondiente en `auth_users` collection con el mismo `user_id`

## VERIFICACIÓN

Después de ejecutar el fix:

1. **Probar login del broker:**
   ```bash
   curl -X POST "https://[TU-DOMINIO]/api/auth/login" \
   -H "Content-Type: application/json" \
   -d '{"email": "broker@protegeya.com", "password": "ProtegeYa2025!"}'
   ```
   
   Deberías recibir un token de acceso.

2. **Verificar que el broker vea sus leads:**
   Usar el token del paso anterior:
   ```bash
   curl -X GET "https://[TU-DOMINIO]/api/leads" \
   -H "Authorization: Bearer [TOKEN]"
   ```
   
   Deberías ver los leads asignados al broker.

3. **Verificar en el dashboard:**
   - El broker hace login
   - Ve sus leads asignados en "Mis Leads"
   - El contador de "Leads Asignados" muestra el número correcto

## CONTACTO

Si necesitas ayuda adicional o el problema persiste después de ejecutar estos pasos, por favor proporciona:
- Logs del script de sincronización
- Email del broker afectado
- Capturas de pantalla del problema

---

**Última actualización**: 2025-12-03
