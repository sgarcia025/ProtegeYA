from fastapi import FastAPI, APIRouter, HTTPException, Depends, BackgroundTasks, Form, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
from enum import Enum
import httpx
import json
import base64
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="ProtegeYa API", description="WhatsApp Insurance Lead Generator & Broker CRM")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# LLM Chat initialization
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

# Guatemala timezone offset (UTC-6)
GUATEMALA_TZ = timezone(timedelta(hours=-6))

# Enums
class LeadStatus(str, Enum):
    PENDING_DATA = "PendingData"
    QUOTED_NO_PREFERENCE = "QuotedNoPreference"  
    ASSIGNED_TO_BROKER = "AssignedToBroker"

class BrokerLeadStatus(str, Enum):
    CONTACTED = "Contacted"
    INTERESTED = "Interested"
    NEGOTIATION = "Negotiation"
    NOT_INTERESTED = "NotInterested"
    CLOSED_WON = "ClosedWon"
    CLOSED_LOST = "ClosedLost"

class BrokerSubscriptionStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    PAST_DUE = "PastDue"
    CANCELED = "Canceled"

class InsuranceType(str, Enum):
    FULL_COVERAGE = "FullCoverage"  # Seguro completo
    THIRD_PARTY = "ThirdParty"      # Responsabilidad civil (RC)

# Models
class UserProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    phone_number: str
    name: Optional[str] = None
    email: Optional[str] = None
    municipality: Optional[str] = None
    consent_wa: bool = True
    opt_out_wa: bool = False
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(GUATEMALA_TZ))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(GUATEMALA_TZ))

class Vehicle(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    make: str  # Marca
    model: str # Modelo
    year: int  # Año
    value: float # Valor en GTQ
    created_at: datetime = Field(default_factory=lambda: datetime.now(GUATEMALA_TZ))

class Insurer(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    logo_url: Optional[str] = None
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(GUATEMALA_TZ))

class TariffSection(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_version_id: str
    name: str
    percentage_of_sum_insured: float  # Porcentaje del valor del vehículo
    created_at: datetime = Field(default_factory=lambda: datetime.now(GUATEMALA_TZ))

class FixedBenefit(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_version_id: str
    name: str
    amount: float  # Cantidad fija en GTQ
    created_at: datetime = Field(default_factory=lambda: datetime.now(GUATEMALA_TZ))

class ProductVersion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_id: str
    version_name: str
    base_premium_percentage: float  # Porcentaje base del valor del vehículo para prima
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(GUATEMALA_TZ))

class Product(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    insurer_id: str
    name: str
    insurance_type: InsuranceType
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(GUATEMALA_TZ))

class Lead(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    vehicle_id: Optional[str] = None
    status: LeadStatus = LeadStatus.PENDING_DATA
    assigned_broker_id: Optional[str] = None
    sla_first_contact_deadline: Optional[datetime] = None
    sla_reassignment_deadline: Optional[datetime] = None
    quotes: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(GUATEMALA_TZ))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(GUATEMALA_TZ))

class BrokerProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    phone_number: str
    whatsapp_number: str
    subscription_status: BrokerSubscriptionStatus = BrokerSubscriptionStatus.INACTIVE
    monthly_lead_quota: int = 50
    current_month_leads: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(GUATEMALA_TZ))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(GUATEMALA_TZ))

class BrokerLeadStatusUpdate(BaseModel):
    lead_id: str
    broker_id: str
    status: BrokerLeadStatus
    notes: Optional[str] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(GUATEMALA_TZ))

class LeadInteraction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    lead_id: str
    interaction_type: str  # "whatsapp_message", "voice_note", "status_update"
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(GUATEMALA_TZ))

# Request/Response Models
class QuoteRequest(BaseModel):
    make: str
    model: str
    year: int
    value: float
    municipality: Optional[str] = None

class QuoteResponse(BaseModel):
    quotes: List[Dict[str, Any]]
    disclaimer: str

class WhatsAppWebhook(BaseModel):
    instance_id: str
    data: Dict[str, Any]

class WhatsAppMessage(BaseModel):
    phone_number: str
    message: str

# Helper Functions
def prepare_for_mongo(data):
    """Prepare data for MongoDB storage"""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
    return data

