#!/usr/bin/env python3
"""
Script para FORZAR la reasignación de leads al broker correcto
Ejecutar en PRODUCCIÓN
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def force_reassign():
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("=" * 80)
    print("FORZAR REASIGNACIÓN DE LEADS - PRODUCCIÓN")
    print("=" * 80)
    
    # 1. Obtener el broker por email
    broker_email = "amaseguros.gt@gmail.com"
    print(f"\n1. Buscando broker: {broker_email}")
    
    broker = await db.brokers.find_one({"email": broker_email})
    
    if not broker:
        print(f"❌ NO SE ENCONTRÓ EL BROKER")
        # Listar todos los brokers
        all_brokers = await db.brokers.find({}).to_list(length=None)
        print(f"\nBrokers disponibles:")
        for b in all_brokers:
            print(f"  - {b.get('email')}: {b.get('name')}")
        client.close()
        return
    
    broker_id = broker.get('id')
    broker_name = broker.get('name')
    
    print(f"✅ Broker encontrado:")
    print(f"   Nombre: {broker_name}")
    print(f"   Email: {broker.get('email')}")
    print(f"   Broker ID: {broker_id}")
    print(f"   User ID: {broker.get('user_id')}")
    
    # 2. Buscar TODOS los leads (asignados o no)
    print(f"\n2. Buscando TODOS los leads en la BD...")
    all_leads = await db.leads.find({}).to_list(length=None)
    print(f"   Total de leads en BD: {len(all_leads)}")
    
    # 3. Analizar leads
    leads_assigned_to_this_broker = []
    leads_assigned_to_others = []
    leads_unassigned = []
    
    for lead in all_leads:
        assigned_to = lead.get('assigned_broker_id')
        
        if not assigned_to:
            leads_unassigned.append(lead)
        elif assigned_to == broker_id:
            leads_assigned_to_this_broker.append(lead)
        else:
            leads_assigned_to_others.append(lead)
    
    print(f"\n3. Análisis de leads:")
    print(f"   Leads asignados a {broker_name}: {len(leads_assigned_to_this_broker)}")
    print(f"   Leads asignados a otros: {len(leads_assigned_to_others)}")
    print(f"   Leads sin asignar: {len(leads_unassigned)}")
    
    # 4. Mostrar leads asignados a otros brokers
    if leads_assigned_to_others:
        print(f"\n4. Leads asignados a OTROS brokers:")
        for lead in leads_assigned_to_others:
            assigned_to = lead.get('assigned_broker_id')
            print(f"\n   Lead ID: {lead.get('id')}")
            print(f"   Cliente: {lead.get('name', 'Sin nombre')}")
            print(f"   Teléfono: {lead.get('phone_number')}")
            print(f"   Asignado a broker_id: {assigned_to}")
            
            # Buscar el broker al que está asignado
            other_broker = await db.brokers.find_one({"id": assigned_to})
            if other_broker:
                print(f"   ✅ Broker existe: {other_broker.get('name')} ({other_broker.get('email')})")
            else:
                print(f"   ❌ Broker NO EXISTE (lead huérfano)")
    
    # 5. REASIGNAR leads huérfanos al broker correcto
    print(f"\n5. REASIGNANDO leads huérfanos a {broker_name}...")
    fixed_count = 0
    
    for lead in leads_assigned_to_others:
        assigned_to = lead.get('assigned_broker_id')
        other_broker = await db.brokers.find_one({"id": assigned_to})
        
        if not other_broker:
            # Lead huérfano - reasignar
            lead_id = lead.get('id')
            result = await db.leads.update_one(
                {"id": lead_id},
                {"$set": {"assigned_broker_id": broker_id}}
            )
            
            if result.modified_count > 0:
                print(f"   ✅ Lead {lead_id} reasignado a {broker_name}")
                fixed_count += 1
            else:
                print(f"   ⚠️ No se pudo reasignar lead {lead_id}")
    
    print(f"\n6. REASIGNANDO leads sin asignar a {broker_name}...")
    for lead in leads_unassigned[:5]:  # Solo los primeros 5
        lead_id = lead.get('id')
        result = await db.leads.update_one(
            {"id": lead_id},
            {"$set": {"assigned_broker_id": broker_id}}
        )
        
        if result.modified_count > 0:
            print(f"   ✅ Lead {lead_id} asignado a {broker_name}")
            fixed_count += 1
    
    # 7. Verificación final
    print(f"\n7. VERIFICACIÓN FINAL:")
    final_count = await db.leads.count_documents({"assigned_broker_id": broker_id})
    print(f"   Leads asignados a {broker_name}: {final_count}")
    
    if final_count > 0:
        sample_leads = await db.leads.find({"assigned_broker_id": broker_id}).limit(5).to_list(length=5)
        print(f"\n   Muestra de leads:")
        for lead in sample_leads:
            print(f"   - {lead.get('name', 'Sin nombre')} ({lead.get('phone_number')})")
    
    print(f"\n" + "=" * 80)
    print(f"RESUMEN:")
    print(f"  Broker: {broker_name} ({broker_email})")
    print(f"  Broker ID: {broker_id}")
    print(f"  Leads reasignados: {fixed_count}")
    print(f"  Leads totales asignados: {final_count}")
    print(f"=" * 80)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(force_reassign())
