#!/usr/bin/env python3
"""
Script de diagnóstico para el problema de asignación de leads a brokers
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def diagnose_broker_leads():
    """Diagnose broker-lead assignment issues"""
    
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("=" * 80)
    print("DIAGNÓSTICO DE ASIGNACIÓN DE LEADS A BROKERS")
    print("=" * 80)
    
    # 1. Check brokers
    print("\n1. BROKERS EN EL SISTEMA:")
    print("-" * 80)
    brokers = await db.brokers.find({}).to_list(length=None)
    print(f"Total de brokers: {len(brokers)}")
    
    for broker in brokers:
        print(f"\n  Broker ID: {broker.get('id')}")
        print(f"  Nombre: {broker.get('name')}")
        print(f"  Email: {broker.get('email')}")
        print(f"  User ID: {broker.get('user_id')}")
        print(f"  Status: {broker.get('subscription_status')}")
        print(f"  Leads actuales: {broker.get('current_month_leads', 0)}")
        print(f"  Cuota mensual: {broker.get('monthly_lead_quota', 0)}")
    
    # 2. Check users associated with brokers
    print("\n\n2. USUARIOS ASOCIADOS A BROKERS:")
    print("-" * 80)
    for broker in brokers:
        user_id = broker.get('user_id')
        if user_id:
            user = await db.users.find_one({"id": user_id})
            if user:
                print(f"\n  User ID: {user.get('id')}")
                print(f"  Email: {user.get('email')}")
                print(f"  Role: {user.get('role')}")
            else:
                print(f"\n  ⚠️  Usuario no encontrado para user_id: {user_id}")
    
    # 3. Check leads with assigned brokers
    print("\n\n3. LEADS ASIGNADOS:")
    print("-" * 80)
    assigned_leads = await db.leads.find({"assigned_broker_id": {"$exists": True, "$ne": None}}).to_list(length=None)
    print(f"Total de leads asignados: {len(assigned_leads)}")
    
    for lead in assigned_leads[:10]:  # Show first 10
        print(f"\n  Lead ID: {lead.get('id')}")
        print(f"  Teléfono: {lead.get('phone_number')}")
        print(f"  Nombre: {lead.get('name', 'Sin nombre')}")
        print(f"  Status: {lead.get('status')}")
        print(f"  Broker Status: {lead.get('broker_status')}")
        print(f"  Assigned Broker ID: {lead.get('assigned_broker_id')}")
        print(f"  Fecha creación: {lead.get('created_at')}")
        
        # Check if broker exists
        assigned_broker_id = lead.get('assigned_broker_id')
        broker = await db.brokers.find_one({"id": assigned_broker_id})
        if broker:
            print(f"  ✅ Broker encontrado: {broker.get('name')}")
        else:
            print(f"  ❌ Broker NO encontrado para ID: {assigned_broker_id}")
    
    # 4. Verify query that broker dashboard uses
    print("\n\n4. PRUEBA DE QUERY DEL DASHBOARD DEL BROKER:")
    print("-" * 80)
    for broker in brokers:
        broker_id = broker.get('id')
        print(f"\n  Buscando leads para broker: {broker.get('name')} (ID: {broker_id})")
        
        # This is the query used in the endpoint
        query = {"assigned_broker_id": broker_id}
        broker_leads = await db.leads.find(query).to_list(length=None)
        
        print(f"  Leads encontrados: {len(broker_leads)}")
        if broker_leads:
            for lead in broker_leads[:5]:
                print(f"    - Lead {lead.get('id')}: {lead.get('phone_number')} - {lead.get('name', 'Sin nombre')}")
        else:
            print(f"  ⚠️  No se encontraron leads para este broker")
            
            # Check if there are leads with this broker_id but stored differently
            print(f"\n  Verificando si hay variaciones en el formato del broker_id...")
            all_leads = await db.leads.find({}).to_list(length=None)
            matches = []
            for lead in all_leads:
                lead_broker_id = lead.get('assigned_broker_id')
                if lead_broker_id:
                    # Check various comparison methods
                    if str(lead_broker_id) == str(broker_id):
                        matches.append(lead)
                        print(f"    ✅ Match encontrado: Lead {lead.get('id')}")
                        print(f"       Broker ID en lead: '{lead_broker_id}' (tipo: {type(lead_broker_id).__name__})")
                        print(f"       Broker ID buscado: '{broker_id}' (tipo: {type(broker_id).__name__})")
            
            if not matches:
                print(f"    ❌ No se encontraron matches incluso con conversión de tipos")
    
    # 5. Check for orphaned leads
    print("\n\n5. LEADS HUÉRFANOS (broker_id asignado pero broker no existe):")
    print("-" * 80)
    all_leads = await db.leads.find({"assigned_broker_id": {"$exists": True, "$ne": None}}).to_list(length=None)
    broker_ids = {b.get('id') for b in brokers}
    
    orphaned = 0
    for lead in all_leads:
        if lead.get('assigned_broker_id') not in broker_ids:
            orphaned += 1
            print(f"  ⚠️  Lead {lead.get('id')} asignado a broker inexistente: {lead.get('assigned_broker_id')}")
    
    if orphaned == 0:
        print("  ✅ No hay leads huérfanos")
    else:
        print(f"  Total de leads huérfanos: {orphaned}")
    
    print("\n" + "=" * 80)
    print("DIAGNÓSTICO COMPLETO")
    print("=" * 80)
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(diagnose_broker_leads())
