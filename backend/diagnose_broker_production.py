#!/usr/bin/env python3
"""
Diagnóstico urgente para broker que no ve leads
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def diagnose():
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("=" * 80)
    print("DIAGNÓSTICO URGENTE - BROKER NO VE LEADS")
    print("=" * 80)
    
    # 1. Listar TODOS los brokers
    print("\n1. BROKERS EN BASE DE DATOS:")
    brokers = await db.brokers.find({}).to_list(length=None)
    for broker in brokers:
        print(f"\n  Broker:")
        print(f"    ID: {broker.get('id')}")
        print(f"    Nombre: {broker.get('name')}")
        print(f"    Email: {broker.get('email')}")
        print(f"    User ID: {broker.get('user_id')}")
        
        # Check auth_users
        user = await db.auth_users.find_one({"id": broker.get('user_id')})
        if user:
            print(f"    ✅ Usuario existe en auth_users")
            print(f"       Email en auth_users: {user.get('email')}")
            print(f"       Role: {user.get('role')}")
        else:
            print(f"    ❌ Usuario NO existe en auth_users")
    
    # 2. Listar TODOS los leads asignados
    print("\n\n2. TODOS LOS LEADS ASIGNADOS:")
    all_leads = await db.leads.find({"assigned_broker_id": {"$ne": None}}).to_list(length=None)
    print(f"   Total: {len(all_leads)} leads asignados")
    
    for lead in all_leads:
        print(f"\n  Lead:")
        print(f"    ID: {lead.get('id')}")
        print(f"    Nombre: {lead.get('name', 'Sin nombre')}")
        print(f"    Teléfono: {lead.get('phone_number')}")
        print(f"    Assigned Broker ID: {lead.get('assigned_broker_id')}")
        
        # Find broker
        broker = await db.brokers.find_one({"id": lead.get('assigned_broker_id')})
        if broker:
            print(f"    ✅ Broker encontrado: {broker.get('name')}")
        else:
            print(f"    ❌ Broker NO encontrado para ID: {lead.get('assigned_broker_id')}")
    
    # 3. Simular la query que hace el endpoint
    print("\n\n3. SIMULACIÓN DE QUERY DEL ENDPOINT GET /api/leads:")
    for broker in brokers:
        print(f"\n  Para broker: {broker.get('name')}")
        print(f"  User ID: {broker.get('user_id')}")
        print(f"  Broker ID: {broker.get('id')}")
        
        # Esta es EXACTAMENTE la query que hace el endpoint
        query = {"assigned_broker_id": broker.get('id')}
        leads = await db.leads.find(query).to_list(length=None)
        
        print(f"  Query: {query}")
        print(f"  Resultado: {len(leads)} leads encontrados")
        
        if leads:
            for lead in leads:
                print(f"    - {lead.get('id')}: {lead.get('name', 'Sin nombre')} ({lead.get('phone_number')})")
        else:
            print(f"    ⚠️ NO SE ENCONTRARON LEADS CON ESTA QUERY")
            
            # Buscar si hay leads con broker_id similar
            print(f"\n  Buscando leads con cualquier assigned_broker_id...")
            all_assigned = await db.leads.find({"assigned_broker_id": {"$exists": True}}).to_list(length=None)
            print(f"  Total de leads con assigned_broker_id: {len(all_assigned)}")
            
            for lead in all_assigned:
                lead_broker_id = lead.get('assigned_broker_id')
                broker_id = broker.get('id')
                
                print(f"\n    Lead {lead.get('id')}:")
                print(f"      assigned_broker_id: '{lead_broker_id}' (tipo: {type(lead_broker_id).__name__})")
                print(f"      broker.id buscado: '{broker_id}' (tipo: {type(broker_id).__name__})")
                print(f"      ¿Son iguales? {lead_broker_id == broker_id}")
                print(f"      ¿Son iguales con str()? {str(lead_broker_id) == str(broker_id)}")
    
    # 4. Verificar colecciones
    print("\n\n4. COLECCIONES EN LA BASE DE DATOS:")
    collections = await db.list_collection_names()
    relevant = [c for c in collections if 'broker' in c.lower() or 'lead' in c.lower() or 'user' in c.lower()]
    for col in relevant:
        count = await db[col].count_documents({})
        print(f"  {col}: {count} documentos")
    
    print("\n" + "=" * 80)
    client.close()

if __name__ == "__main__":
    asyncio.run(diagnose())