def parse_from_mongo(item):
    """Parse data from MongoDB"""
    if isinstance(item, dict):
        for key, value in item.items():
            if isinstance(value, str) and 'T' in value and 'Z' in value or '+' in value:
                try:
                    item[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except:
                    pass
    return item

async def get_or_create_user(phone_number: str) -> UserProfile:
    """Get existing user or create new one"""
    user_doc = await db.users.find_one({"phone_number": phone_number})
    if user_doc:
        user_doc = parse_from_mongo(user_doc)
        return UserProfile(**user_doc)
    
    # Create new user
    new_user = UserProfile(phone_number=phone_number)
    user_dict = prepare_for_mongo(new_user.dict())
    await db.users.insert_one(user_dict)
    return new_user

async def calculate_quotes(vehicle_data: QuoteRequest) -> List[Dict[str, Any]]:
    """Calculate indicative insurance quotes"""
    # Get active insurers and products
    insurers = await db.insurers.find({"active": True}).to_list(length=None)
    quotes = []
    
    for insurer in insurers:
        products = await db.products.find({
            "insurer_id": insurer["id"], 
            "active": True
        }).to_list(length=None)
        
        for product in products:
            # Get latest active version
            version = await db.product_versions.find_one({
                "product_id": product["id"],
                "active": True
            })
            
            if version:
                # Calculate premium
                base_premium = vehicle_data.value * (version["base_premium_percentage"] / 100)
                
                # Get tariff sections and benefits
                tariff_sections = await db.tariff_sections.find({
                    "product_version_id": version["id"]
                }).to_list(length=None)
                
                benefits = await db.fixed_benefits.find({
                    "product_version_id": version["id"] 
                }).to_list(length=None)
                
                coverage = {}
                for section in tariff_sections:
                    coverage[section["name"]] = f"Q{vehicle_data.value * (section['percentage_of_sum_insured'] / 100):,.2f}"
                
                for benefit in benefits:
                    coverage[benefit["name"]] = f"Q{benefit['amount']:,.2f}"
                
                quote = {
                    "insurer_name": insurer["name"],
                    "product_name": product["name"],
                    "insurance_type": product["insurance_type"],
                    "monthly_premium": round(base_premium, 2),
                    "coverage": coverage,
                    "version_id": version["id"]
                }
                quotes.append(quote)
    
    return quotes[:4]  # Return max 4 quotes

async def assign_broker_to_lead(lead_id: str) -> Optional[str]:
    """Assign lead to available broker using round-robin"""
    # Get active brokers with available quota
    brokers = await db.brokers.find({
        "subscription_status": BrokerSubscriptionStatus.ACTIVE,
        "$expr": {"$lt": ["$current_month_leads", "$monthly_lead_quota"]}
    }).to_list(length=None)
    
    if not brokers:
        return None
    
    # Simple round-robin: broker with least current leads
    chosen_broker = min(brokers, key=lambda x: x["current_month_leads"])
    
    # Update lead with assigned broker
    await db.leads.update_one(
        {"id": lead_id},
        {
            "$set": {
                "assigned_broker_id": chosen_broker["id"],
                "status": LeadStatus.ASSIGNED_TO_BROKER,
                "sla_first_contact_deadline": datetime.now(GUATEMALA_TZ) + timedelta(hours=2),
                "sla_reassignment_deadline": datetime.now(GUATEMALA_TZ) + timedelta(hours=4),
                "updated_at": datetime.now(GUATEMALA_TZ)
            }
        }
    )
    
    # Update broker lead count
    await db.brokers.update_one(
        {"id": chosen_broker["id"]},
        {"$inc": {"current_month_leads": 1}}
    )
    
    return chosen_broker["id"]

async def process_whatsapp_message(phone_number: str, message: str) -> str:
    """Process incoming WhatsApp message using AI"""
    try:
        user = await get_or_create_user(phone_number)
        
        # Get user's current lead if exists
        current_lead = await db.leads.find_one({
            "user_id": user.id,
            "status": {"$in": [LeadStatus.PENDING_DATA, LeadStatus.QUOTED_NO_PREFERENCE]}
        })
        
        # Initialize AI chat
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"protegeya_{user.id}",
            system_message="""Eres un asistente de ProtegeYa, un comparador de seguros para vehículos en Guatemala.

IMPORTANTE: ProtegeYa es un comparador y generador de leads. No es aseguradora ni corredor. Los precios son indicativos y deben confirmarse con un corredor autorizado.

Tu trabajo es:
1. Recopilar datos del vehículo: marca, modelo, año, valor en GTQ, municipio
2. Obtener datos personales: nombre, teléfono
3. Ayudar con el proceso de cotización
4. Ser amable y profesional en español guatemalteco

Menú principal:
1. Cotizar seguro
2. Ver mi cotización
3. Renovar/Mejorar
4. Ayuda

Responde siempre en español de Guatemala y sé conciso."""
        ).with_model("openai", "gpt-4o")
        
        # Add context about current lead
        context = f"Usuario actual: {user.phone_number}"
        if current_lead:
            context += f"\nLead actual: {current_lead.get('status', 'sin estado')}"
        
        user_message = UserMessage(text=f"Contexto: {context}\n\nMensaje del usuario: {message}")
        
        response = await chat.send_message(user_message)
        
        # Log interaction
        interaction = LeadInteraction(
            lead_id=current_lead["id"] if current_lead else "none",
            interaction_type="whatsapp_message",
            content=message,
            metadata={"response": response}
        )
        await db.interactions.insert_one(prepare_for_mongo(interaction.dict()))
        
        return response
        
    except Exception as e:
        logging.error(f"Error processing WhatsApp message: {e}")
        return "Disculpa, hubo un error. Por favor intenta de nuevo o escribe 'ayuda'."

