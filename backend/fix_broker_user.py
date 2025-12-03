#!/usr/bin/env python3
"""
Script para crear el usuario faltante del broker
"""
import asyncio
import os
import uuid
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
from passlib.context import CryptContext
from datetime import datetime, timezone, timedelta

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
GUATEMALA_TZ = timezone(timedelta(hours=-6))

async def fix_broker_user():
    """Create or fix the missing broker user"""
    
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("=" * 80)
    print("REPARACIÓN DE USUARIO DEL BROKER")
    print("=" * 80)
    
    # Get broker data
    broker = await db.brokers.find_one({})
    if not broker:
        print("❌ No se encontró ningún broker")
        client.close()
        return
    
    print(f"\nBroker encontrado:")
    print(f"  Nombre: {broker.get('name')}")
    print(f"  Email: {broker.get('email')}")
    print(f"  User ID esperado: {broker.get('user_id')}")
    
    expected_user_id = broker.get('user_id')
    broker_email = broker.get('email')
    
    # Check if user exists
    existing_user = await db.users.find_one({"id": expected_user_id})
    
    if existing_user:
        print(f"\n✅ Usuario ya existe con este ID")
        print(f"   Email: {existing_user.get('email')}")
        print(f"   Role: {existing_user.get('role')}")
    else:
        print(f"\n❌ Usuario no existe. Creando usuario...")
        
        # Create new user with the correct ID
        new_user = {
            "id": expected_user_id,
            "email": broker_email,
            "password": pwd_context.hash("ProtegeYa2025!"),  # Default password
            "role": "broker",
            "name": broker.get('name'),
            "created_at": datetime.now(GUATEMALA_TZ).isoformat(),
            "updated_at": datetime.now(GUATEMALA_TZ).isoformat()
        }
        
        await db.users.insert_one(new_user)
        print(f"✅ Usuario creado exitosamente")
        print(f"   Email: {broker_email}")
        print(f"   Password temporal: ProtegeYa2025!")
        print(f"   Role: broker")
        print(f"\n⚠️  IMPORTANTE: El broker debe cambiar su contraseña después del primer login")
    
    # Verify the fix
    print(f"\n\nVERIFICANDO LA REPARACIÓN:")
    print("-" * 80)
    
    user = await db.users.find_one({"id": expected_user_id})
    if user:
        print(f"✅ Usuario verificado:")
        print(f"   ID: {user.get('id')}")
        print(f"   Email: {user.get('email')}")
        print(f"   Role: {user.get('role')}")
        
        # Now test the query that dashboard uses
        broker_data = await db.brokers.find_one({"user_id": user.get('id')})
        if broker_data:
            print(f"\n✅ Broker asociado encontrado:")
            print(f"   Broker ID: {broker_data.get('id')}")
            print(f"   Nombre: {broker_data.get('name')}")
            
            # Test lead query
            leads = await db.leads.find({"assigned_broker_id": broker_data.get('id')}).to_list(length=None)
            print(f"\n✅ Leads asignados a este broker: {len(leads)}")
            for lead in leads[:5]:
                print(f"   - {lead.get('phone_number')}: {lead.get('name', 'Sin nombre')}")
        else:
            print(f"\n❌ No se encontró broker asociado")
    else:
        print(f"❌ Error: Usuario no se pudo crear o verificar")
    
    print("\n" + "=" * 80)
    print("REPARACIÓN COMPLETA")
    print("=" * 80)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(fix_broker_user())
