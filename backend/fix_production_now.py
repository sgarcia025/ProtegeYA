#!/usr/bin/env python3
"""
Script de diagnóstico y reparación URGENTE para producción
Ejecutar en el servidor de producción
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def fix_production():
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("=" * 80)
    print("DIAGNÓSTICO Y REPARACIÓN URGENTE - PRODUCCIÓN")
    print("=" * 80)
    
    # 1. Listar TODOS los brokers
    print("\n1. BROKERS EN PRODUCCIÓN:")
    brokers = await db.brokers.find({}).to_list(length=None)
    print(f"   Total: {len(brokers)} broker(s)")
    
    for broker in brokers:
        print(f"\n   Broker:")
        print(f"     ID: {broker.get('id')}")
        print(f"     Nombre: {broker.get('name')}")
        print(f"     Email: {broker.get('email')}")
        print(f"     User ID: {broker.get('user_id')}")
        
        # Check auth_users
        user = await db.auth_users.find_one({"id": broker.get('user_id')})
        if user:
            print(f"     ✅ Usuario existe en auth_users")
            print(f"        Email: {user.get('email')}")
            print(f"        Role: {user.get('role')}")
        else:
            print(f"     ❌ Usuario NO existe en auth_users")
            print(f"     🔧 ESTE BROKER NECESITA SINCRONIZACIÓN")
    
    # 2. Contar leads asignados por broker
    print("\n\n2. LEADS ASIGNADOS POR BROKER:")
    for broker in brokers:
        broker_id = broker.get('id')
        query = {"assigned_broker_id": broker_id}
        count = await db.leads.count_documents(query)
        
        print(f"\n   Broker: {broker.get('name')} ({broker.get('email')})")
        print(f"   Broker ID: {broker_id}")
        print(f"   Query: {query}")
        print(f"   Leads asignados: {count}")
        
        if count > 0:
            leads = await db.leads.find(query).limit(5).to_list(length=5)
            for lead in leads:
                print(f"     - {lead.get('name', 'Sin nombre')} ({lead.get('phone_number')})")
    
    # 3. Verificar leads "huérfanos" (asignados a brokers inexistentes)
    print("\n\n3. VERIFICANDO LEADS HUÉRFANOS:")
    broker_ids = {b.get('id') for b in brokers}
    all_assigned = await db.leads.find({"assigned_broker_id": {"$ne": None}}).to_list(length=None)
    
    orphaned = []
    for lead in all_assigned:
        assigned_to = lead.get('assigned_broker_id')
        if assigned_to not in broker_ids:
            orphaned.append(lead)
    
    if orphaned:
        print(f"   ⚠️ {len(orphaned)} lead(s) asignado(s) a broker(s) inexistente(s):")
        for lead in orphaned:
            print(f"     - Lead {lead.get('id')}: asignado a '{lead.get('assigned_broker_id')}'")
            print(f"       Cliente: {lead.get('name', 'Sin nombre')}")
    else:
        print(f"   ✅ No hay leads huérfanos")
    
    # 4. Verificar leads sin asignar
    print("\n\n4. LEADS SIN ASIGNAR:")
    unassigned = await db.leads.find({
        "$or": [
            {"assigned_broker_id": None},
            {"assigned_broker_id": {"$exists": False}}
        ]
    }).to_list(length=None)
    
    print(f"   Total: {len(unassigned)} lead(s) sin asignar")
    if unassigned:
        for lead in unassigned[:5]:
            print(f"     - {lead.get('name', 'Sin nombre')} ({lead.get('phone_number')})")
    
    # 5. SOLUCIÓN: Si hay un broker pero no tiene leads asignados, revisar qué está pasando
    print("\n\n5. ANÁLISIS DE DISCREPANCIAS:")
    
    if len(brokers) == 0:
        print("   ❌ NO HAY BROKERS EN LA BASE DE DATOS")
        print("   → Solución: Crear broker desde el admin dashboard")
    
    elif len(all_assigned) == 0:
        print("   ❌ NO HAY LEADS ASIGNADOS A NINGÚN BROKER")
        print("   → Solución: Asignar leads desde el admin dashboard")
    
    else:
        # Verificar si los broker_ids en leads coinciden con los brokers existentes
        for broker in brokers:
            broker_id = broker.get('id')
            user_id = broker.get('user_id')
            
            # Contar leads
            leads_count = await db.leads.count_documents({"assigned_broker_id": broker_id})
            
            # Verificar usuario
            user = await db.auth_users.find_one({"id": user_id})
            
            print(f"\n   Broker: {broker.get('name')}")
            print(f"     Email: {broker.get('email')}")
            print(f"     Broker ID: {broker_id}")
            print(f"     User ID: {user_id}")
            print(f"     Usuario en auth_users: {'✅ Sí' if user else '❌ No'}")
            print(f"     Leads asignados: {leads_count}")
            
            if leads_count == 0:
                print(f"     ⚠️ PROBLEMA: No tiene leads asignados")
                print(f"     → Posibles causas:")
                print(f"        1. Los leads no están asignados a este broker en la BD")
                print(f"        2. El broker_id en leads es diferente al broker_id actual")
            elif not user:
                print(f"     ⚠️ PROBLEMA: No tiene usuario en auth_users")
                print(f"     → Solución: Ejecutar sync de brokers desde admin dashboard")
            else:
                print(f"     ✅ TODO CORRECTO")
    
    # 6. Mostrar comando para revisar en MongoDB directamente
    print("\n\n6. COMANDOS PARA VERIFICACIÓN MANUAL EN MONGODB:")
    print("   " + "=" * 76)
    for broker in brokers:
        print(f"\n   // Verificar leads del broker: {broker.get('name')}")
        print(f'   db.leads.find({{assigned_broker_id: "{broker.get("id")}"}}).count()')
        print(f'   db.leads.find({{assigned_broker_id: "{broker.get("id")}"}}).pretty()')
    
    print("\n" + "=" * 80)
    print("DIAGNÓSTICO COMPLETO")
    print("=" * 80)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(fix_production())