# API Routes

@api_router.get("/")
async def root():
    return {"message": "ProtegeYa API - Insurance Lead Generator", "status": "active"}

# WhatsApp Routes
@api_router.post("/whatsapp/webhook")
async def whatsapp_webhook(webhook_data: WhatsAppWebhook, background_tasks: BackgroundTasks):
    """Handle incoming WhatsApp webhook from UltraMSG"""
    try:
        data = webhook_data.data
        
        if data.get("type") == "message":
            phone_number = data.get("from", "").replace("@c.us", "")
            message_text = data.get("body", "")
            
            if message_text and phone_number:
                # Process message in background
                background_tasks.add_task(
                    handle_whatsapp_message_async, 
                    phone_number, 
                    message_text
                )
        
        return {"status": "received"}
    except Exception as e:
        logging.error(f"WhatsApp webhook error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

async def handle_whatsapp_message_async(phone_number: str, message: str):
    """Async handler for WhatsApp messages"""
    try:
        response = await process_whatsapp_message(phone_number, message)
        
        # Send response via UltraMSG (mock for now)
        await send_whatsapp_message(phone_number, response)
        
    except Exception as e:
        logging.error(f"Error handling WhatsApp message async: {e}")

async def send_whatsapp_message(phone_number: str, message: str) -> bool:
    """Send WhatsApp message via UltraMSG (mock implementation)"""
    try:
        # Mock implementation - replace with real UltraMSG API call
        logging.info(f"MOCK WhatsApp send to {phone_number}: {message}")
        
        # Real implementation would be:
        # ultramsg_url = "https://api.ultramsg.com/{instance_id}/messages/chat"
        # headers = {"Content-Type": "application/json"}
        # payload = {
        #     "token": os.environ.get("ULTRAMSG_TOKEN"),
        #     "to": phone_number,
        #     "body": message
        # }
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(ultramsg_url, json=payload, headers=headers)
        #     return response.status_code == 200
        
        return True
    except Exception as e:
        logging.error(f"Error sending WhatsApp message: {e}")
        return False

@api_router.post("/whatsapp/send")
async def send_whatsapp(message_data: WhatsAppMessage):
    """Manually send WhatsApp message"""
    success = await send_whatsapp_message(message_data.phone_number, message_data.message)
    return {"success": success}

# Quote Routes
@api_router.post("/quotes/simulate", response_model=QuoteResponse)
async def simulate_quotes(quote_request: QuoteRequest):
    """Generate indicative insurance quotes"""
    quotes = await calculate_quotes(quote_request)
    
    disclaimer = (
        "ProtegeYa es un comparador y generador de leads. No es aseguradora ni corredor. "
        "Precios indicativos a confirmar con un corredor autorizado."
    )
    
    return QuoteResponse(quotes=quotes, disclaimer=disclaimer)

# Admin Routes - Insurers
@api_router.post("/admin/insurers", response_model=Insurer)
async def create_insurer(insurer: Insurer):
    """Create new insurer"""
    insurer_dict = prepare_for_mongo(insurer.dict())
    await db.insurers.insert_one(insurer_dict)
    return insurer

@api_router.get("/admin/insurers", response_model=List[Insurer])
async def get_insurers():
    """Get all insurers"""
    insurers = await db.insurers.find().to_list(length=None)
    return [Insurer(**parse_from_mongo(insurer)) for insurer in insurers]

@api_router.put("/admin/insurers/{insurer_id}")
async def update_insurer(insurer_id: str, insurer_data: Dict[str, Any]):
    """Update insurer"""
    insurer_data["updated_at"] = datetime.now(GUATEMALA_TZ)
    insurer_dict = prepare_for_mongo(insurer_data)
    
    result = await db.insurers.update_one(
        {"id": insurer_id}, 
        {"$set": insurer_dict}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Insurer not found")
    return {"success": True}

# Admin Routes - Products
@api_router.post("/admin/products", response_model=Product)
async def create_product(product: Product):
    """Create new insurance product"""
    product_dict = prepare_for_mongo(product.dict())
    await db.products.insert_one(product_dict)
    return product

@api_router.get("/admin/products", response_model=List[Product])
async def get_products():
    """Get all products"""
    products = await db.products.find().to_list(length=None)
    return [Product(**parse_from_mongo(product)) for product in products]

# Admin Routes - Product Versions
@api_router.post("/admin/product-versions", response_model=ProductVersion)
async def create_product_version(version: ProductVersion):
    """Create new product version"""
    version_dict = prepare_for_mongo(version.dict())
    await db.product_versions.insert_one(version_dict)
    return version

@api_router.get("/admin/product-versions/{product_id}")
async def get_product_versions(product_id: str):
    """Get versions for a product"""
    versions = await db.product_versions.find({"product_id": product_id}).to_list(length=None)
    return [ProductVersion(**parse_from_mongo(version)) for version in versions]

# Admin Routes - Tariff Sections
@api_router.post("/admin/tariff-sections", response_model=TariffSection)
async def create_tariff_section(section: TariffSection):
    """Create tariff section"""
    section_dict = prepare_for_mongo(section.dict())
    await db.tariff_sections.insert_one(section_dict)
    return section

# Admin Routes - Fixed Benefits
@api_router.post("/admin/fixed-benefits", response_model=FixedBenefit)
async def create_fixed_benefit(benefit: FixedBenefit):
    """Create fixed benefit"""
    benefit_dict = prepare_for_mongo(benefit.dict())
    await db.fixed_benefits.insert_one(benefit_dict)
    return benefit

# Lead Management Routes
@api_router.get("/leads")
async def get_leads(broker_id: Optional[str] = None, limit: int = 50):
    """Get leads (optionally filtered by broker)"""
    query = {}
    if broker_id:
        query["assigned_broker_id"] = broker_id
    
    leads = await db.leads.find(query).limit(limit).to_list(length=None)
    return [Lead(**parse_from_mongo(lead)) for lead in leads]

@api_router.post("/leads/{lead_id}/status")
async def update_broker_lead_status(lead_id: str, status_update: BrokerLeadStatusUpdate):
    """Update broker lead status"""
    status_dict = prepare_for_mongo(status_update.dict())
    await db.broker_lead_status.insert_one(status_dict)
    return {"success": True}

# Broker Routes
@api_router.get("/brokers")
async def get_brokers():
    """Get all brokers"""
    brokers = await db.brokers.find().to_list(length=None)
    return [BrokerProfile(**parse_from_mongo(broker)) for broker in brokers]

@api_router.post("/brokers", response_model=BrokerProfile)
async def create_broker(broker: BrokerProfile):
    """Create new broker"""
    broker_dict = prepare_for_mongo(broker.dict())
    await db.brokers.insert_one(broker_dict)
    return broker

@api_router.put("/brokers/{broker_id}/subscription")
async def update_broker_subscription(broker_id: str, status: BrokerSubscriptionStatus):
    """Update broker subscription status"""
    result = await db.brokers.update_one(
        {"id": broker_id},
        {"$set": {"subscription_status": status, "updated_at": datetime.now(GUATEMALA_TZ)}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Broker not found")
    return {"success": True}

# Reports and Analytics
@api_router.get("/reports/kpi")
async def get_kpi_report():
    """Get KPI dashboard data"""
    # Lead funnel
    total_leads = await db.leads.count_documents({})
    assigned_leads = await db.leads.count_documents({"status": LeadStatus.ASSIGNED_TO_BROKER})
    
    # Broker performance
    active_brokers = await db.brokers.count_documents({"subscription_status": BrokerSubscriptionStatus.ACTIVE})
    
    # SLA compliance (mock calculation)
    sla_compliance = 85.5  # Would calculate from actual SLA events
    
    return {
        "total_leads": total_leads,
        "assigned_leads": assigned_leads,
        "active_brokers": active_brokers,
        "assignment_rate": round((assigned_leads / max(total_leads, 1)) * 100, 1),
        "sla_compliance": sla_compliance,
        "generated_at": datetime.now(GUATEMALA_TZ).isoformat()
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()