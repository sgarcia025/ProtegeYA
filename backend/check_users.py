#!/usr/bin/env python3
"""
Script para verificar usuarios en la base de datos
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def check_users():
    """Check all users in the system"""
    
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("=" * 80)
    print("USUARIOS EN EL SISTEMA")
    print("=" * 80)
    
    users = await db.users.find({}).to_list(length=None)
    print(f"\nTotal de usuarios: {len(users)}\n")
    
    for user in users:
        print(f"User ID: {user.get('id')}")
        print(f"Email: {user.get('email')}")
        print(f"Role: {user.get('role')}")
        print(f"Nombre: {user.get('name', 'Sin nombre')}")
        print("-" * 80)
    
    # Check brokers
    print("\n\nBROKERS Y SUS USER_IDS:")
    print("=" * 80)
    brokers = await db.brokers.find({}).to_list(length=None)
    
    for broker in brokers:
        broker_user_id = broker.get('user_id')
        print(f"\nBroker: {broker.get('name')}")
        print(f"Broker ID: {broker.get('id')}")
        print(f"User ID esperado: {broker_user_id}")
        
        # Check if user exists
        user = await db.users.find_one({"id": broker_user_id})
        if user:
            print(f"✅ Usuario encontrado: {user.get('email')}")
        else:
            print(f"❌ Usuario NO encontrado")
            print(f"\nBuscando usuarios con email similar a broker email: {broker.get('email')}")
            similar_user = await db.users.find_one({"email": broker.get('email')})
            if similar_user:
                print(f"  ⚠️  Encontrado usuario con mismo email pero diferente ID:")
                print(f"     User ID en users: {similar_user.get('id')}")
                print(f"     User ID en broker: {broker_user_id}")
                print(f"     --> ESTE ES EL PROBLEMA: Los IDs no coinciden")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_users())
