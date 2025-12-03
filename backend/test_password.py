#!/usr/bin/env python3
"""
Script para probar el password
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
from passlib.context import CryptContext

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def test_password():
    """Test password hashing and verification"""
    
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("=" * 80)
    print("PRUEBA DE PASSWORD")
    print("=" * 80)
    
    # Get user
    user = await db.auth_users.find_one({"email": "broker@protegeya.com"})
    
    if not user:
        print("❌ Usuario no encontrado en auth_users")
        client.close()
        return
    
    print(f"\nUsuario encontrado:")
    print(f"  Email: {user.get('email')}")
    print(f"  ID: {user.get('id')}")
    print(f"  Role: {user.get('role')}")
    
    stored_hash = user.get('password')
    print(f"\nHash almacenado: {stored_hash[:50]}...")
    
    # Test password
    test_password = "ProtegeYa2025!"
    print(f"\nProbando password: {test_password}")
    
    try:
        is_valid = pwd_context.verify(test_password, stored_hash)
        print(f"Resultado: {'✅ VÁLIDO' if is_valid else '❌ INVÁLIDO'}")
    except Exception as e:
        print(f"❌ Error al verificar: {e}")
    
    # Create new hash
    print(f"\nCreando nuevo hash...")
    new_hash = pwd_context.hash(test_password)
    print(f"Nuevo hash: {new_hash[:50]}...")
    
    # Update user with new hash
    print(f"\nActualizando usuario con nuevo hash...")
    await db.auth_users.update_one(
        {"email": "broker@protegeya.com"},
        {"$set": {"password": new_hash}}
    )
    print(f"✅ Hash actualizado")
    
    # Verify again
    updated_user = await db.auth_users.find_one({"email": "broker@protegeya.com"})
    updated_hash = updated_user.get('password')
    is_valid = pwd_context.verify(test_password, updated_hash)
    print(f"\nVerificación después de actualizar: {'✅ VÁLIDO' if is_valid else '❌ INVÁLIDO'}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(test_password())
