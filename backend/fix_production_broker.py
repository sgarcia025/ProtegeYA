#!/usr/bin/env python3
"""
Fix específico para broker amaseguros.gt@gmail.com en producción
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def fix_broker():
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    broker_email = "amaseguros.gt@gmail.com"
    
    print("=" * 80)
    print(f"DIAGNÓSTICO Y FIX PARA: {broker_email}")
    print("=" * 80)
    
    # 1. Buscar el broker por email
    print("\n1. BUSCANDO BROKER POR EMAIL...")
    broker = await db.brokers.find_one({"email": broker_email})
    
    if not broker:
        print(f"❌ NO SE ENCONTRÓ BROKER CON EMAIL: {broker_email}")
        print("\nBrokers disponibles:")
        all_brokers = await db.brokers.find({}).to_list(length=None)
        for b in all_brokers:
            print(f"  - {b.get('email')} ({b.get('name')})")
        client.close()
        return
    
    print(f"✅ Broker encontrado:")
    print(f"   ID: {broker.get('id')}")
    print(f"   Nombre: {broker.get('name')}")
    print(f"   Email: {broker.get('email')}")
    print(f"   User ID: {broker.get('user_id')}")
    
    broker_id = broker.get('id')
    user_id = broker.get('user_id')
    
    # 2. Verificar usuario en auth_users
    print(f"\n2. VERIFICANDO USUARIO EN AUTH_USERS...")
    user = await db.auth_users.find_one({"id": user_id})
    
    if user:
        print(f"✅ Usuario existe en auth_users")
        print(f"   Email: {user.get('email')}")
        print(f"   Role: {user.get('role')}")
    else:
        print(f"❌ Usuario NO existe en auth_users")
        print(f"   Buscando por email...")
        user_by_email = await db.auth_users.find_one({"email": broker_email})
        if user_by_email:
            print(f"⚠️  Encontrado usuario con email pero diferente ID:")
            print(f"   User ID en auth_users: {user_by_email.get('id')}")
            print(f"   User ID en broker: {user_id}")
            print(f"   ¡ESTE ES EL PROBLEMA!")
    
    # 3. Buscar leads asignados a este broker
    print(f"\n3. BUSCANDO LEADS ASIGNADOS AL BROKER...")
    query = {"assigned_broker_id": broker_id}
    leads = await db.leads.find(query).to_list(length=None)
    
    print(f"Query: {query}")
    print(f"Resultado: {len(leads)} leads encontrados")
    
    if leads:
        print(f"\n✅ LEADS ASIGNADOS:")
        for lead in leads:
            print(f"   - ID: {lead.get('id')}")
            print(f"     Nombre: {lead.get('name', 'Sin nombre')}")
            print(f"     Teléfono: {lead.get('phone_number')}")
            print(f"     Status: {lead.get('status')}")
            print(f"     Broker Status: {lead.get('broker_status')}")
    else:
        print(f"\n❌ NO HAY LEADS ASIGNADOS A ESTE BROKER")
        
        # Buscar todos los leads asignados
        print(f"\n   Buscando TODOS los leads asignados en la BD...")
        all_assigned = await db.leads.find({"assigned_broker_id": {"$ne": None}}).to_list(length=None)
        print(f"   Total de leads asignados: {len(all_assigned)}")
        
        if all_assigned:
            print(f"\n   Leads asignados a otros brokers:")
            for lead in all_assigned:
                assigned_to = lead.get('assigned_broker_id')
                print(f"   - Lead {lead.get('id')}: asignado a '{assigned_to}'")
                
                # Ver si el broker_id es diferente por alguna razón
                if assigned_to:
                    other_broker = await db.brokers.find_one({"id": assigned_to})
                    if other_broker:
                        print(f"     → Broker: {other_broker.get('name')} ({other_broker.get('email')})")
                    else:
                        print(f"     → ⚠️ Broker no encontrado para ID: {assigned_to}")
    
    # 4. Verificar si hay leads que DEBERÍAN estar asignados a este broker
    print(f"\n4. VERIFICANDO LEADS SIN ASIGNAR...")
    unassigned = await db.leads.find({
        "$or": [
            {"assigned_broker_id": None},
            {"assigned_broker_id": {"$exists": False}}
        ],
        "status": {"$in": ["QuotedNoPreference", "PendingData"]}
    }).to_list(length=None)
    
    print(f"   Leads sin asignar: {len(unassigned)}")
    
    if unassigned:
        print(f"\n   ¿Deseas asignar estos leads al broker {broker.get('name')}?")
        print(f"   (Este script no lo hará automáticamente)")
    
    # 5. Probar la query que hace el endpoint
    print(f"\n5. SIMULANDO QUERY DEL ENDPOINT /api/reports/kpi...")
    total_leads = await db.leads.count_documents({"assigned_broker_id": broker_id})
    closed_won = await db.leads.count_documents({
        "assigned_broker_id": broker_id,
        "broker_status": "ClosedWon"
    })
    
    print(f"   Total leads asignados: {total_leads}")
    print(f"   Closed won: {closed_won}")
    print(f"   Esto es lo que debería ver en el dashboard")
    
    print("\n" + "=" * 80)
    print("RESUMEN:")
    print(f"  Broker: {broker.get('name')}")
    print(f"  Leads asignados: {total_leads}")
    print(f"  Usuario en auth_users: {'✅ Sí' if user else '❌ No'}")
    
    if total_leads == 0:
        print(f"\n⚠️ PROBLEMA: El broker NO tiene leads asignados en la base de datos")
        print(f"   Solución: Asignar leads manualmente desde el admin dashboard")
    elif not user:
        print(f"\n⚠️ PROBLEMA: El usuario del broker no existe en auth_users")
        print(f"   Solución: Ejecutar sync_broker_users.py")
    else:
        print(f"\n✅ TODO ESTÁ CORRECTO - El broker debería ver sus leads")
        print(f"   Si no los ve, puede ser problema de cache del navegador")
        print(f"   Solución: Pedir al broker que haga Ctrl+Shift+R (hard refresh)")
    
    print("=" * 80)
    client.close()

if __name__ == "__main__":
    asyncio.run(fix_broker())
