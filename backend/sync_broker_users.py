#!/usr/bin/env python3
"""
Script para sincronizar usuarios de brokers entre collections
Asegura que todos los brokers tengan un usuario válido en auth_users
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
from passlib.context import CryptContext
from datetime import datetime, timezone, timedelta

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
GUATEMALA_TZ = timezone(timedelta(hours=-6))

async def sync_broker_users():
    """Ensure all brokers have valid users in auth_users collection"""
    
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("=" * 80)
    print("SINCRONIZACIÓN DE USUARIOS DE BROKERS")
    print("=" * 80)
    
    # Get all brokers
    brokers = await db.brokers.find({}).to_list(length=None)
    print(f"\nTotal de brokers: {len(brokers)}")
    
    fixed_count = 0
    ok_count = 0
    
    for broker in brokers:
        print(f"\n{'-' * 80}")
        print(f"Broker: {broker.get('name')}")
        print(f"Email: {broker.get('email')}")
        print(f"User ID: {broker.get('user_id')}")
        
        user_id = broker.get('user_id')
        broker_email = broker.get('email')
        
        # Check if user exists in auth_users
        user = await db.auth_users.find_one({"id": user_id})
        
        if user:
            print(f"  ✅ Usuario existe en auth_users")
            
            # Verify password is valid
            try:
                test_password = "ProtegeYa2025!"
                is_valid = pwd_context.verify(test_password, user.get('password', ''))
                if not is_valid:
                    print(f"  ⚠️  Password inválido, regenerando...")
                    new_hash = pwd_context.hash(test_password)
                    await db.auth_users.update_one(
                        {"id": user_id},
                        {"$set": {"password": new_hash}}
                    )
                    print(f"  ✅ Password actualizado")
                    fixed_count += 1
                else:
                    ok_count += 1
            except Exception as e:
                print(f"  ⚠️  Error verificando password: {e}")
                # Regenerate password
                new_hash = pwd_context.hash("ProtegeYa2025!")
                await db.auth_users.update_one(
                    {"id": user_id},
                    {"$set": {"password": new_hash}}
                )
                print(f"  ✅ Password regenerado")
                fixed_count += 1
        else:
            print(f"  ❌ Usuario NO existe en auth_users. Creando...")
            
            # Create user
            new_user = {
                "id": user_id,
                "email": broker_email,
                "password": pwd_context.hash("ProtegeYa2025!"),
                "role": "broker",
                "name": broker.get('name'),
                "active": True,
                "created_at": datetime.now(GUATEMALA_TZ).isoformat(),
                "updated_at": datetime.now(GUATEMALA_TZ).isoformat()
            }
            
            await db.auth_users.insert_one(new_user)
            print(f"  ✅ Usuario creado exitosamente")
            print(f"     Email: {broker_email}")
            print(f"     Password: ProtegeYa2025!")
            fixed_count += 1
        
        # Verify leads can be queried
        leads_count = await db.leads.count_documents({"assigned_broker_id": broker.get('id')})
        print(f"  📊 Leads asignados: {leads_count}")
    
    print(f"\n{'=' * 80}")
    print(f"RESUMEN:")
    print(f"  ✅ Brokers OK: {ok_count}")
    print(f"  🔧 Brokers reparados: {fixed_count}")
    print(f"  📊 Total procesados: {len(brokers)}")
    print(f"{'=' * 80}")
    
    if fixed_count > 0:
        print(f"\n⚠️  IMPORTANTE: Los brokers reparados deben usar:")
        print(f"     Email: [su email registrado]")
        print(f"     Password: ProtegeYa2025!")
        print(f"     Deben cambiar su contraseña después del primer login")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(sync_broker_users())
