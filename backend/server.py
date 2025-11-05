from fastapi import FastAPI, APIRouter, HTTPException, Depends, BackgroundTasks, Form, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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
import jwt
from passlib.context import CryptContext
from emergentintegrations.llm.chat import LlmChat, UserMessage
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
import tempfile

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

# JWT Configuration
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'protegeya-secret-key-2025')
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_HOURS = 24

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# LLM Chat initialization
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

# Guatemala timezone offset (UTC-6)
GUATEMALA_TZ = timezone(timedelta(hours=-6))

# Enums
class UserRole(str, Enum):
    ADMIN = "admin"
    BROKER = "broker"

class LeadStatus(str, Enum):
    PENDING_DATA = "PendingData"
    QUOTED_NO_PREFERENCE = "QuotedNoPreference"  
    ASSIGNED_TO_BROKER = "AssignedToBroker"

class BrokerLeadStatus(str, Enum):
    NEW = "New"
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

class PaymentStatus(str, Enum):
    PAID = "Paid"
    PENDING = "Pending"
    OVERDUE = "Overdue"

# Auth Models
class UserCreate(BaseModel):
    email: str
    password: str
    role: UserRole
    name: str

class BrokerCreate(BaseModel):
    email: str
    password: str
    name: str
    phone_number: str
    whatsapp_number: str
    corretaje_name: str = ""
    broker_credential: str = ""
    subscription_status: BrokerSubscriptionStatus = BrokerSubscriptionStatus.INACTIVE
    monthly_lead_quota: int = 50
    commission_percentage: float = 10.0

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: UserRole
    created_at: datetime
    active: bool = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# Core Models
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
    broker_status: BrokerLeadStatus = BrokerLeadStatus.NEW
    assigned_broker_id: Optional[str] = None
    sla_first_contact_deadline: Optional[datetime] = None
    sla_reassignment_deadline: Optional[datetime] = None
    quotes: List[Dict[str, Any]] = Field(default_factory=list)
    broker_notes: Optional[str] = None
    closed_amount: Optional[float] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(GUATEMALA_TZ))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(GUATEMALA_TZ))

class BrokerProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str  # Reference to auth user
    name: str
    email: str
    phone_number: str
    whatsapp_number: str
    corretaje_name: str = ""  # Nombre del corretaje
    broker_credential: str = ""  # Número de credencial de corredor autorizado
    profile_photo_url: Optional[str] = None  # URL de la foto de perfil
    subscription_status: BrokerSubscriptionStatus = BrokerSubscriptionStatus.INACTIVE
    subscription_plan_id: Optional[str] = None
    monthly_lead_quota: int = 50
    current_month_leads: int = 0
    commission_percentage: float = 10.0
    total_closed_deals: int = 0
    total_revenue: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(GUATEMALA_TZ))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(GUATEMALA_TZ))

class SubscriptionPlan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    amount: float
    currency: str = "GTQ"
    period: str = "monthly"  # monthly, quarterly, semiannual, annual
    benefits: List[str] = Field(default_factory=list)
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(GUATEMALA_TZ))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(GUATEMALA_TZ))

class Lead(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str = ""
    phone_number: str = ""
    vehicle_make: str = ""
    vehicle_model: str = ""
    vehicle_year: Optional[int] = None
    vehicle_value: Optional[float] = None
    municipality: str = "Guatemala"
    selected_insurer: str = ""
    selected_quote_price: Optional[float] = None
    selected_insurance_type: Optional[str] = None  # "FullCoverage" or "ThirdParty"
    quote_details: Dict[str, Any] = Field(default_factory=dict)
    quotations: List[Dict[str, Any]] = Field(default_factory=list)  # NUEVO: Historial de cotizaciones
    status: LeadStatus = LeadStatus.PENDING_DATA
    broker_status: BrokerLeadStatus = BrokerLeadStatus.NEW
    assigned_broker_id: Optional[str] = None
    sla_first_contact_deadline: Optional[datetime] = None
    sla_reassignment_deadline: Optional[datetime] = None
    quotes: List[Dict[str, Any]] = Field(default_factory=list)
    broker_notes: Optional[str] = None
    closed_amount: Optional[float] = None
    quote_generated: bool = False
    pdf_sent: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(GUATEMALA_TZ))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(GUATEMALA_TZ))

class InsuranceRateConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    insurer_id: str
    insurance_type: str  # auto, medical, etc
    coverage_type: InsuranceType  # FullCoverage, ThirdParty
    own_damage_rate: float = 0.0  # Tasa daños propios (%)
    civil_liability_amount: float = 0.0  # Monto RC fijo
    other_damages_rate: float = 0.0  # Tasa otros daños (%)
    other_benefits_amount: float = 0.0  # Monto otros beneficios
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(GUATEMALA_TZ))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(GUATEMALA_TZ))

class BrokerPayment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    broker_id: str
    amount: float
    month: int
    year: int
    status: PaymentStatus = PaymentStatus.PENDING
    due_date: datetime
    paid_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(GUATEMALA_TZ))

class SystemConfiguration(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ultramsg_instance_id: Optional[str] = None
    ultramsg_token: Optional[str] = None
    ultramsg_webhook_secret: Optional[str] = None
    openai_api_key: Optional[str] = None
    use_emergent_llm: bool = True
    whatsapp_enabled: bool = False
    ai_chat_prompt: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(GUATEMALA_TZ))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(GUATEMALA_TZ))

class AccountStatus(str, Enum):
    ACTIVE = "Active"          # Al día
    OVERDUE = "Overdue"        # Vencido
    GRACE_PERIOD = "GracePeriod"  # En período de gracia
    SUSPENDED = "Suspended"    # Suspendido por falta de pago

# Aseguradoras Models
class TasaRango(BaseModel):
    desde: float  # Desde (Q)
    hasta: float  # Hasta (Q)
    tasa: float   # Tasa (%)

class Aseguradora(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nombre: str
    iva: float = 0.12  # % IVA
    cuotas: int = 12   # Número de cuotas
    completo_gastos_emision: float = 0.0  # Gastos de emisión (Seguro Completo)
    completo_asistencia: float = 0.0      # Asistencia (Seguro Completo)
    completo_prima_minima: float = 0.0    # Prima mínima para Seguro Completo
    rc_gastos_emision: float = 0.0        # Gastos de emisión (Seguro RC)
    rc_asistencia: float = 0.0            # Asistencia (Seguro RC)
    completo_tasas: List[TasaRango] = Field(default_factory=list)  # Tasas por rango - Seguro Completo
    rc_prima_neta: float = 0.0            # Prima neta fija para Seguro RC
    completo_año_desde: int = 2000        # Año mínimo asegurable para Completo
    completo_año_hasta: int = 2025        # Año máximo asegurable para Completo
    rc_año_desde: int = 2000              # Año mínimo asegurable para RC
    rc_año_hasta: int = 2025              # Año máximo asegurable para RC
    activo: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(GUATEMALA_TZ))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(GUATEMALA_TZ))

class AseguradoraCreate(BaseModel):
    nombre: str
    iva: float = 0.12
    cuotas: int = 12
    completo_gastos_emision: float = 0.0
    completo_asistencia: float = 0.0
    completo_prima_minima: float = 0.0
    rc_gastos_emision: float = 0.0
    rc_asistencia: float = 0.0
    completo_tasas: List[TasaRango] = Field(default_factory=list)
    rc_prima_neta: float = 0.0
    completo_año_desde: int = 2000
    completo_año_hasta: int = 2025
    rc_año_desde: int = 2000
    rc_año_hasta: int = 2025
    activo: bool = True

class AseguradoraUpdate(BaseModel):
    nombre: Optional[str] = None
    iva: Optional[float] = None
    cuotas: Optional[int] = None
    completo_gastos_emision: Optional[float] = None
    completo_asistencia: Optional[float] = None
    completo_prima_minima: Optional[float] = None
    rc_gastos_emision: Optional[float] = None
    rc_asistencia: Optional[float] = None
    completo_tasas: Optional[List[TasaRango]] = None
    rc_prima_neta: Optional[float] = None
    completo_año_desde: Optional[int] = None
    completo_año_hasta: Optional[int] = None
    rc_año_desde: Optional[int] = None
    rc_año_hasta: Optional[int] = None
    activo: Optional[bool] = None

class CotizacionResult(BaseModel):
    aseguradora: str
    aseguradora_id: str
    cuota_rc: float
    cuota_completo: float

class VehiculoNoAsegurable(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    marca: str  # Marca del vehículo
    modelo: str  # Modelo del vehículo
    año: Optional[int] = None  # Año específico (opcional, None = todos los años)
    razon: str = ""  # Razón por la cual no es asegurable
    created_at: datetime = Field(default_factory=lambda: datetime.now(GUATEMALA_TZ))

class VehiculoNoAsegurableCreate(BaseModel):
    marca: str
    modelo: str
    año: Optional[int] = None
    razon: str = ""

class TransactionType(str, Enum):
    CHARGE = "Charge"          # Cargo mensual
    PAYMENT = "Payment"        # Pago aplicado
    ADJUSTMENT = "Adjustment"  # Ajuste manual

class BrokerAccount(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    broker_id: str
    account_number: str  # ID único por corredor (ej: ACC-001, ACC-002)
    current_balance: float = 0.0  # Balance actual (negativo = debe, positivo = a favor)
    subscription_start_date: datetime
    last_charge_date: Optional[datetime] = None
    next_due_date: datetime  # Próxima fecha de vencimiento
    grace_period_end: Optional[datetime] = None  # Fecha fin del período de gracia
    account_status: AccountStatus = AccountStatus.ACTIVE
    created_at: datetime = Field(default_factory=lambda: datetime.now(GUATEMALA_TZ))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(GUATEMALA_TZ))

class BrokerTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    account_id: str  # Referencia a BrokerAccount
    broker_id: str
    transaction_type: TransactionType
    amount: float  # Positivo para pagos, negativo para cargos
    description: str
    reference_number: Optional[str] = None  # Número de referencia del pago
    balance_after: float  # Balance después de esta transacción
    due_date: Optional[datetime] = None  # Para cargos, fecha de vencimiento
    created_by: Optional[str] = None  # Usuario que aplicó el movimiento
    created_at: datetime = Field(default_factory=lambda: datetime.now(GUATEMALA_TZ))

class BrokerLeadStatusUpdate(BaseModel):
    lead_id: str
    broker_status: BrokerLeadStatus
    notes: Optional[str] = None
    closed_amount: Optional[float] = None

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

class ConfigurationUpdate(BaseModel):
    ultramsg_instance_id: Optional[str] = None
    ultramsg_token: Optional[str] = None
    ultramsg_webhook_secret: Optional[str] = None
    openai_api_key: Optional[str] = None
    use_emergent_llm: Optional[bool] = None
    whatsapp_enabled: Optional[bool] = None
    ai_chat_prompt: Optional[str] = None

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
            if isinstance(value, str) and ('T' in value and ('Z' in value or '+' in value)):
                try:
                    item[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except:
                    pass
            # Skip MongoDB ObjectId fields
            elif key == '_id':
                continue
    return item

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=JWT_ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = await db.auth_users.find_one({"id": user_id})
    if user is None:
        raise credentials_exception
    
    user = parse_from_mongo(user)
    return UserResponse(**user)

async def require_admin(current_user: UserResponse = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

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
    """
    Calculate indicative insurance quotes using configured aseguradoras
    This is the CORE function for WhatsApp automatic quotation
    """
    # Verificar si el vehículo es asegurable
    vehiculo_check = await db.vehiculos_no_asegurables.find_one({
        "marca": {"$regex": f"^{vehicle_data.make}$", "$options": "i"},
        "modelo": {"$regex": f"^{vehicle_data.model}$", "$options": "i"},
        "$or": [
            {"año": vehicle_data.year},
            {"año": None}
        ]
    })
    
    if vehiculo_check:
        # Vehículo no asegurable
        logging.warning(f"Vehicle not insurable: {vehicle_data.make} {vehicle_data.model} {vehicle_data.year}")
        return []
    
    # Obtener aseguradoras activas
    aseguradoras = await db.aseguradoras.find({"activo": True}).to_list(length=None)
    
    if not aseguradoras:
        logging.warning("No active aseguradoras found")
        return []
    
    quotes = []
    
    for aseg_data in aseguradoras:
        aseguradora = Aseguradora(**parse_from_mongo(aseg_data))
        
        # Calcular cuota RC si el año está en el rango
        if aseguradora.rc_año_desde <= vehicle_data.year <= aseguradora.rc_año_hasta:
            cuota_rc = calcular_cuota_rc_fija(
                prima_neta=aseguradora.rc_prima_neta,
                gastos_emision=aseguradora.rc_gastos_emision,
                asistencia=aseguradora.rc_asistencia,
                iva=aseguradora.iva,
                cuotas=aseguradora.cuotas
            )
            
            if cuota_rc > 0:
                quotes.append({
                    "insurer_name": aseguradora.nombre,
                    "aseguradora_id": aseguradora.id,
                    "product_name": "Seguro RC",
                    "insurance_type": "ThirdParty",
                    "monthly_premium": round(cuota_rc, 2),
                    "coverage": {
                        "Responsabilidad Civil": "Incluida",
                        "Gastos de Emisión": f"Q{aseguradora.rc_gastos_emision:,.2f}",
                        "Asistencia": f"Q{aseguradora.rc_asistencia:,.2f}"
                    }
                })
        
        # Calcular cuota Completo si el año está en el rango
        if aseguradora.completo_año_desde <= vehicle_data.year <= aseguradora.completo_año_hasta:
            cuota_completo = calcular_cuota_seguro(
                suma_asegurada=vehicle_data.value,
                tasas=aseguradora.completo_tasas,
                gastos_emision=aseguradora.completo_gastos_emision,
                asistencia=aseguradora.completo_asistencia,
                iva=aseguradora.iva,
                cuotas=aseguradora.cuotas,
                prima_minima=aseguradora.completo_prima_minima
            )
            
            logging.info(f"Cotización Completo - {aseguradora.nombre}: año={vehicle_data.year}, rango={aseguradora.completo_año_desde}-{aseguradora.completo_año_hasta}, cuota={cuota_completo}, tasas={len(aseguradora.completo_tasas)}")
            
            if cuota_completo > 0:
                quotes.append({
                    "insurer_name": aseguradora.nombre,
                    "aseguradora_id": aseguradora.id,
                    "product_name": "Seguro Completo",
                    "insurance_type": "FullCoverage",
                    "monthly_premium": round(cuota_completo, 2),
                    "coverage": {
                        "Suma Asegurada": f"Q{vehicle_data.value:,.2f}",
                        "Gastos de Emisión": f"Q{aseguradora.completo_gastos_emision:,.2f}",
                        "Asistencia": f"Q{aseguradora.completo_asistencia:,.2f}"
                    }
                })
        else:
            logging.info(f"Cotización Completo RECHAZADA - {aseguradora.nombre}: año={vehicle_data.year} fuera de rango {aseguradora.completo_año_desde}-{aseguradora.completo_año_hasta}")
    
    # Ordenar por precio (menor a mayor)
    quotes.sort(key=lambda x: x["monthly_premium"])
    
    return quotes[:10]  # Return max 10 quotes (5 aseguradoras × 2 tipos)

def calcular_cuota_seguro(suma_asegurada: float, tasas: List[TasaRango], gastos_emision: float, asistencia: float, iva: float, cuotas: int, prima_minima: float = 0.0) -> float:
    """
    Calcula la cuota mensual de seguro basada en las tasas por rango (para Seguro Completo)
    Si la prima calculada es menor a la prima mínima, usa la prima mínima
    """
    # Encontrar la tasa aplicable según el rango de suma asegurada
    tasa_aplicable = 0.0
    
    for tasa_rango in tasas:
        if tasa_rango.desde <= suma_asegurada <= tasa_rango.hasta:
            tasa_aplicable = tasa_rango.tasa
            break
    
    # Si no se encuentra en ningún rango, usar la tasa del último rango
    if tasa_aplicable == 0.0 and tasas:
        tasa_aplicable = tasas[-1].tasa
    
    # Calcular prima base
    prima_base = suma_asegurada * (tasa_aplicable / 100)
    
    # Aplicar prima mínima si corresponde
    if prima_minima > 0 and prima_base < prima_minima:
        prima_base = prima_minima
    
    # Agregar gastos de emisión y asistencia
    prima_total = prima_base + gastos_emision + asistencia
    
    # Aplicar IVA
    prima_con_iva = prima_total * (1 + iva)
    
    # Dividir entre número de cuotas para obtener cuota mensual
    cuota_mensual = prima_con_iva / cuotas
    
    return cuota_mensual

def calcular_cuota_rc_fija(prima_neta: float, gastos_emision: float, asistencia: float, iva: float, cuotas: int) -> float:
    """
    Calcula la cuota mensual de seguro RC basada en prima neta fija
    """
    # Prima total = prima neta fija + gastos + asistencia
    prima_total = prima_neta + gastos_emision + asistencia
    
    # Aplicar IVA
    prima_con_iva = prima_total * (1 + iva)
    
    # Dividir entre número de cuotas para obtener cuota mensual
    cuota_mensual = prima_con_iva / cuotas
    
    return cuota_mensual
    
    # Dividir entre número de cuotas para obtener cuota mensual
    cuota_mensual = prima_con_iva / cuotas
    
    return cuota_mensual

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
    
    # Get lead details for notification
    lead = await db.leads.find_one({"id": lead_id})
    
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
    
    # Send WhatsApp notification to broker
    await send_broker_lead_notification(chosen_broker, lead)
    
    return chosen_broker["id"]

async def generate_account_number() -> str:
    """Generate unique account number for broker"""
    # Get the last account number
    last_account = await db.broker_accounts.find().sort([("account_number", -1)]).limit(1).to_list(1)
    
    if last_account:
        last_num = int(last_account[0]["account_number"].split("-")[1])
        new_num = last_num + 1
    else:
        new_num = 1
    
    return f"ACC-{new_num:03d}"

async def create_broker_account(broker_id: str, subscription_plan_id: str) -> str:
    """Create broker account when they subscribe to a plan"""
    # Get subscription plan
    plan = await db.subscription_plans.find_one({"id": subscription_plan_id})
    if not plan:
        raise HTTPException(status_code=404, detail="Subscription plan not found")
    
    # Generate unique account number
    account_number = await generate_account_number()
    
    # Calculate next due date
    now = datetime.now(GUATEMALA_TZ)
    if now.day >= 25:  # If subscription is between 25-31, next charge is 1st of next month
        if now.month == 12:
            next_due = datetime(now.year + 1, 1, 1, tzinfo=GUATEMALA_TZ)
        else:
            next_due = datetime(now.year, now.month + 1, 1, tzinfo=GUATEMALA_TZ)
    else:
        # Next charge is 1st of current month (if before 25th)
        next_due = datetime(now.year, now.month, 1, tzinfo=GUATEMALA_TZ)
        if next_due <= now:  # If 1st has passed, next month
            if now.month == 12:
                next_due = datetime(now.year + 1, 1, 1, tzinfo=GUATEMALA_TZ)
            else:
                next_due = datetime(now.year, now.month + 1, 1, tzinfo=GUATEMALA_TZ)
    
    # Create account
    account = BrokerAccount(
        broker_id=broker_id,
        account_number=account_number,
        subscription_start_date=now,
        next_due_date=next_due,
        current_balance=-plan["amount"]  # Initial charge
    )
    
    account_dict = prepare_for_mongo(account.dict())
    await db.broker_accounts.insert_one(account_dict)
    
    # Create initial charge transaction
    transaction = BrokerTransaction(
        account_id=account.id,
        broker_id=broker_id,
        transaction_type=TransactionType.CHARGE,
        amount=-plan["amount"],
        description=f"Suscripción inicial - {plan['name']}",
        balance_after=-plan["amount"],
        due_date=now  # Initial payment is due immediately
    )
    
    transaction_dict = prepare_for_mongo(transaction.dict())
    await db.broker_transactions.insert_one(transaction_dict)
    
    return account.id

async def generate_monthly_charges(force_manual: bool = False):
    """
    Generate monthly charges for all active brokers
    Args:
        force_manual: If True, generates charges regardless of date (for manual admin trigger)
    """
    current_date = datetime.now(GUATEMALA_TZ)
    
    # Only run on 1st of month (unless forced manually)
    if not force_manual and current_date.day != 1:
        return
    
    # Get all active accounts
    accounts = await db.broker_accounts.find({"account_status": {"$ne": AccountStatus.SUSPENDED}}).to_list(length=None)
    
    for account_data in accounts:
        account = BrokerAccount(**parse_from_mongo(account_data))
        
        # Skip if already charged this month
        if account.last_charge_date and account.last_charge_date.month == current_date.month and account.last_charge_date.year == current_date.year:
            continue
        
        # Get broker and plan info
        broker = await db.brokers.find_one({"id": account.broker_id})
        if not broker or not broker.get("subscription_plan_id"):
            continue
            
        plan = await db.subscription_plans.find_one({"id": broker["subscription_plan_id"]})
        if not plan:
            continue
        
        # Calculate next due date based on period
        if plan["period"] == "monthly":
            if current_date.month == 12:
                next_due = datetime(current_date.year + 1, 1, 1, tzinfo=GUATEMALA_TZ)
            else:
                next_due = datetime(current_date.year, current_date.month + 1, 1, tzinfo=GUATEMALA_TZ)
        else:
            # Handle other periods if needed
            next_due = current_date + timedelta(days=30)
        
        # Update account balance and due date
        new_balance = account.current_balance - plan["amount"]
        
        await db.broker_accounts.update_one(
            {"id": account.id},
            {
                "$set": {
                    "current_balance": new_balance,
                    "last_charge_date": current_date,
                    "next_due_date": next_due,
                    "updated_at": current_date
                }
            }
        )
        
        # Create charge transaction
        transaction = BrokerTransaction(
            account_id=account.id,
            broker_id=account.broker_id,
            transaction_type=TransactionType.CHARGE,
            amount=-plan["amount"],
            description=f"Cargo mensual - {plan['name']}",
            balance_after=new_balance,
            due_date=next_due
        )
        
        transaction_dict = prepare_for_mongo(transaction.dict())
        await db.broker_transactions.insert_one(transaction_dict)

async def check_overdue_accounts():
    """Check for overdue accounts and manage grace periods (runs daily)"""
    current_date = datetime.now(GUATEMALA_TZ)
    
    # Get accounts that might be overdue
    accounts = await db.broker_accounts.find({
        "account_status": {"$in": [AccountStatus.ACTIVE, AccountStatus.OVERDUE, AccountStatus.GRACE_PERIOD]},
        "current_balance": {"$lt": 0}  # Has debt
    }).to_list(length=None)
    
    for account_data in accounts:
        account = BrokerAccount(**parse_from_mongo(account_data))
        
        # Check if payment is overdue
        # Ensure both dates are timezone-aware for comparison
        next_due_date = account.next_due_date
        if next_due_date.tzinfo is None:
            next_due_date = next_due_date.replace(tzinfo=GUATEMALA_TZ)
        
        if current_date > next_due_date and account.current_balance < 0:
            
            if account.account_status == AccountStatus.ACTIVE:
                # Move to overdue and start grace period
                grace_end = current_date + timedelta(days=5)
                
                await db.broker_accounts.update_one(
                    {"id": account.id},
                    {
                        "$set": {
                            "account_status": AccountStatus.GRACE_PERIOD,
                            "grace_period_end": grace_end,
                            "updated_at": current_date
                        }
                    }
                )
                
                # Send WhatsApp notification
                await send_overdue_notification(account.broker_id, grace_end)
                
            elif account.account_status == AccountStatus.GRACE_PERIOD and current_date > account.grace_period_end:
                # Grace period expired, suspend account
                await suspend_broker_account(account.broker_id)

async def send_overdue_notification(broker_id: str, grace_end: datetime):
    """Send WhatsApp notification for overdue payment"""
    broker = await db.brokers.find_one({"id": broker_id})
    if not broker:
        return
    
    message = f"""
🚨 *ProtegeYa - Pago Vencido*

Estimado {broker['name']},

Su pago mensual está vencido. Tiene hasta el {grace_end.strftime('%d/%m/%Y')} para regularizar su situación.

Después de esta fecha, su cuenta será suspendida automáticamente.

Para más información, contacte al administrador.
    """.strip()
    
    await send_whatsapp_message(broker["whatsapp_number"], message)

async def suspend_broker_account(broker_id: str):
    """Suspend broker account and deactivate user"""
    # Update account status
    await db.broker_accounts.update_one(
        {"broker_id": broker_id},
        {
            "$set": {
                "account_status": AccountStatus.SUSPENDED,
                "updated_at": datetime.now(GUATEMALA_TZ)
            }
        }
    )
    
    # Deactivate broker
    await db.brokers.update_one(
        {"id": broker_id},
        {"$set": {"subscription_status": BrokerSubscriptionStatus.INACTIVE}}
    )
    
    # Deactivate user
    broker = await db.brokers.find_one({"id": broker_id})
    if broker and broker.get("user_id"):
        await db.auth_users.update_one(
            {"id": broker["user_id"]},
            {"$set": {"active": False}}
        )
    
    # Send suspension notification
    broker_data = await db.brokers.find_one({"id": broker_id})
    if broker_data:
        message = f"""
❌ *ProtegeYa - Cuenta Suspendida*

Estimado {broker_data['name']},

Su cuenta ha sido suspendida por falta de pago.

Para reactivar su cuenta, debe regularizar su situación de pago.

Contacte al administrador para más información.
        """.strip()
        
        await send_whatsapp_message(broker_data["whatsapp_number"], message)

async def generate_quote_pdf(lead_data: dict, broker_data: dict) -> str:
    """Generate PDF quote and return file path"""
    try:
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        pdf_path = temp_file.name
        temp_file.close()
        
        # Create PDF document
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=HexColor('#0F766E'),
            alignment=1  # Center alignment
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=20,
            textColor=HexColor('#0F766E')
        )
        
        # Build PDF content
        story = []
        
        # Header
        story.append(Paragraph("ProtegeYa", title_style))
        story.append(Paragraph("Cotización de Seguro Vehicular", subtitle_style))
        story.append(Spacer(1, 20))
        
        # Client Info
        story.append(Paragraph("Información del Cliente", subtitle_style))
        client_data = [
            ['Nombre:', lead_data.get('name', 'No especificado')],
            ['Teléfono:', lead_data.get('phone_number', 'No especificado')],
            ['Fecha:', datetime.now(GUATEMALA_TZ).strftime('%d/%m/%Y')],
            ['ID de Cotización:', lead_data.get('id', '')[:8] + '...']
        ]
        
        client_table = Table(client_data, colWidths=[2*inch, 3*inch])
        client_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#F0FDFA')),
            ('TEXTCOLOR', (0, 0), (-1, -1), HexColor('#0F172A')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#E5E7EB'))
        ]))
        story.append(client_table)
        story.append(Spacer(1, 20))
        
        # Vehicle Info
        story.append(Paragraph("Información del Vehículo", subtitle_style))
        vehicle_data = [
            ['Marca:', lead_data.get('vehicle_make', 'No especificado')],
            ['Modelo:', lead_data.get('vehicle_model', 'No especificado')],
            ['Año:', str(lead_data.get('vehicle_year', 'No especificado'))],
            ['Valor:', f"Q{lead_data.get('vehicle_value', 0):,.2f}" if lead_data.get('vehicle_value') else 'No especificado']
        ]
        
        vehicle_table = Table(vehicle_data, colWidths=[2*inch, 3*inch])
        vehicle_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#F0FDFA')),
            ('TEXTCOLOR', (0, 0), (-1, -1), HexColor('#0F172A')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#E5E7EB'))
        ]))
        story.append(vehicle_table)
        story.append(Spacer(1, 20))
        
        # Quote Info
        story.append(Paragraph("Cotización Seleccionada", subtitle_style))
        insurance_type_text = "Seguro Completo" if lead_data.get('selected_insurance_type') == 'FullCoverage' else "Responsabilidad Civil"
        
        quote_data = [
            ['Aseguradora:', lead_data.get('selected_insurer', 'No especificada')],
            ['Tipo de Seguro:', insurance_type_text],
            ['Prima Mensual:', f"Q{lead_data.get('selected_quote_price', 0):,.2f}" if lead_data.get('selected_quote_price') else 'No especificada'],
            ['Municipio:', lead_data.get('municipality', 'Guatemala')]
        ]
        
        quote_table = Table(quote_data, colWidths=[2*inch, 3*inch])
        quote_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#FEF3C7')),
            ('TEXTCOLOR', (0, 0), (-1, -1), HexColor('#0F172A')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#E5E7EB'))
        ]))
        story.append(quote_table)
        story.append(Spacer(1, 20))
        
        # Broker Info
        story.append(Paragraph("Corredor Asignado", subtitle_style))
        broker_data_table = [
            ['Nombre:', broker_data.get('name', 'No asignado')],
            ['Corretaje:', broker_data.get('corretaje_name', 'No especificado')],
            ['Credencial:', broker_data.get('credential_id', 'No especificada')],
            ['Teléfono:', broker_data.get('phone_number', 'No especificado')]
        ]
        
        broker_table = Table(broker_data_table, colWidths=[2*inch, 3*inch])
        broker_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#EFF6FF')),
            ('TEXTCOLOR', (0, 0), (-1, -1), HexColor('#0F172A')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#E5E7EB'))
        ]))
        story.append(broker_table)
        story.append(Spacer(1, 30))
        
        # Disclaimer
        disclaimer_text = """
        <b>AVISO IMPORTANTE:</b><br/>
        ProtegeYa es un comparador y generador de leads. No es aseguradora ni corredor. 
        Los precios mostrados son indicativos y deben ser confirmados con un corredor autorizado.
        <br/><br/>
        Para proceder con la contratación, el corredor asignado se pondrá en contacto contigo 
        en las próximas horas para finalizar el proceso y confirmar los detalles de tu póliza.
        """
        
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Normal'],
            fontSize=10,
            textColor=HexColor('#6B7280'),
            borderWidth=1,
            borderColor=HexColor('#D1D5DB'),
            borderPadding=10,
            backColor=HexColor('#F9FAFB')
        )
        
        story.append(Paragraph(disclaimer_text, disclaimer_style))
        
        # Build PDF
        doc.build(story)
        
        logging.info(f"PDF generated successfully: {pdf_path}")
        return pdf_path
        
    except Exception as e:
        logging.error(f"Error generating PDF: {e}")
        return None

async def generate_automatic_quote(vehicle_data: dict, lead_id: str = None) -> str:
    """Generate automatic quote and return formatted summary"""
    try:
        # Create QuoteRequest from vehicle data
        quote_request = QuoteRequest(
            make=vehicle_data.get("make", ""),
            model=vehicle_data.get("model", ""),
            year=int(vehicle_data.get("year", 2020)),
            value=float(vehicle_data.get("value", 100000)),
            municipality=vehicle_data.get("municipality", "Guatemala")
        )
        
        # Calculate quotes
        quotes = await calculate_quotes(quote_request)
        
        if not quotes:
            return "No se pudieron generar cotizaciones en este momento. Un corredor se pondrá en contacto contigo."
        
        # Save quotes to lead if lead_id provided
        if lead_id:
            try:
                await db.leads.update_one(
                    {"id": lead_id},
                    {"$set": {"quotes": quotes, "updated_at": datetime.now(GUATEMALA_TZ)}}
                )
                logging.info(f"Saved {len(quotes)} quotes to lead {lead_id}")
            except Exception as e:
                logging.error(f"Error saving quotes to lead: {e}")
        
        # Format response with only monthly premium per insurer
        response = "🎯 *Cotizaciones disponibles para tu vehículo:*\n\n"
        
        for i, quote in enumerate(quotes[:4], 1):  # Limit to 4 quotes
            insurer = quote["insurer_name"]
            premium = quote["monthly_premium"]
            insurance_type = "Seguro Completo" if quote["insurance_type"] == "FullCoverage" else "Responsabilidad Civil"
            
            response += f"{i}. 🏢 *{insurer}*\n"
            response += f"   💰 Prima mensual: *Q{premium:,.2f}*\n"
            response += f"   📋 Tipo: {insurance_type}\n\n"
        
        response += "⚠️ *Importante:* Estos son precios indicativos. Un corredor autorizado confirmará el precio final y te ayudará con la contratación.\n\n"
        response += "¿Cuál aseguradora y tipo de seguro te interesa?\n\n📝 Puedes responder de varias formas:\n• 'MAPFRE Completo' o 'MAPFRE RC'\n• Solo 'Completo' o solo 'RC' (te cotizaremos la más económica)\n• 'BANTRAB seguro completo' 📞"
        
        return response
        
    except Exception as e:
        logging.error(f"Error generating automatic quote: {e}")
        return "Hubo un error generando las cotizaciones. Un corredor se pondrá en contacto para ayudarte."

async def process_whatsapp_message(phone_number: str, message: str) -> str:
    """Process incoming WhatsApp message using AI"""
    try:
        user = await get_or_create_user(phone_number)
        
        # Get configuration
        config = await db.system_config.find_one({})
        if not config:
            config = {"use_emergent_llm": True}
        
        api_key = EMERGENT_LLM_KEY if config.get("use_emergent_llm", True) else config.get("openai_api_key")
        
        if not api_key:
            return "El sistema de chat no está configurado. Contacte al administrador."
        
        # Get user's current lead if exists (check for any active lead, not just specific statuses)
        current_lead = await db.leads.find_one({
            "user_id": user.id,
            "status": {"$in": [
                LeadStatus.PENDING_DATA, 
                LeadStatus.QUOTED_NO_PREFERENCE, 
                LeadStatus.ASSIGNED_TO_BROKER
            ]}
        })
        
        # If no active lead exists, check if we need to create one
        if not current_lead:
            # Also check for ANY lead by this user to avoid complete duplicates
            any_existing_lead = await db.leads.find_one({"user_id": user.id})
            
            if not any_existing_lead:
                # Check if message is related to insurance/vehicle
                insurance_keywords = ["seguro", "cotizar", "cotización", "vehículo", "carro", "auto", "precio", "póliza"]
                if any(keyword in message.lower() for keyword in insurance_keywords):
                    logging.info(f"Creating new lead for user {user.phone_number}")
                    
                    # Create new lead WITHOUT assigning broker initially
                    new_lead = Lead(
                        user_id=user.id,
                        phone_number=phone_number,
                        name=user.name or "",
                        status=LeadStatus.PENDING_DATA,
                        broker_status=BrokerLeadStatus.NEW
                    )
                    
                    lead_dict = prepare_for_mongo(new_lead.dict())
                    await db.leads.insert_one(lead_dict)
                    current_lead = lead_dict
                    
                    logging.info(f"Lead created without broker assignment: {new_lead.id}")
            else:
                # Use existing lead if it's in an appropriate state
                if any_existing_lead.get("status") in [LeadStatus.PENDING_DATA, LeadStatus.QUOTED_NO_PREFERENCE]:
                    current_lead = any_existing_lead
                    logging.info(f"Using existing lead: {current_lead['id']}")
        
        # Get conversation history for context
        conversation_history = await db.interactions.find({
            "metadata.phone_number": phone_number
        }).sort("created_at", -1).limit(5).to_list(length=5)
        
        # Build conversation context
        conversation_context = ""
        if conversation_history:
            for interaction in reversed(conversation_history):  # Reverse to get chronological order
                user_msg = interaction.get("content", "")
                ai_response = interaction.get("metadata", {}).get("response", "")
                conversation_context += f"Usuario: {user_msg}\nAsistente: {ai_response}\n\n"
        
        # Get custom AI prompt from configuration or use default with quote functionality
        custom_prompt = config.get("ai_chat_prompt", "")
        if custom_prompt:
            system_message = custom_prompt
        else:
            system_message = """Eres un asistente especializado en seguros vehiculares de ProtegeYa, Guatemala.

ROLE: Experto en recolección de datos vehiculares y generación de cotizaciones.

IMPORTANTE: ProtegeYa es un comparador y generador de leads. No es aseguradora ni corredor. Los precios son indicativos.

CONTEXTO DE CONVERSACIÓN:
- Mantén el contexto de toda la conversación anterior
- Si ya tienes el nombre del usuario, NO vuelvas a preguntarlo  
- Si ya tienes datos del vehículo, úsalos para generar cotización
- Progresa lógicamente en la conversación

PROCESO PASO A PASO (OBLIGATORIO):

1. CAPTURAR NOMBRE (solo si no lo tienes):
   Si no conoces el nombre → Pregunta: "¡Hola! Soy el asistente de ProtegeYa 🇬🇹 ¿Cuál es tu nombre completo?"
   Cuando respondan su nombre → GENERAR EXACTAMENTE: "CAPTURAR_NOMBRE:[nombre_completo]"
   
2. RECOPILAR DATOS DEL VEHÍCULO:
   Necesitas: marca, modelo, año, valor en GTQ, municipio
   Pregunta uno por uno si no están completos.
   
3. GENERAR COTIZACIÓN:
   CUANDO tengas marca + modelo + año + valor → GENERAR EXACTAMENTE:
   "GENERAR_COTIZACION:[marca],[modelo],[año],[valor],[municipio]"
   
4. PROCESAR SELECCIÓN:
   Después de mostrar cotizaciones, cuando escojan → GENERAR EXACTAMENTE:
   "SELECCIONAR_ASEGURADORA:[nombre_aseguradora],[tipo_seguro],[precio_mensual]"
   
   REGLAS DE SELECCIÓN:
   - Si mencionan SOLO el tipo (Ej: "Completo" o "RC"): Busca la opción MÁS ECONÓMICA de ese tipo
   - Si mencionan aseguradora + tipo (Ej: "MAPFRE Completo"): Busca esa combinación exacta
   - Variaciones aceptadas: "completo", "seguro completo", "cobertura completa", "RC", "responsabilidad civil", "solo RC"

EJEMPLOS EXACTOS DE RESPUESTA:
- Usuario: "Mi nombre es Juan Carlos Pérez" → "CAPTURAR_NOMBRE:Juan Carlos Pérez"
- Usuario: "Toyota Corolla 2020 vale 150000" → "GENERAR_COTIZACION:Toyota,Corolla,2020,150000,Guatemala"
- Usuario: "Me interesa MAPFRE completo" → "SELECCIONAR_ASEGURADORA:MAPFRE,Seguro Completo,1250.00"
- Usuario: "Completo" (solo tipo) → "SELECCIONAR_ASEGURADORA:[Aseguradora más barata],Seguro Completo,[precio]"
- Usuario: "RC" (solo tipo) → "SELECCIONAR_ASEGURADORA:[Aseguradora más barata],Responsabilidad Civil,[precio]"

INSTRUCCIONES CRÍTICAS:
- SIEMPRE generar los comandos EXACTOS cuando corresponda
- NO reiniciar la conversación si ya tienes datos
- Usar formato guatemalteco amigable
- Ser conciso pero completo"""
        
        # Add special commands to any custom prompt
        if custom_prompt and "CAPTURAR_NOMBRE" not in custom_prompt:
            system_message += "\n\nCOMANDOS ESPECIALES REQUERIDOS:"
            system_message += "\n- Para capturar nombre: 'CAPTURAR_NOMBRE:{nombre_completo}'"
            system_message += "\n- Para generar cotización: 'GENERAR_COTIZACION:{marca},{modelo},{año},{valor},{municipio}'"
            system_message += "\n- Para seleccionar aseguradora: 'SELECCIONAR_ASEGURADORA:{aseguradora},{tipo},{precio}'"
        
        # Initialize AI chat with conversation history
        chat = LlmChat(
            api_key=api_key,
            session_id=f"protegeya_{user.id}",
            system_message=system_message
        ).with_model("openai", "gpt-4o")
        
        # Add context about current lead and conversation
        context = f"Usuario actual: {user.phone_number}"
        if current_lead:
            lead_data = current_lead
            context += f"\nLead ID: {lead_data.get('id', 'N/A')}"
            context += f"\nEstado: {lead_data.get('status', 'sin estado')}"
            context += f"\nNombre del usuario: {lead_data.get('name', 'No especificado')}"
            if lead_data.get('vehicle_make'):
                context += f"\nVehículo actual: {lead_data.get('vehicle_make')} {lead_data.get('vehicle_model')} {lead_data.get('vehicle_year')}"
            if lead_data.get('quote_generated'):
                context += f"\nCotización ya generada: Sí"
        
        # Include conversation history in context
        if conversation_context:
            context += f"\n\nConversación previa:\n{conversation_context}"
        
        user_message = UserMessage(text=f"Contexto: {context}\n\nMensaje del usuario: {message}")
        
        logging.info(f"Sending to AI - Context: {context}")
        logging.info(f"User message: {message}")
        
        response = await chat.send_message(user_message)
        
        logging.info(f"AI Response: {response}")
        
        # Check if AI wants to capture user name
        if "CAPTURAR_NOMBRE:" in response:
            try:
                logging.info("Processing name capture...")
                # Extract name from AI response
                name_data = response.split("CAPTURAR_NOMBRE:")[1].split("\n")[0]
                user_name = name_data.strip()
                
                # Update user and lead with name
                await db.users.update_one(
                    {"id": user.id},
                    {"$set": {"name": user_name, "updated_at": datetime.now(GUATEMALA_TZ)}}
                )
                
                if current_lead:
                    await db.leads.update_one(
                        {"id": current_lead["id"]},
                        {"$set": {"name": user_name, "updated_at": datetime.now(GUATEMALA_TZ)}}
                    )
                
                logging.info(f"User name captured: {user_name} for {phone_number}")
                response = response.replace(f"CAPTURAR_NOMBRE:{user_name}", "").strip()
                
            except Exception as e:
                logging.error(f"Error capturing user name: {e}")
        
        # Check if AI wants to generate a quote
        if "GENERAR_COTIZACION:" in response:
            try:
                logging.info("Processing quote generation...")
                # Extract vehicle data from AI response
                quote_data = response.split("GENERAR_COTIZACION:")[1].split("\n")[0]
                parts = quote_data.split(",")
                
                logging.info(f"Quote data parts: {parts}")
                
                if len(parts) >= 4:
                    vehicle_data = {
                        "make": parts[0].strip(),
                        "model": parts[1].strip(), 
                        "year": parts[2].strip(),
                        "value": parts[3].strip(),
                        "municipality": parts[4].strip() if len(parts) > 4 else "Guatemala"
                    }
                    
                    logging.info(f"Extracted vehicle data: {vehicle_data}")
                    
                    # Update lead with vehicle data
                    if current_lead:
                        # Crear objeto de cotización para el historial
                        new_quotation = {
                            "vehicle_make": vehicle_data["make"],
                            "vehicle_model": vehicle_data["model"],
                            "vehicle_year": int(vehicle_data["year"]),
                            "vehicle_value": float(vehicle_data["value"]),
                            "municipality": vehicle_data["municipality"],
                            "quoted_at": datetime.now(GUATEMALA_TZ).isoformat(),
                            "selected_insurer": "",
                            "selected_type": "",
                            "selected_price": None
                        }
                        
                        # Si es la primera cotización, actualizar campos principales
                        # Si no, solo agregar al historial
                        is_first_quote = not current_lead.get("quote_generated", False)
                        
                        update_data = {
                            "status": LeadStatus.QUOTED_NO_PREFERENCE,
                            "quote_generated": True,
                            "updated_at": datetime.now(GUATEMALA_TZ)
                        }
                        
                        # Solo actualizar campos principales si es la primera cotización
                        if is_first_quote:
                            update_data.update({
                                "vehicle_make": vehicle_data["make"],
                                "vehicle_model": vehicle_data["model"],
                                "vehicle_year": int(vehicle_data["year"]),
                                "vehicle_value": float(vehicle_data["value"]),
                                "municipality": vehicle_data["municipality"]
                            })
                        
                        await db.leads.update_one(
                            {"id": current_lead["id"]},
                            {
                                "$set": update_data,
                                "$push": {"quotations": new_quotation}
                            }
                        )
                        logging.info(f"Updated lead with vehicle data (quote #{len(current_lead.get('quotations', [])) + 1}): {current_lead['id']}")
                    
                    # Generate and return quote
                    lead_id = current_lead["id"] if current_lead else None
                    quote_response = await generate_automatic_quote(vehicle_data, lead_id)
                    response = quote_response
                    logging.info("Quote generation completed")
                    
            except Exception as e:
                logging.error(f"Error processing quote generation: {e}")
                response = "Tengo los datos de tu vehículo. Un corredor se pondrá en contacto contigo pronto para completar la cotización."
        
        # Check if AI wants to select insurer and generate PDF
        elif "SELECCIONAR_ASEGURADORA:" in response:
            try:
                logging.info(f"Processing insurer selection for {phone_number}")
                
                # Extract selection data
                selection_data = response.split("SELECCIONAR_ASEGURADORA:")[1].split("\n")[0]
                parts = selection_data.split(",")
                
                logging.info(f"Selection data parts: {parts}")
                
                if len(parts) >= 3 and current_lead:
                    selected_insurer = parts[0].strip()
                    selected_type = parts[1].strip()
                    selected_price_str = parts[2].strip().replace("Q", "").replace(",", "")
                    
                    try:
                        selected_price = float(selected_price_str)
                    except:
                        logging.error(f"Could not parse price: {selected_price_str}")
                        selected_price = 0.0
                    
                    # Determine insurance type
                    insurance_type = "FullCoverage" if any(word in selected_type.lower() for word in ["completo", "full", "total"]) else "ThirdParty"
                    
                    logging.info(f"Selected: {selected_insurer}, Type: {insurance_type}, Price: {selected_price}")
                    
                    # NOW assign broker when user selects insurer
                    assigned_broker_id = None
                    try:
                        assigned_broker_id = await assign_broker_to_lead(current_lead["id"])
                        logging.info(f"Broker assigned to lead {current_lead['id']}: {assigned_broker_id}")
                    except Exception as e:
                        logging.error(f"Error assigning broker: {e}")
                    
                    # Update lead with selection AND broker assignment
                    update_data = {
                        "selected_insurer": selected_insurer,
                        "selected_insurance_type": insurance_type,
                        "selected_quote_price": selected_price,
                        "status": LeadStatus.ASSIGNED_TO_BROKER,
                        "broker_status": BrokerLeadStatus.INTERESTED,
                        "updated_at": datetime.now(GUATEMALA_TZ)
                    }
                    
                    if assigned_broker_id:
                        update_data["assigned_broker_id"] = assigned_broker_id
                    
                    update_result = await db.leads.update_one(
                        {"id": current_lead["id"]},
                        {"$set": update_data}
                    )
                    
                    logging.info(f"Lead update result: {update_result.modified_count}")
                    
                    # Get updated lead and broker data
                    updated_lead = await db.leads.find_one({"id": current_lead["id"]})
                    broker_data = {}
                    
                    if updated_lead and updated_lead.get("assigned_broker_id"):
                        broker = await db.brokers.find_one({"id": updated_lead["assigned_broker_id"]})
                        if broker:
                            broker_data = broker
                            logging.info(f"Found assigned broker: {broker_data.get('name', 'Unknown')}")
                        else:
                            logging.warning(f"Broker not found for ID: {updated_lead['assigned_broker_id']}")
                    else:
                        logging.warning("No broker was assigned to lead")
                    
                    # Generate PDF
                    logging.info("Generating PDF...")
                    pdf_path = await generate_quote_pdf(updated_lead, broker_data)
                    
                    if pdf_path:
                        logging.info(f"PDF generated at: {pdf_path}")
                        
                        # Send PDF via WhatsApp
                        caption = f"📄 ¡Tu cotización está lista!\n\n🏢 {selected_insurer}\n💰 Q{selected_price:,.2f}/mes\n📋 {'Seguro Completo' if insurance_type == 'FullCoverage' else 'Responsabilidad Civil'}\n\n¡Tu corredor se pondrá en contacto contigo pronto!"
                        
                        logging.info(f"Sending PDF to {phone_number}")
                        pdf_sent = await send_whatsapp_pdf(phone_number, pdf_path, caption)
                        
                        if pdf_sent:
                            await db.leads.update_one(
                                {"id": current_lead["id"]},
                                {"$set": {"pdf_sent": True, "updated_at": datetime.now(GUATEMALA_TZ)}}
                            )
                            
                            logging.info("PDF sent successfully and lead updated")
                            response = f"¡Perfecto! 🎉\n\nHe enviado tu cotización en PDF con todos los detalles:\n\n🏢 {selected_insurer}\n💰 Q{selected_price:,.2f} mensual\n📋 {'Seguro Completo' if insurance_type == 'FullCoverage' else 'Responsabilidad Civil'}\n\n📞 Tu corredor asignado se pondrá en contacto contigo en las próximas horas para finalizar el proceso.\n\n✅ ¡Gracias por elegir ProtegeYa!"
                        else:
                            logging.error("Failed to send PDF")
                            response = f"Tu selección ha sido registrada:\n\n🏢 {selected_insurer}\n💰 Q{selected_price:,.2f}/mes\n\nTu corredor se pondrá en contacto contigo pronto. Hubo un problema enviando el PDF, pero recibirás toda la información por parte de tu corredor."
                    else:
                        logging.error("Failed to generate PDF")
                        response = f"Tu selección ha sido registrada:\n\n🏢 {selected_insurer}\n💰 Q{selected_price:,.2f}/mes\n\nTu corredor se pondrá en contacto contigo pronto para completar el proceso."
                else:
                    logging.error(f"Invalid selection format. Parts count: {len(parts)}, Current lead: {current_lead is not None}")
                    response = "No pude procesar tu selección. Por favor indica claramente qué aseguradora y tipo de seguro te interesa."
                        
            except Exception as e:
                logging.error(f"Error processing insurer selection: {e}")
                logging.error(f"Selection raw data: {response}")
                response = "Tu selección ha sido registrada. Un corredor se pondrá en contacto contigo pronto."
        
        # Check if user is trying to select an insurer in natural language
        elif current_lead and current_lead.get("quote_generated") and any(word in message.lower() for word in ["me interesa", "quiero", "elijo", "escojo", "prefiero"]):
            try:
                # Try to extract insurer and type from natural language
                insurers = ["El Roble", "Seguros Universal", "Aseguradora Rural", "Mapfre"]
                types = ["completo", "responsabilidad", "civil", "basico"]
                
                selected_insurer = None
                selected_type = "completo"  # default
                
                for insurer in insurers:
                    if insurer.lower() in message.lower():
                        selected_insurer = insurer
                        break
                
                for tipo in types:
                    if tipo.lower() in message.lower():
                        selected_type = tipo
                        break
                
                if selected_insurer:
                    # Try to find the price from the last quotes generated
                    quotes = current_lead.get("quotes", [])
                    selected_price = 1000.0  # default fallback
                    
                    for quote in quotes:
                        if quote.get("insurer_name", "").lower() in selected_insurer.lower():
                            selected_price = quote.get("monthly_premium", 1000.0)
                            break
                    
                    logging.info(f"Natural language selection: {selected_insurer}, {selected_type}, {selected_price}")
                    
                    # Process as if it were a structured selection
                    selection_string = f"SELECCIONAR_ASEGURADORA:{selected_insurer},{selected_type},{selected_price}"
                    response = selection_string + "\n" + response
                    
                    logging.info(f"Generated selection string: {selection_string}")
                    
            except Exception as e:
                logging.error(f"Error processing natural language selection: {e}")
        
        # Log interaction
        interaction = LeadInteraction(
            lead_id=current_lead["id"] if current_lead else "none",
            interaction_type="whatsapp_message",
            content=message,
            metadata={
                "response": response,
                "phone_number": phone_number,
                "user_id": user.id,
                "timestamp": datetime.now(GUATEMALA_TZ).isoformat()
            }
        )
        interaction_dict = prepare_for_mongo(interaction.dict())
        interaction_dict["created_at"] = datetime.now(GUATEMALA_TZ)
        await db.interactions.insert_one(interaction_dict)
        
        return response
        
    except Exception as e:
        logging.error(f"Error processing WhatsApp message: {e}")
        return "Disculpa, hubo un error. Por favor intenta de nuevo o escribe 'ayuda'."

# Authentication Routes
@api_router.post("/auth/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, current_admin: UserResponse = Depends(require_admin)):
    """Register new user (admin only)"""
    # Check if user exists
    existing_user = await db.auth_users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    hashed_password = hash_password(user_data.password)
    
    # Create user
    new_user = {
        "id": str(uuid.uuid4()),
        "email": user_data.email,
        "password": hashed_password,
        "name": user_data.name,
        "role": user_data.role,
        "active": True,
        "created_at": datetime.now(GUATEMALA_TZ)
    }
    
    user_dict = prepare_for_mongo(new_user)
    await db.auth_users.insert_one(user_dict)
    
    # If broker, create broker profile
    if user_data.role == UserRole.BROKER:
        broker_profile = BrokerProfile(
            user_id=new_user["id"],
            name=user_data.name,
            email=user_data.email,
            phone_number="",  # To be filled later
            whatsapp_number=""
        )
        broker_dict = prepare_for_mongo(broker_profile.dict())
        await db.brokers.insert_one(broker_dict)
    
    return UserResponse(**new_user)

@api_router.post("/auth/login", response_model=TokenResponse)
async def login_user(login_data: UserLogin):
    """Login user"""
    user = await db.auth_users.find_one({"email": login_data.email})
    if not user or not verify_password(login_data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    if not user.get("active", True):
        raise HTTPException(status_code=400, detail="User account is disabled")
    
    # Create access token
    access_token = create_access_token(data={"sub": user["id"]})
    
    user = parse_from_mongo(user)
    user_response = UserResponse(**user)
    
    return TokenResponse(
        access_token=access_token,
        user=user_response
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_current_user_profile(current_user: UserResponse = Depends(get_current_user)):
    """Get current user profile"""
    return current_user

@api_router.get("/auth/users", response_model=List[UserResponse])
async def get_all_users(current_admin: UserResponse = Depends(require_admin)):
    """Get all users (admin only)"""
    users = await db.auth_users.find().to_list(length=None)
    return [UserResponse(**parse_from_mongo(user)) for user in users]

@api_router.put("/auth/users/{user_id}/toggle-status")
async def toggle_user_status(user_id: str, current_admin: UserResponse = Depends(require_admin)):
    """Toggle user active status (admin only)"""
    user = await db.auth_users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_status = not user.get("active", True)
    
    # Update auth user status
    await db.auth_users.update_one(
        {"id": user_id},
        {"$set": {"active": new_status}}
    )
    
    # If it's a broker, also update broker subscription status
    if user.get("role") == UserRole.BROKER:
        broker_status = BrokerSubscriptionStatus.ACTIVE if new_status else BrokerSubscriptionStatus.INACTIVE
        await db.brokers.update_one(
            {"user_id": user_id},
            {"$set": {"subscription_status": broker_status}}
        )
    
    return {"success": True, "active": new_status}

class PasswordReset(BaseModel):
    new_password: str

@api_router.put("/auth/users/{user_id}/reset-password")
async def reset_user_password(user_id: str, password_data: PasswordReset, current_admin: UserResponse = Depends(require_admin)):
    """Reset user password (admin only)"""
    user = await db.auth_users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Hash new password
    hashed_password = hash_password(password_data.new_password)
    
    # Update password
    await db.auth_users.update_one(
        {"id": user_id},
        {"$set": {"password": hashed_password}}
    )
    
    return {"success": True, "message": "Password reset successfully"}

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None

@api_router.put("/auth/users/{user_id}")
async def update_user(user_id: str, user_data: UserUpdate, current_admin: UserResponse = Depends(require_admin)):
    """Update user information (admin only)"""
    user = await db.auth_users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if email is being changed and if it already exists
    if user_data.email and user_data.email != user.get("email"):
        existing_user = await db.auth_users.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already exists")
    
    # Prepare update data
    update_data = {k: v for k, v in user_data.dict().items() if v is not None}
    
    if update_data:
        await db.auth_users.update_one(
            {"id": user_id},
            {"$set": update_data}
        )
        
        # If it's a broker, also update broker profile
        if user.get("role") == UserRole.BROKER or user_data.role == UserRole.BROKER:
            broker_update = {}
            if user_data.name:
                broker_update["name"] = user_data.name
            if user_data.email:
                broker_update["email"] = user_data.email
            
            if broker_update:
                await db.brokers.update_one(
                    {"user_id": user_id},
                    {"$set": broker_update}
                )
    
    return {"success": True, "message": "User updated successfully"}

@api_router.delete("/auth/users/{user_id}")
async def delete_user(user_id: str, current_admin: UserResponse = Depends(require_admin)):
    """Delete user (admin only) - Also deletes associated broker profile and account"""
    # Prevent deleting yourself
    if user_id == current_admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    # Get user to check if it exists and get role
    user = await db.auth_users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # If it's a broker, delete associated data
    if user.get("role") == UserRole.BROKER:
        # Find broker profile
        broker = await db.brokers.find_one({"user_id": user_id})
        if broker:
            broker_id = broker["id"]
            
            # Delete broker account
            await db.broker_accounts.delete_many({"broker_id": broker_id})
            
            # Delete broker transactions
            await db.broker_transactions.delete_many({"broker_id": broker_id})
            
            # Unassign leads from this broker
            await db.leads.update_many(
                {"assigned_broker_id": broker_id},
                {"$set": {"assigned_broker_id": None, "broker_status": "New"}}
            )
            
            # Delete broker profile
            await db.brokers.delete_one({"id": broker_id})
    
    # Delete auth user
    await db.auth_users.delete_one({"id": user_id})
    
    logging.info(f"Admin {current_admin.email} deleted user {user.get('email')} (ID: {user_id})")
    
    return {"success": True, "message": "User deleted successfully"}

# API Routes

@api_router.get("/")
async def root():
    return {"message": "ProtegeYa API - Insurance Lead Generator", "status": "active"}

# WhatsApp Routes
@api_router.post("/whatsapp/webhook")
async def whatsapp_webhook(request: dict, background_tasks: BackgroundTasks):
    """Handle incoming WhatsApp webhook from UltraMSG"""
    try:
        logging.info(f"UltraMSG webhook received: {request}")
        
        # UltraMSG webhook structure can vary, let's handle different formats
        # Sometimes data comes directly, sometimes in 'data' field
        data = request.get("data", request)
        
        # Handle message events - UltraMSG sends different formats
        is_incoming_message = (
            data.get("event_type") in ["message", "message_received"] or 
            data.get("type") in ["message", "chat"] or
            "body" in data  # Direct message format
        )
        
        if is_incoming_message:
            # CRITICAL: Only process messages FROM users TO us, not messages we send
            from_me = data.get("fromMe", False)
            if from_me:
                logging.info("Ignoring outbound message (sent by us)")
                return {"status": "received", "message": "Outbound message ignored"}
            
            # Extract phone number and message
            phone_number = data.get("from", "").replace("@c.us", "")
            message_text = data.get("body", "")
            message_type = data.get("type", "text")
            
            # Only process text messages for now
            if message_text and phone_number and message_type in ["message", "text", "chat"]:
                # Clean phone number
                phone_number = phone_number.replace("+", "").replace("-", "").replace(" ", "")
                
                logging.info(f"Processing INBOUND WhatsApp message from {phone_number}: {message_text}")
                logging.info(f"Full webhook data: {data}")
                
                # Process message in background
                background_tasks.add_task(
                    handle_whatsapp_message_async, 
                    phone_number, 
                    message_text
                )
            else:
                logging.info(f"Skipping message - invalid format or missing data")
                logging.info(f"Phone: {phone_number}, Message: {message_text}, Type: {message_type}")
        
        # Handle delivery receipts and other events
        elif data.get("event_type") == "message_ack" or "ack" in data:
            message_id = data.get("id", "")
            ack_status = data.get("ack", "")
            logging.info(f"Message {message_id} delivery status: {ack_status}")
            # Here you could update message delivery status in database
        
        return {"status": "received", "message": "Webhook processed successfully"}
        
    except Exception as e:
        logging.error(f"WhatsApp webhook error: {str(e)}")
        logging.error(f"Request data: {request}")
        # Don't raise exception to avoid webhook retries from UltraMSG
        return {"status": "error", "message": "Webhook processing failed"}

async def handle_whatsapp_message_async(phone_number: str, message: str):
    """Async handler for WhatsApp messages"""
    try:
        logging.info(f"Processing message from {phone_number}: {message}")
        
        # Anti-loop protection: Check if this exact message was processed recently
        recent_interaction = await db.interactions.find_one({
            "metadata.phone_number": phone_number,
            "content": message,
            "created_at": {"$gte": datetime.now(GUATEMALA_TZ) - timedelta(minutes=2)}
        })
        
        if recent_interaction:
            logging.info(f"Duplicate message detected for {phone_number}, skipping processing")
            return
        
        response = await process_whatsapp_message(phone_number, message)
        
        if response:
            # Send response via UltraMSG
            success = await send_whatsapp_message(phone_number, response)
            if success:
                logging.info(f"Response sent successfully to {phone_number}")
            else:
                logging.error(f"Failed to send response to {phone_number}")
        
    except Exception as e:
        logging.error(f"Error handling WhatsApp message async: {e}")
        logging.error(f"Error details - Phone: {phone_number}, Message: {message}")

async def send_whatsapp_message(phone_number: str, message: str) -> bool:
    """Send WhatsApp message via UltraMSG"""
    try:
        # Get UltraMSG credentials from environment
        ultramsg_instance_id = os.environ.get('ULTRAMSG_INSTANCE_ID')
        ultramsg_token = os.environ.get('ULTRAMSG_TOKEN')
        
        if not ultramsg_instance_id or not ultramsg_token:
            # Try getting from database config as fallback
            config = await db.system_config.find_one({})
            if config and config.get("whatsapp_enabled", False):
                ultramsg_instance_id = config.get('ultramsg_instance_id')
                ultramsg_token = config.get('ultramsg_token')
            else:
                logging.info(f"MOCK WhatsApp send to {phone_number}: {message}")
                return True
        
        if not ultramsg_instance_id or not ultramsg_token:
            logging.warning("UltraMSG credentials not configured")
            return False
        
        # Format phone number correctly (should include country code without +)
        # Assuming Guatemala numbers, add 502 if not present
        formatted_phone = phone_number.replace("+", "").replace("-", "").replace(" ", "")
        if not formatted_phone.startswith("502") and len(formatted_phone) == 8:
            formatted_phone = f"502{formatted_phone}"
        
        # Real UltraMSG API call
        ultramsg_url = f"https://api.ultramsg.com/{ultramsg_instance_id}/messages/chat"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        payload = {
            "token": ultramsg_token,
            "to": formatted_phone,
            "body": message
        }
        
        logging.info(f"Sending WhatsApp message to {formatted_phone} via UltraMSG")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(ultramsg_url, data=payload, headers=headers)
            
            if response.status_code == 200:
                response_data = response.json()
                logging.info(f"WhatsApp message sent successfully: {response_data}")
                return response_data.get("sent", False)
            else:
                logging.error(f"UltraMSG API error: {response.status_code} - {response.text}")
                return False
        
    except Exception as e:
        logging.error(f"Error sending WhatsApp message: {e}")
        return False

async def send_broker_lead_notification(broker_data: dict, lead_data: dict) -> bool:
    """Send WhatsApp notification to broker about new lead assignment"""
    try:
        # Get broker's WhatsApp number
        broker_whatsapp = broker_data.get("whatsapp_number") or broker_data.get("phone_number")
        
        if not broker_whatsapp:
            logging.warning(f"No WhatsApp number found for broker {broker_data.get('name', 'Unknown')}")
            return False
        
        # Clean and format phone number
        broker_phone = broker_whatsapp.replace("+", "").replace("-", "").replace(" ", "")
        if not broker_phone.startswith("502") and len(broker_phone) == 8:
            broker_phone = f"502{broker_phone}"
        
        # Get lead details
        client_name = lead_data.get("name", "Cliente")
        client_phone = lead_data.get("phone_number", "No especificado")
        vehicle_info = ""
        
        # Build vehicle information if available
        if lead_data.get("vehicle_make") and lead_data.get("vehicle_model"):
            vehicle_year = lead_data.get("vehicle_year", "")
            vehicle_value = lead_data.get("vehicle_value", 0)
            vehicle_info = f"\n🚗 *Vehículo:* {lead_data['vehicle_make']} {lead_data['vehicle_model']} {vehicle_year}"
            if vehicle_value:
                vehicle_info += f"\n💰 *Valor:* Q{vehicle_value:,.2f}"
        
        # Build selected insurer info if available
        insurer_info = ""
        if lead_data.get("selected_insurer"):
            insurance_type = "Seguro Completo" if lead_data.get("selected_insurance_type") == "FullCoverage" else "Responsabilidad Civil"
            selected_price = lead_data.get("selected_quote_price", 0)
            insurer_info = f"\n🏢 *Aseguradora:* {lead_data['selected_insurer']}"
            insurer_info += f"\n📋 *Tipo:* {insurance_type}"
            if selected_price:
                insurer_info += f"\n💵 *Prima mensual:* Q{selected_price:,.2f}"
        
        # Create notification message
        notification_message = f"""🔔 *Nuevo Lead Asignado - ProtegeYa*

👤 *Cliente:* {client_name}
📱 *Teléfono:* {client_phone}{vehicle_info}{insurer_info}

⏰ *Plazo de contacto:* 2 horas
🎯 *Estado:* Interesado en cotización

¡Contacta al cliente lo antes posible para cerrar la venta!

_Mensaje automático de ProtegeYa_"""

        # Send notification
        success = await send_whatsapp_message(broker_phone, notification_message)
        
        if success:
            logging.info(f"Lead notification sent successfully to broker {broker_data.get('name', 'Unknown')} at {broker_phone}")
        else:
            logging.error(f"Failed to send lead notification to broker {broker_data.get('name', 'Unknown')}")
        
        return success
        
    except Exception as e:
        logging.error(f"Error sending broker notification: {e}")
        return False

async def send_whatsapp_pdf(phone_number: str, pdf_path: str, caption: str = "") -> bool:
    """Send PDF file via UltraMSG"""
    try:
        # Get UltraMSG credentials from environment
        ultramsg_instance_id = os.environ.get('ULTRAMSG_INSTANCE_ID')
        ultramsg_token = os.environ.get('ULTRAMSG_TOKEN')
        
        if not ultramsg_instance_id or not ultramsg_token:
            # Try getting from database config as fallback
            config = await db.system_config.find_one({})
            if config and config.get("whatsapp_enabled", False):
                ultramsg_instance_id = config.get('ultramsg_instance_id')
                ultramsg_token = config.get('ultramsg_token')
            else:
                logging.info(f"MOCK PDF send to {phone_number}: {pdf_path}")
                return True
        
        if not ultramsg_instance_id or not ultramsg_token:
            logging.warning("UltraMSG credentials not configured for PDF sending")
            return False
        
        # Format phone number correctly
        formatted_phone = phone_number.replace("+", "").replace("-", "").replace(" ", "")
        if not formatted_phone.startswith("502") and len(formatted_phone) == 8:
            formatted_phone = f"502{formatted_phone}"
        
        # UltraMSG document sending endpoint
        ultramsg_url = f"https://api.ultramsg.com/{ultramsg_instance_id}/messages/document"
        
        logging.info(f"Sending PDF to {formatted_phone} via UltraMSG")
        
        # Prepare file for upload
        with open(pdf_path, 'rb') as pdf_file:
            files = {
                'document': ('cotizacion.pdf', pdf_file, 'application/pdf')
            }
            
            data = {
                'token': ultramsg_token,
                'to': formatted_phone,
                'caption': caption or "📄 Tu cotización de ProtegeYa está lista"
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(ultramsg_url, data=data, files=files)
                
                if response.status_code == 200:
                    response_data = response.json()
                    logging.info(f"PDF sent successfully: {response_data}")
                    
                    # Clean up temporary file
                    try:
                        os.unlink(pdf_path)
                        logging.info(f"Temporary PDF file deleted: {pdf_path}")
                    except:
                        pass
                    
                    return response_data.get("sent", False)
                else:
                    logging.error(f"UltraMSG PDF API error: {response.status_code} - {response.text}")
                    return False
        
    except Exception as e:
        logging.error(f"Error sending PDF via WhatsApp: {e}")
        return False

# Test endpoint for WhatsApp
@api_router.post("/whatsapp/test")
async def test_whatsapp_message(phone_number: str, message: str, current_admin: UserResponse = Depends(require_admin)):
    """Test WhatsApp message sending (admin only)"""
    try:
        success = await send_whatsapp_message(phone_number, message)
        return {
            "success": success, 
            "message": "Message sent successfully" if success else "Failed to send message",
            "phone_number": phone_number,
            "test_message": message
        }
    except Exception as e:
        logging.error(f"Test WhatsApp error: {e}")
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")

@api_router.post("/whatsapp/send")
async def send_whatsapp(message_data: WhatsAppMessage, current_user: UserResponse = Depends(get_current_user)):
    """Manually send WhatsApp message"""
    try:
        logging.info(f"WhatsApp send request from user {current_user.email}: {message_data.phone_number}")
        
        success = await send_whatsapp_message(message_data.phone_number, message_data.message)
        
        response = {
            "success": success,
            "phone_number": message_data.phone_number,
            "message_length": len(message_data.message),
            "timestamp": datetime.now(GUATEMALA_TZ).isoformat()
        }
        
        if success:
            response["status"] = "Message sent successfully"
        else:
            response["status"] = "Failed to send message"
            response["error"] = "Check server logs for details"
        
        return response
        
    except Exception as e:
        logging.error(f"Error in send_whatsapp endpoint: {e}")
        return {
            "success": False,
            "error": str(e),
            "phone_number": message_data.phone_number,
            "timestamp": datetime.now(GUATEMALA_TZ).isoformat()
        }

# Initialize UltraMSG configuration on startup
async def initialize_ultramsg_config():
    """Initialize UltraMSG configuration from environment variables"""
    try:
        # Check if configuration already exists
        config = await db.system_config.find_one({})
        
        ultramsg_instance_id = os.environ.get('ULTRAMSG_INSTANCE_ID')
        ultramsg_token = os.environ.get('ULTRAMSG_TOKEN')
        ultramsg_webhook_secret = os.environ.get('ULTRAMSG_WEBHOOK_SECRET')
        
        if ultramsg_instance_id and ultramsg_token:
            config_data = {
                "ultramsg_instance_id": ultramsg_instance_id,
                "ultramsg_token": ultramsg_token,
                "ultramsg_webhook_secret": ultramsg_webhook_secret,
                "whatsapp_enabled": True,  # Auto-enable if credentials are present
                "use_emergent_llm": True,
                "updated_at": datetime.now(GUATEMALA_TZ)
            }
            
            if config:
                # Update existing config
                await db.system_config.update_one(
                    {"id": config["id"]},
                    {"$set": config_data}
                )
                logging.info("UltraMSG configuration updated from environment")
            else:
                # Create new config
                config_data["id"] = str(uuid.uuid4())
                config_data["created_at"] = datetime.now(GUATEMALA_TZ)
                
                config_dict = prepare_for_mongo(config_data)
                await db.system_config.insert_one(config_dict)
                logging.info("UltraMSG configuration initialized from environment")
        else:
            logging.warning("UltraMSG credentials not found in environment")
            
    except Exception as e:
        logging.error(f"Error initializing UltraMSG config: {e}")

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
async def create_insurer(insurer: Insurer, current_admin: UserResponse = Depends(require_admin)):
    """Create new insurer"""
    insurer_dict = prepare_for_mongo(insurer.dict())
    await db.insurers.insert_one(insurer_dict)
    return insurer

@api_router.get("/admin/insurers", response_model=List[Insurer])
async def get_insurers(current_user: UserResponse = Depends(get_current_user)):
    """Get all insurers"""
    insurers = await db.insurers.find().to_list(length=None)
    return [Insurer(**parse_from_mongo(insurer)) for insurer in insurers]

@api_router.put("/admin/insurers/{insurer_id}")
async def update_insurer(insurer_id: str, insurer_data: Dict[str, Any], current_admin: UserResponse = Depends(require_admin)):
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

@api_router.delete("/admin/insurers/{insurer_id}")
async def delete_insurer(insurer_id: str, current_admin: UserResponse = Depends(require_admin)):
    """Delete insurer"""
    # Check if insurer has products
    products = await db.products.find({"insurer_id": insurer_id}).to_list(length=1)
    if products:
        raise HTTPException(status_code=400, detail="Cannot delete insurer with associated products")
    
    result = await db.insurers.delete_one({"id": insurer_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Insurer not found")
    return {"success": True}

# Admin Routes - Products
@api_router.post("/admin/products", response_model=Product)
async def create_product(product: Product, current_admin: UserResponse = Depends(require_admin)):
    """Create new insurance product"""
    product_dict = prepare_for_mongo(product.dict())
    await db.products.insert_one(product_dict)
    return product

@api_router.get("/admin/products", response_model=List[Product])
async def get_products(current_user: UserResponse = Depends(get_current_user)):
    """Get all products"""
    products = await db.products.find().to_list(length=None)
    return [Product(**parse_from_mongo(product)) for product in products]

@api_router.put("/admin/products/{product_id}")
async def update_product(product_id: str, product_data: Dict[str, Any], current_admin: UserResponse = Depends(require_admin)):
    """Update product"""
    product_data["updated_at"] = datetime.now(GUATEMALA_TZ)
    product_dict = prepare_for_mongo(product_data)
    
    result = await db.products.update_one(
        {"id": product_id},
        {"$set": product_dict}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"success": True}

@api_router.delete("/admin/products/{product_id}")
async def delete_product(product_id: str, current_admin: UserResponse = Depends(require_admin)):
    """Delete product"""
    # Check if product has versions
    versions = await db.product_versions.find({"product_id": product_id}).to_list(length=1)
    if versions:
        raise HTTPException(status_code=400, detail="Cannot delete product with associated versions")
    
    result = await db.products.delete_one({"id": product_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"success": True}

# Admin Routes - Product Versions
@api_router.post("/admin/product-versions", response_model=ProductVersion)
async def create_product_version(version: ProductVersion, current_admin: UserResponse = Depends(require_admin)):
    """Create new product version"""
    version_dict = prepare_for_mongo(version.dict())
    await db.product_versions.insert_one(version_dict)
    return version

@api_router.get("/admin/product-versions/{product_id}")
async def get_product_versions(product_id: str, current_user: UserResponse = Depends(get_current_user)):
    """Get versions for a product"""
    versions = await db.product_versions.find({"product_id": product_id}).to_list(length=None)
    return [ProductVersion(**parse_from_mongo(version)) for version in versions]

# Admin Routes - Tariff Sections
@api_router.post("/admin/tariff-sections", response_model=TariffSection)
async def create_tariff_section(section: TariffSection, current_admin: UserResponse = Depends(require_admin)):
    """Create tariff section"""
    section_dict = prepare_for_mongo(section.dict())
    await db.tariff_sections.insert_one(section_dict)
    return section

# Admin Routes - Fixed Benefits
@api_router.post("/admin/fixed-benefits", response_model=FixedBenefit)
async def create_fixed_benefit(benefit: FixedBenefit, current_admin: UserResponse = Depends(require_admin)):
    """Create fixed benefit"""
    benefit_dict = prepare_for_mongo(benefit.dict())
    await db.fixed_benefits.insert_one(benefit_dict)
    return benefit

# Lead Management Routes
@api_router.get("/leads")
async def get_leads(
    current_user: UserResponse = Depends(get_current_user), 
    limit: int = 50,
    status: Optional[str] = None,
    broker_status: Optional[str] = None,
    assigned_broker_id: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None
):
    """Get leads with filters (broker sees only assigned, admin sees all)"""
    query = {}
    
    if current_user.role == UserRole.BROKER:
        # Get broker profile
        broker = await db.brokers.find_one({"user_id": current_user.id})
        if broker:
            query["assigned_broker_id"] = broker["id"]
        else:
            query["assigned_broker_id"] = "none"  # No results
    
    # Apply filters (only for admin or if doesn't conflict with broker restriction)
    if status and (current_user.role == UserRole.ADMIN or status in query.get("status", [])):
        query["status"] = status
    
    if broker_status:
        query["broker_status"] = broker_status
    
    if assigned_broker_id and current_user.role == UserRole.ADMIN:
        query["assigned_broker_id"] = assigned_broker_id
    
    # Date filtering by month/year
    if month and year:
        start_date = datetime(year, month, 1, tzinfo=GUATEMALA_TZ)
        if month == 12:
            end_date = datetime(year + 1, 1, 1, tzinfo=GUATEMALA_TZ)
        else:
            end_date = datetime(year, month + 1, 1, tzinfo=GUATEMALA_TZ)
        
        query["created_at"] = {
            "$gte": start_date.isoformat(),
            "$lt": end_date.isoformat()
        }
    
    leads = await db.leads.find(query).limit(limit).to_list(length=None)
    return [Lead(**parse_from_mongo(lead)) for lead in leads]

@api_router.post("/leads/{lead_id}/status")
async def update_broker_lead_status(lead_id: str, status_update: BrokerLeadStatusUpdate, current_user: UserResponse = Depends(get_current_user)):
    """Update broker lead status"""
    # Verify lead access
    lead = await db.leads.find_one({"id": lead_id})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    if current_user.role == UserRole.BROKER:
        broker = await db.brokers.find_one({"user_id": current_user.id})
        if not broker or lead.get("assigned_broker_id") != broker["id"]:
            raise HTTPException(status_code=403, detail="Access denied to this lead")
    
    # Update lead status
    update_data = {
        "broker_status": status_update.broker_status,
        "updated_at": datetime.now(GUATEMALA_TZ)
    }
    
    if status_update.notes:
        update_data["broker_notes"] = status_update.notes
    
    if status_update.closed_amount:
        update_data["closed_amount"] = status_update.closed_amount
    
    # Update broker stats if closed won
    if status_update.broker_status == BrokerLeadStatus.CLOSED_WON and status_update.closed_amount:
        broker = await db.brokers.find_one({"user_id": current_user.id})
        if broker:
            await db.brokers.update_one(
                {"id": broker["id"]},
                {
                    "$inc": {
                        "total_closed_deals": 1,
                        "total_revenue": status_update.closed_amount
                    }
                }
            )
    
    await db.leads.update_one(
        {"id": lead_id},
        {"$set": update_data}
    )
    
    return {"success": True}

# Broker Routes
@api_router.get("/brokers")
async def get_brokers(current_admin: UserResponse = Depends(require_admin)):
    """Get all brokers (admin only)"""
    try:
        brokers = await db.brokers.find().to_list(length=None)
        valid_brokers = []
        
        for broker in brokers:
            # Skip brokers without required fields
            if 'user_id' not in broker:
                continue
            
            try:
                parsed_broker = parse_from_mongo(broker)
                valid_brokers.append(BrokerProfile(**parsed_broker))
            except Exception as e:
                logging.warning(f"Skipping invalid broker {broker.get('id', 'unknown')}: {e}")
                continue
        
        return valid_brokers
    except Exception as e:
        logging.error(f"Error fetching brokers: {e}")
        return []

@api_router.post("/admin/brokers", response_model=BrokerProfile)
async def create_broker(broker_data: BrokerCreate, current_admin: UserResponse = Depends(require_admin)):
    """Create new broker (admin only)"""
    # Check if email already exists
    existing_user = await db.auth_users.find_one({"email": broker_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Create auth user first
    hashed_password = hash_password(broker_data.password)
    
    user = {
        "id": str(uuid.uuid4()),
        "email": broker_data.email,
        "password": hashed_password,
        "name": broker_data.name,
        "role": UserRole.BROKER,
        "active": True,
        "created_at": datetime.now(GUATEMALA_TZ)
    }
    
    user_dict = prepare_for_mongo(user)
    await db.auth_users.insert_one(user_dict)
    
    # Create broker profile
    broker_profile = BrokerProfile(
        user_id=user["id"],
        name=broker_data.name,
        email=broker_data.email,
        phone_number=broker_data.phone_number,
        whatsapp_number=broker_data.whatsapp_number,
        corretaje_name=broker_data.corretaje_name,
        broker_credential=broker_data.broker_credential,
        subscription_status=broker_data.subscription_status,
        monthly_lead_quota=broker_data.monthly_lead_quota,
        commission_percentage=broker_data.commission_percentage
    )
    
    broker_dict = prepare_for_mongo(broker_profile.dict())
    await db.brokers.insert_one(broker_dict)
    
    return broker_profile

@api_router.post("/brokers", response_model=BrokerProfile)
async def create_broker(broker: BrokerProfile, current_admin: UserResponse = Depends(require_admin)):
    """Create new broker (admin only)"""
    # Assign default subscription plan if none provided
    if not broker.subscription_plan_id:
        default_plan = await db.subscription_plans.find_one({"name": "Plan Básico ProtegeYa"})
        if default_plan:
            broker.subscription_plan_id = default_plan["id"]
    
    broker_dict = prepare_for_mongo(broker.dict())
    await db.brokers.insert_one(broker_dict)
    return broker

class BrokerPlanAssignment(BaseModel):
    subscription_plan_id: str

@api_router.post("/admin/brokers/{broker_id}/assign-plan")
async def assign_plan_to_broker(broker_id: str, assignment: BrokerPlanAssignment, current_admin: UserResponse = Depends(require_admin)):
    """Assign subscription plan to broker and create account (admin only)"""
    # Check if broker exists
    broker = await db.brokers.find_one({"id": broker_id})
    if not broker:
        raise HTTPException(status_code=404, detail="Broker not found")
    
    # Check if plan exists
    plan = await db.subscription_plans.find_one({"id": assignment.subscription_plan_id})
    if not plan:
        raise HTTPException(status_code=404, detail="Subscription plan not found")
    
    # Check if account already exists
    existing_account = await db.broker_accounts.find_one({"broker_id": broker_id})
    if existing_account:
        raise HTTPException(status_code=400, detail="Broker already has an account. Use update instead.")
    
    # Update broker with subscription plan
    await db.brokers.update_one(
        {"id": broker_id},
        {
            "$set": {
                "subscription_plan_id": assignment.subscription_plan_id,
                "subscription_status": BrokerSubscriptionStatus.ACTIVE,
                "updated_at": datetime.now(GUATEMALA_TZ)
            }
        }
    )
    
    # Create broker account
    account_id = await create_broker_account(broker_id, assignment.subscription_plan_id)
    
    return {"success": True, "account_id": account_id, "message": "Plan assigned and account created successfully"}

@api_router.put("/brokers/{broker_id}")
async def update_broker(broker_id: str, broker_data: Dict[str, Any], current_admin: UserResponse = Depends(require_admin)):
    """Update broker (admin only)"""
    broker_data["updated_at"] = datetime.now(GUATEMALA_TZ)
    broker_dict = prepare_for_mongo(broker_data)
    
    result = await db.brokers.update_one(
        {"id": broker_id},
        {"$set": broker_dict}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Broker not found")
    return {"success": True}

@api_router.delete("/brokers/{broker_id}")
async def delete_broker(broker_id: str, current_admin: UserResponse = Depends(require_admin)):
    """Delete broker (admin only)"""
    # Check if broker has active leads
    active_leads = await db.leads.find({"assigned_broker_id": broker_id}).to_list(length=1)
    if active_leads:
        raise HTTPException(status_code=400, detail="Cannot delete broker with assigned leads")
    
    result = await db.brokers.delete_one({"id": broker_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Broker not found")
    
    # Also delete associated auth user if exists
    broker_data = await db.brokers.find_one({"id": broker_id})
    if broker_data and broker_data.get("user_id"):
        await db.auth_users.delete_one({"id": broker_data["user_id"]})
    
    return {"success": True}

# ========== ASEGURADORAS ROUTES ==========

@api_router.get("/admin/aseguradoras", response_model=List[Aseguradora])
async def get_aseguradoras(current_admin: UserResponse = Depends(require_admin)):
    """Get all aseguradoras (admin only)"""
    aseguradoras = await db.aseguradoras.find().to_list(length=None)
    return [Aseguradora(**parse_from_mongo(aseg)) for aseg in aseguradoras]

@api_router.post("/admin/aseguradoras", response_model=Aseguradora)
async def create_aseguradora(aseguradora: AseguradoraCreate, current_admin: UserResponse = Depends(require_admin)):
    """Create new aseguradora (admin only)"""
    new_aseguradora = Aseguradora(**aseguradora.dict())
    aseg_dict = prepare_for_mongo(new_aseguradora.dict())
    await db.aseguradoras.insert_one(aseg_dict)
    logging.info(f"Admin {current_admin.email} created aseguradora: {new_aseguradora.nombre}")
    return new_aseguradora

@api_router.get("/admin/aseguradoras/{aseguradora_id}", response_model=Aseguradora)
async def get_aseguradora(aseguradora_id: str, current_admin: UserResponse = Depends(require_admin)):
    """Get specific aseguradora (admin only)"""
    aseguradora = await db.aseguradoras.find_one({"id": aseguradora_id})
    if not aseguradora:
        raise HTTPException(status_code=404, detail="Aseguradora not found")
    return Aseguradora(**parse_from_mongo(aseguradora))

@api_router.put("/admin/aseguradoras/{aseguradora_id}", response_model=Aseguradora)
async def update_aseguradora(
    aseguradora_id: str,
    aseguradora_update: AseguradoraUpdate,
    current_admin: UserResponse = Depends(require_admin)
):
    """Update aseguradora (admin only)"""
    aseguradora = await db.aseguradoras.find_one({"id": aseguradora_id})
    if not aseguradora:
        raise HTTPException(status_code=404, detail="Aseguradora not found")
    
    # Update only provided fields
    update_data = {k: v for k, v in aseguradora_update.dict(exclude_unset=True).items() if v is not None}
    update_data["updated_at"] = datetime.now(GUATEMALA_TZ)
    update_dict = prepare_for_mongo(update_data)
    
    await db.aseguradoras.update_one(
        {"id": aseguradora_id},
        {"$set": update_dict}
    )
    
    # Fetch and return updated aseguradora
    updated_aseguradora = await db.aseguradoras.find_one({"id": aseguradora_id})
    logging.info(f"Admin {current_admin.email} updated aseguradora: {aseguradora_id}")
    return Aseguradora(**parse_from_mongo(updated_aseguradora))

@api_router.delete("/admin/aseguradoras/{aseguradora_id}")
async def delete_aseguradora(aseguradora_id: str, current_admin: UserResponse = Depends(require_admin)):
    """Delete aseguradora (admin only)"""
    result = await db.aseguradoras.delete_one({"id": aseguradora_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Aseguradora not found")
    
    logging.info(f"Admin {current_admin.email} deleted aseguradora: {aseguradora_id}")
    return {"message": "Aseguradora deleted successfully"}

# Cotización automática
@api_router.post("/admin/aseguradoras/cotizar", response_model=List[CotizacionResult])
async def cotizar_con_todas_aseguradoras(
    suma_asegurada: float,
    año_vehiculo: int,
    current_admin: UserResponse = Depends(require_admin)
):
    """
    Cotiza con todas las aseguradoras activas
    Calcula cuota mensual RC y Completo según las tasas configuradas
    Valida que el año del vehículo esté en el rango permitido por la aseguradora
    """
    aseguradoras = await db.aseguradoras.find({"activo": True}).to_list(length=None)
    
    if not aseguradoras:
        return []
    
    resultados = []
    
    for aseg_data in aseguradoras:
        aseguradora = Aseguradora(**parse_from_mongo(aseg_data))
        
        # Calcular cuota RC (usando prima neta fija)
        cuota_rc = 0.0
        if aseguradora.rc_año_desde <= año_vehiculo <= aseguradora.rc_año_hasta:
            cuota_rc = calcular_cuota_rc_fija(
                prima_neta=aseguradora.rc_prima_neta,
                gastos_emision=aseguradora.rc_gastos_emision,
                asistencia=aseguradora.rc_asistencia,
                iva=aseguradora.iva,
                cuotas=aseguradora.cuotas
            )
        
        # Calcular cuota Completo (usando tasas por rango)
        cuota_completo = 0.0
        if aseguradora.completo_año_desde <= año_vehiculo <= aseguradora.completo_año_hasta:
            cuota_completo = calcular_cuota_seguro(
                suma_asegurada=suma_asegurada,
                tasas=aseguradora.completo_tasas,
                gastos_emision=aseguradora.completo_gastos_emision,
                asistencia=aseguradora.completo_asistencia,
                iva=aseguradora.iva,
                cuotas=aseguradora.cuotas,
                prima_minima=aseguradora.completo_prima_minima
            )
        
        # Solo agregar si al menos uno de los seguros está disponible
        if cuota_rc > 0 or cuota_completo > 0:
            resultados.append(CotizacionResult(
                aseguradora=aseguradora.nombre,
                aseguradora_id=aseguradora.id,
                cuota_rc=round(cuota_rc, 2),
                cuota_completo=round(cuota_completo, 2)
            ))
    
    return resultados

# ========== VEHICULOS NO ASEGURABLES ROUTES ==========

@api_router.get("/admin/vehiculos-no-asegurables", response_model=List[VehiculoNoAsegurable])
async def get_vehiculos_no_asegurables(current_admin: UserResponse = Depends(require_admin)):
    """Get all non-insurable vehicles (admin only)"""
    vehiculos = await db.vehiculos_no_asegurables.find().to_list(length=None)
    return [VehiculoNoAsegurable(**parse_from_mongo(v)) for v in vehiculos]

@api_router.post("/admin/vehiculos-no-asegurables", response_model=VehiculoNoAsegurable)
async def create_vehiculo_no_asegurable(
    vehiculo: VehiculoNoAsegurableCreate,
    current_admin: UserResponse = Depends(require_admin)
):
    """Add a vehicle to the non-insurable list (admin only)"""
    new_vehiculo = VehiculoNoAsegurable(**vehiculo.dict())
    vehiculo_dict = prepare_for_mongo(new_vehiculo.dict())
    await db.vehiculos_no_asegurables.insert_one(vehiculo_dict)
    logging.info(f"Admin {current_admin.email} added non-insurable vehicle: {new_vehiculo.marca} {new_vehiculo.modelo}")
    return new_vehiculo

@api_router.delete("/admin/vehiculos-no-asegurables/{vehiculo_id}")
async def delete_vehiculo_no_asegurable(
    vehiculo_id: str,
    current_admin: UserResponse = Depends(require_admin)
):
    """Remove a vehicle from the non-insurable list (admin only)"""
    result = await db.vehiculos_no_asegurables.delete_one({"id": vehiculo_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    logging.info(f"Admin {current_admin.email} removed non-insurable vehicle: {vehiculo_id}")
    return {"message": "Vehicle removed from non-insurable list"}

@api_router.post("/admin/vehiculos-no-asegurables/verificar")
async def verificar_vehiculo_asegurable(
    marca: str,
    modelo: str,
    año: int,
    current_admin: UserResponse = Depends(require_admin)
):
    """
    Verifica si un vehículo es asegurable
    Retorna True si es asegurable, False si está en la lista de exclusión
    """
    # Buscar coincidencia exacta con año específico
    vehiculo = await db.vehiculos_no_asegurables.find_one({
        "marca": {"$regex": f"^{marca}$", "$options": "i"},
        "modelo": {"$regex": f"^{modelo}$", "$options": "i"},
        "año": año
    })
    
    if vehiculo:
        return {
            "asegurable": False,
            "razon": vehiculo.get("razon", "Vehículo no asegurable"),
            "vehiculo": VehiculoNoAsegurable(**parse_from_mongo(vehiculo))
        }
    
    # Buscar coincidencia sin año específico (aplica a todos los años)
    vehiculo_sin_año = await db.vehiculos_no_asegurables.find_one({
        "marca": {"$regex": f"^{marca}$", "$options": "i"},
        "modelo": {"$regex": f"^{modelo}$", "$options": "i"},
        "año": None
    })
    
    if vehiculo_sin_año:
        return {
            "asegurable": False,
            "razon": vehiculo_sin_año.get("razon", "Vehículo no asegurable"),
            "vehiculo": VehiculoNoAsegurable(**parse_from_mongo(vehiculo_sin_año))
        }
    
    return {"asegurable": True, "razon": None, "vehiculo": None}

# Subscription Plans Routes
@api_router.get("/admin/subscription-plans")
async def get_subscription_plans(current_admin: UserResponse = Depends(require_admin)):
    """Get all subscription plans (admin only)"""
    plans = await db.subscription_plans.find().to_list(length=None)
    return [SubscriptionPlan(**parse_from_mongo(plan)) for plan in plans]

@api_router.post("/admin/subscription-plans", response_model=SubscriptionPlan)
async def create_subscription_plan(plan: SubscriptionPlan, current_admin: UserResponse = Depends(require_admin)):
    """Create new subscription plan (admin only)"""
    plan_dict = prepare_for_mongo(plan.dict())
    await db.subscription_plans.insert_one(plan_dict)
    return plan

@api_router.put("/admin/subscription-plans/{plan_id}")
async def update_subscription_plan(plan_id: str, plan_data: Dict[str, Any], current_admin: UserResponse = Depends(require_admin)):
    """Update subscription plan (admin only)"""
    plan_data["updated_at"] = datetime.now(GUATEMALA_TZ)
    plan_dict = prepare_for_mongo(plan_data)
    
    result = await db.subscription_plans.update_one(
        {"id": plan_id},
        {"$set": plan_dict}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Subscription plan not found")
    return {"success": True}

# Manual Lead Creation
@api_router.post("/admin/leads", response_model=Lead)
async def create_manual_lead(lead_data: Dict[str, Any], current_admin: UserResponse = Depends(require_admin)):
    """Create manual lead (admin only)"""
    # Create or get user profile
    phone_number = lead_data.get("phone_number", "")
    if not phone_number:
        raise HTTPException(status_code=400, detail="Phone number is required")
    
    user = await get_or_create_user(phone_number)
    if lead_data.get("name"):
        user.name = lead_data["name"]
        user_dict = prepare_for_mongo(user.dict())
        await db.users.update_one({"id": user.id}, {"$set": user_dict})
    
    # Create lead with user_id
    lead = Lead(
        user_id=user.id,
        name=lead_data.get("name", ""),
        phone_number=phone_number,
        vehicle_make=lead_data.get("vehicle_make", ""),
        vehicle_model=lead_data.get("vehicle_model", ""),
        vehicle_year=lead_data.get("vehicle_year"),
        vehicle_value=lead_data.get("vehicle_value"),
        selected_insurer=lead_data.get("selected_insurer", ""),
        selected_quote_price=lead_data.get("selected_quote_price"),
        status=LeadStatus(lead_data.get("status", "PendingData"))
    )
    
    lead_dict = prepare_for_mongo(lead.dict())
    await db.leads.insert_one(lead_dict)
    return lead

@api_router.post("/admin/leads/{lead_id}/assign")
async def assign_lead_to_broker(lead_id: str, broker_id: str, current_admin: UserResponse = Depends(require_admin)):
    """Manually assign lead to specific broker (admin only)"""
    # Verify broker exists and is active
    broker = await db.brokers.find_one({"id": broker_id})
    if not broker:
        raise HTTPException(status_code=404, detail="Broker not found")
    
    if broker["subscription_status"] != BrokerSubscriptionStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Broker is not active")
    
    # Check broker quota
    if broker["current_month_leads"] >= broker["monthly_lead_quota"]:
        raise HTTPException(status_code=400, detail="Broker has reached monthly lead quota")
    
    # Update lead
    await db.leads.update_one(
        {"id": lead_id},
        {
            "$set": {
                "assigned_broker_id": broker_id,
                "status": LeadStatus.ASSIGNED_TO_BROKER,
                "broker_status": BrokerLeadStatus.NEW,
                "sla_first_contact_deadline": datetime.now(GUATEMALA_TZ) + timedelta(hours=2),
                "sla_reassignment_deadline": datetime.now(GUATEMALA_TZ) + timedelta(hours=4),
                "updated_at": datetime.now(GUATEMALA_TZ)
            }
        }
    )
    
    # Update broker lead count
    await db.brokers.update_one(
        {"id": broker_id},
        {"$inc": {"current_month_leads": 1}}
    )
    
    return {"success": True}

@api_router.post("/admin/leads/{lead_id}/assign-auto")
async def assign_lead_auto(lead_id: str, current_admin: UserResponse = Depends(require_admin)):
    """Automatically assign lead using round-robin (admin only)"""
    assigned_broker_id = await assign_broker_to_lead(lead_id)
    
    if not assigned_broker_id:
        raise HTTPException(status_code=400, detail="No available brokers for assignment")
    
    return {"success": True, "assigned_broker_id": assigned_broker_id}

# Admin Lead Management
@api_router.delete("/admin/leads/{lead_id}")
async def delete_lead(lead_id: str, current_admin: UserResponse = Depends(require_admin)):
    """Delete a specific lead (admin only)"""
    try:
        # Delete lead
        lead_result = await db.leads.delete_one({"id": lead_id})
        
        if lead_result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Delete associated interactions
        interactions_result = await db.interactions.delete_many({"lead_id": lead_id})
        
        logging.info(f"Admin {current_admin.email} deleted lead {lead_id} and {interactions_result.deleted_count} interactions")
        
        return {
            "message": "Lead deleted successfully",
            "lead_id": lead_id,
            "interactions_deleted": interactions_result.deleted_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting lead: {e}")
        raise HTTPException(status_code=500, detail="Error deleting lead")

@api_router.delete("/admin/leads")
async def delete_all_leads(current_admin: UserResponse = Depends(require_admin)):
    """Delete all leads and related data (admin only)"""
    try:
        # Count before deletion
        leads_count = await db.leads.count_documents({})
        interactions_count = await db.interactions.count_documents({})
        users_count = await db.users.count_documents({})
        
        # Delete all leads
        await db.leads.delete_many({})
        
        # Delete all interactions
        await db.interactions.delete_many({})
        
        # Delete all lead users (not auth users)
        await db.users.delete_many({})
        
        logging.info(f"Admin {current_admin.email} deleted ALL leads and data")
        
        return {
            "message": "All leads and related data deleted successfully",
            "deleted_counts": {
                "leads": leads_count,
                "interactions": interactions_count,
                "users": users_count
            }
        }
        
    except Exception as e:
        logging.error(f"Error deleting all leads: {e}")
        raise HTTPException(status_code=500, detail="Error deleting all leads")

@api_router.delete("/admin/leads/bulk")
async def delete_leads_bulk(lead_ids: List[str], current_admin: UserResponse = Depends(require_admin)):
    """Delete multiple leads (admin only)"""
    try:
        if not lead_ids:
            raise HTTPException(status_code=400, detail="No lead IDs provided")
        
        # Delete leads
        leads_result = await db.leads.delete_many({"id": {"$in": lead_ids}})
        
        # Delete associated interactions
        interactions_result = await db.interactions.delete_many({"lead_id": {"$in": lead_ids}})
        
        logging.info(f"Admin {current_admin.email} deleted {leads_result.deleted_count} leads in bulk")
        
        return {
            "message": f"Deleted {leads_result.deleted_count} leads successfully",
            "leads_deleted": leads_result.deleted_count,
            "interactions_deleted": interactions_result.deleted_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error bulk deleting leads: {e}")
        raise HTTPException(status_code=500, detail="Error bulk deleting leads")

# Insurance Rate Configuration Routes
@api_router.get("/admin/insurance-rates")
async def get_insurance_rates(current_admin: UserResponse = Depends(require_admin)):
    """Get all insurance rate configurations (admin only)"""
    rates = await db.insurance_rates.find().to_list(length=None)
    return [InsuranceRateConfig(**parse_from_mongo(rate)) for rate in rates]

@api_router.post("/admin/insurance-rates", response_model=InsuranceRateConfig)
async def create_insurance_rate(rate: InsuranceRateConfig, current_admin: UserResponse = Depends(require_admin)):
    """Create new insurance rate configuration (admin only)"""
    rate_dict = prepare_for_mongo(rate.dict())
    await db.insurance_rates.insert_one(rate_dict)
    return rate

@api_router.put("/admin/insurance-rates/{rate_id}")
async def update_insurance_rate(rate_id: str, rate_data: Dict[str, Any], current_admin: UserResponse = Depends(require_admin)):
    """Update insurance rate configuration (admin only)"""
    rate_data["updated_at"] = datetime.now(GUATEMALA_TZ)
    rate_dict = prepare_for_mongo(rate_data)
    
    result = await db.insurance_rates.update_one(
        {"id": rate_id},
        {"$set": rate_dict}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Insurance rate not found")
    return {"success": True}

# Broker Dashboard Analytics
@api_router.get("/admin/brokers-analytics")
async def get_brokers_analytics(current_admin: UserResponse = Depends(require_admin)):
    """Get analytics for all brokers (admin only)"""
    brokers = await db.brokers.find().to_list(length=None)
    analytics = []
    
    for broker in brokers:
        # Get leads for this broker
        leads = await db.leads.find({"assigned_broker_id": broker["id"]}).to_list(length=None)
        
        # Count by status
        status_counts = {
            "total": len(leads),
            "new": len([l for l in leads if l.get("broker_status") == BrokerLeadStatus.NEW]),
            "contacted": len([l for l in leads if l.get("broker_status") == BrokerLeadStatus.CONTACTED]),
            "interested": len([l for l in leads if l.get("broker_status") == BrokerLeadStatus.INTERESTED]),
            "negotiation": len([l for l in leads if l.get("broker_status") == BrokerLeadStatus.NEGOTIATION]),
            "closed_won": len([l for l in leads if l.get("broker_status") == BrokerLeadStatus.CLOSED_WON]),
            "closed_lost": len([l for l in leads if l.get("broker_status") == BrokerLeadStatus.CLOSED_LOST]),
            "not_interested": len([l for l in leads if l.get("broker_status") == BrokerLeadStatus.NOT_INTERESTED])
        }
        
        analytics.append({
            "broker_id": broker["id"],
            "broker_name": broker["name"],
            "corretaje_name": broker.get("corretaje_name", ""),
            "subscription_status": broker["subscription_status"],
            "leads_analytics": status_counts
        })
    
    return analytics

@api_router.put("/brokers/{broker_id}/subscription")
async def update_broker_subscription(broker_id: str, status: BrokerSubscriptionStatus, current_admin: UserResponse = Depends(require_admin)):
    """Update broker subscription status (admin only)"""
    result = await db.brokers.update_one(
        {"id": broker_id},
        {"$set": {"subscription_status": status, "updated_at": datetime.now(GUATEMALA_TZ)}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Broker not found")
    return {"success": True}

@api_router.delete("/brokers/{broker_id}")
async def delete_broker(broker_id: str, current_admin: UserResponse = Depends(require_admin)):
    """Delete broker (admin only)"""
    # Check if broker has active leads
    active_leads = await db.leads.find({"assigned_broker_id": broker_id}).to_list(length=1)
    if active_leads:
        raise HTTPException(status_code=400, detail="Cannot delete broker with assigned leads")
    
    result = await db.brokers.delete_one({"id": broker_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Broker not found")
    
    # Also delete associated auth user if exists
    broker_data = await db.brokers.find_one({"id": broker_id})
    if broker_data and broker_data.get("user_id"):
        await db.auth_users.delete_one({"id": broker_data["user_id"]})
    
    return {"success": True}

# Broker Payments Routes
@api_router.get("/admin/payments")
async def get_broker_payments(current_admin: UserResponse = Depends(require_admin)):
    """Get all broker payments (admin only)"""
    payments = await db.broker_payments.find().to_list(length=None)
    return [BrokerPayment(**parse_from_mongo(payment)) for payment in payments]

@api_router.post("/admin/payments")
async def create_broker_payment(payment: BrokerPayment, current_admin: UserResponse = Depends(require_admin)):
    """Create broker payment record (admin only)"""
    payment_dict = prepare_for_mongo(payment.dict())
    await db.broker_payments.insert_one(payment_dict)
    return payment

@api_router.put("/admin/payments/{payment_id}")
async def update_broker_payment(payment_id: str, payment_data: Dict[str, Any], current_admin: UserResponse = Depends(require_admin)):
    """Update broker payment (admin only)"""
    if payment_data.get("status") == PaymentStatus.PAID:
        payment_data["paid_date"] = datetime.now(GUATEMALA_TZ)
    
    payment_dict = prepare_for_mongo(payment_data)
    
    result = await db.broker_payments.update_one(
        {"id": payment_id},
        {"$set": payment_dict}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Payment not found")
    return {"success": True}

# File Upload Routes
@api_router.post("/upload/profile-photo/{broker_id}")
async def upload_profile_photo(broker_id: str, file: UploadFile = File(...), current_user: UserResponse = Depends(get_current_user)):
    """Upload profile photo for broker"""
    # Check file size (4MB limit)
    if file.size > 4 * 1024 * 1024:  # 4MB
        raise HTTPException(status_code=400, detail="File size too large. Maximum 4MB allowed.")
    
    # Check file type
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPG and PNG allowed.")
    
    # Create uploads directory if it doesn't exist
    upload_dir = Path("/app/uploads/profile_photos")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{broker_id}_{uuid.uuid4().hex[:8]}.{file_extension}"
    file_path = upload_dir / unique_filename
    
    # Save file
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Update broker profile with photo URL
    photo_url = f"/uploads/profile_photos/{unique_filename}"
    await db.brokers.update_one(
        {"id": broker_id},
        {"$set": {"profile_photo_url": photo_url, "updated_at": datetime.now(GUATEMALA_TZ)}}
    )
    
    return {"success": True, "photo_url": photo_url}

# Broker Accounts Routes
@api_router.get("/admin/accounts", response_model=List[BrokerAccount])
async def get_all_broker_accounts(current_admin: UserResponse = Depends(require_admin)):
    """Get all broker accounts (admin only)"""
    accounts = await db.broker_accounts.find().to_list(length=None)
    return [BrokerAccount(**parse_from_mongo(account)) for account in accounts]

@api_router.get("/admin/accounts/{broker_id}")
async def get_broker_account(broker_id: str, current_admin: UserResponse = Depends(require_admin)):
    """Get specific broker account (admin only)"""
    account = await db.broker_accounts.find_one({"broker_id": broker_id})
    if not account:
        raise HTTPException(status_code=404, detail="Broker account not found")
    
    return BrokerAccount(**parse_from_mongo(account))

@api_router.get("/admin/transactions/{account_id}")
async def get_account_transactions(account_id: str, current_admin: UserResponse = Depends(require_admin)):
    """Get transactions for specific account (admin only)"""
    transactions = await db.broker_transactions.find({"account_id": account_id}).sort([("created_at", -1)]).to_list(length=None)
    return [BrokerTransaction(**parse_from_mongo(transaction)) for transaction in transactions]

class PaymentApplication(BaseModel):
    amount: float
    reference_number: Optional[str] = None
    description: Optional[str] = None

class PaymentDeletion(BaseModel):
    authorization_code: str

@api_router.post("/admin/accounts/{broker_id}/apply-payment")
async def apply_payment(broker_id: str, payment: PaymentApplication, current_admin: UserResponse = Depends(require_admin)):
    """Apply manual payment to broker account (admin only)"""
    # Get broker account
    account = await db.broker_accounts.find_one({"broker_id": broker_id})
    if not account:
        raise HTTPException(status_code=404, detail="Broker account not found")
    
    account_obj = BrokerAccount(**parse_from_mongo(account))
    
    # Calculate new balance
    new_balance = account_obj.current_balance + payment.amount
    
    # Update account
    update_data = {
        "current_balance": new_balance,
        "updated_at": datetime.now(GUATEMALA_TZ)
    }
    
    # If payment covers debt, reactivate account
    if account_obj.current_balance < 0 and new_balance >= 0:
        update_data["account_status"] = AccountStatus.ACTIVE
        update_data["grace_period_end"] = None
        
        # Reactivate broker
        await db.brokers.update_one(
            {"id": broker_id},
            {"$set": {"subscription_status": BrokerSubscriptionStatus.ACTIVE}}
        )
        
        # Reactivate user
        broker = await db.brokers.find_one({"id": broker_id})
        if broker and broker.get("user_id"):
            await db.auth_users.update_one(
                {"id": broker["user_id"]},
                {"$set": {"active": True}}
            )
    
    await db.broker_accounts.update_one(
        {"broker_id": broker_id},
        {"$set": update_data}
    )
    
    # Create payment transaction
    transaction = BrokerTransaction(
        account_id=account_obj.id,
        broker_id=broker_id,
        transaction_type=TransactionType.PAYMENT,
        amount=payment.amount,
        description=payment.description or f"Pago aplicado - Ref: {payment.reference_number}",
        reference_number=payment.reference_number,
        balance_after=new_balance,
        created_by=current_admin.id
    )
    
    transaction_dict = prepare_for_mongo(transaction.dict())
    await db.broker_transactions.insert_one(transaction_dict)
    
    # Send confirmation WhatsApp
    broker = await db.brokers.find_one({"id": broker_id})
    if broker:
        message = f"""
✅ *ProtegeYa - Pago Aplicado*

Estimado {broker['name']},

Se ha aplicado un pago por Q{payment.amount:,.2f} a su cuenta.

Balance actual: Q{new_balance:,.2f}

Referencia: {payment.reference_number or 'N/A'}

¡Gracias por su pago!
        """.strip()
        
        await send_whatsapp_message(broker["whatsapp_number"], message)
    
    return {"success": True, "new_balance": new_balance}

@api_router.post("/admin/accounts/generate-charges")
async def manual_generate_charges(current_admin: UserResponse = Depends(require_admin)):
    """Manually generate monthly charges (admin only)"""
    await generate_monthly_charges(force_manual=True)
    return {"success": True, "message": "Monthly charges generated"}

@api_router.post("/admin/accounts/check-overdue")
async def manual_check_overdue(current_admin: UserResponse = Depends(require_admin)):
    """Manually check overdue accounts (admin only)"""
    await check_overdue_accounts()
    return {"success": True, "message": "Overdue accounts checked"}

@api_router.delete("/admin/transactions/{transaction_id}")
async def delete_transaction(transaction_id: str, deletion_data: PaymentDeletion, current_admin: UserResponse = Depends(require_admin)):
    """Delete any transaction (payment, charge, or adjustment) with authorization code (admin only)"""
    # Verify authorization code
    if deletion_data.authorization_code != "ProtegeYa123#":
        raise HTTPException(status_code=403, detail="Código de autorización incorrecto")
    
    # Get transaction
    transaction = await db.broker_transactions.find_one({"id": transaction_id})
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Get account to update balance
    account = await db.broker_accounts.find_one({"id": transaction["account_id"]})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Calculate new balance by reversing the transaction
    transaction_amount = transaction["amount"]  # Positive for payments, negative for charges
    new_balance = account["current_balance"] - transaction_amount
    
    # Check if account needs to be suspended after removing transaction
    account_status = account["account_status"]
    if new_balance < 0 and account_status == AccountStatus.ACTIVE:
        # If balance becomes negative, put in grace period
        grace_end = datetime.now(GUATEMALA_TZ) + timedelta(days=5)
        account_status = AccountStatus.GRACE_PERIOD
        
        # Update account with new status
        await db.broker_accounts.update_one(
            {"id": account["id"]},
            {
                "$set": {
                    "current_balance": new_balance,
                    "account_status": account_status,
                    "grace_period_end": grace_end,
                    "updated_at": datetime.now(GUATEMALA_TZ)
                }
            }
        )
    else:
        # Just update balance
        await db.broker_accounts.update_one(
            {"id": account["id"]},
            {
                "$set": {
                    "current_balance": new_balance,
                    "updated_at": datetime.now(GUATEMALA_TZ)
                }
            }
        )
    
    # Delete the transaction
    await db.broker_transactions.delete_one({"id": transaction_id})
    
    # Get broker info for notification
    broker = await db.brokers.find_one({"id": transaction["broker_id"]})
    
    # Send WhatsApp notification about transaction deletion
    if broker:
        transaction_type_text = {
            TransactionType.PAYMENT: "pago",
            TransactionType.CHARGE: "cargo",
            TransactionType.ADJUSTMENT: "ajuste"
        }.get(transaction["transaction_type"], "transacción")
        
        message = f"""
⚠️ *ProtegeYa - Transacción Eliminada*

Estimado {broker['name']},

Se ha eliminado un {transaction_type_text} de Q{abs(transaction_amount):,.2f} de su cuenta.

Referencia eliminada: {transaction.get('reference_number', 'N/A')}

Balance actual: Q{new_balance:,.2f}

Si tiene preguntas, contacte al administrador.
        """.strip()
        
        await send_whatsapp_message(broker["whatsapp_number"], message)
    
    return {
        "success": True, 
        "message": "Transacción eliminada exitosamente",
        "new_balance": new_balance,
        "deleted_amount": abs(transaction_amount)
    }

# Current user account access
@api_router.get("/my-account")
async def get_my_account(current_user: UserResponse = Depends(get_current_user)):
    """Get current user's account information"""
    if current_user.role != UserRole.BROKER:
        raise HTTPException(status_code=403, detail="Only brokers can access account information")
    
    # Get broker profile
    broker = await db.brokers.find_one({"user_id": current_user.id})
    if not broker:
        raise HTTPException(status_code=404, detail="Broker profile not found")
    
    # Get account
    account = await db.broker_accounts.find_one({"broker_id": broker["id"]})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return BrokerAccount(**parse_from_mongo(account))

@api_router.get("/my-transactions")
async def get_my_transactions(current_user: UserResponse = Depends(get_current_user)):
    """Get current user's transaction history"""
    if current_user.role != UserRole.BROKER:
        raise HTTPException(status_code=403, detail="Only brokers can access transaction information")
    
    # Get broker profile
    broker = await db.brokers.find_one({"user_id": current_user.id})
    if not broker:
        raise HTTPException(status_code=404, detail="Broker profile not found")
    
    # Get account
    account = await db.broker_accounts.find_one({"broker_id": broker["id"]})
    if not account:
        return []
    
    # Get transactions
    transactions = await db.broker_transactions.find({"account_id": account["id"]}).sort([("created_at", -1)]).to_list(length=None)
    return [BrokerTransaction(**parse_from_mongo(transaction)) for transaction in transactions]

# Configuration Routes
@api_router.get("/admin/configuration")
async def get_configuration(current_admin: UserResponse = Depends(require_admin)):
    """Get system configuration (admin only)"""
    config = await db.system_config.find_one({})
    if not config:
        # Create default config
        default_config = SystemConfiguration()
        config_dict = prepare_for_mongo(default_config.dict())
        await db.system_config.insert_one(config_dict)
        return default_config
    
    config = parse_from_mongo(config)
    return SystemConfiguration(**config)

@api_router.put("/admin/configuration")
async def update_configuration(config_update: ConfigurationUpdate, current_admin: UserResponse = Depends(require_admin)):
    """Update system configuration (admin only)"""
    update_data = {k: v for k, v in config_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now(GUATEMALA_TZ)
    
    config_dict = prepare_for_mongo(update_data)
    
    result = await db.system_config.update_one(
        {},
        {"$set": config_dict},
        upsert=True
    )
    return {"success": True}

# Reports and Analytics
@api_router.get("/reports/kpi")
async def get_kpi_report(current_user: UserResponse = Depends(get_current_user)):
    """Get KPI dashboard data"""
    if current_user.role == UserRole.BROKER:
        # Broker-specific KPIs
        broker = await db.brokers.find_one({"user_id": current_user.id})
        if not broker:
            return {"error": "Broker profile not found"}
        
        total_leads = await db.leads.count_documents({"assigned_broker_id": broker["id"]})
        closed_won = await db.leads.count_documents({
            "assigned_broker_id": broker["id"],
            "broker_status": BrokerLeadStatus.CLOSED_WON
        })
        
        return {
            "total_assigned_leads": total_leads,
            "closed_won_deals": closed_won,
            "total_revenue": broker.get("total_revenue", 0.0),
            "current_month_quota": broker.get("monthly_lead_quota", 50),
            "current_month_leads": broker.get("current_month_leads", 0),
            "conversion_rate": round((closed_won / max(total_leads, 1)) * 100, 1),
            "generated_at": datetime.now(GUATEMALA_TZ).isoformat()
        }
    
    # Admin KPIs
    total_leads = await db.leads.count_documents({})
    assigned_leads = await db.leads.count_documents({"status": LeadStatus.ASSIGNED_TO_BROKER})
    active_brokers = await db.brokers.count_documents({"subscription_status": BrokerSubscriptionStatus.ACTIVE})
    closed_won = await db.leads.count_documents({"broker_status": BrokerLeadStatus.CLOSED_WON})
    
    # Calculate revenue from closed deals
    total_revenue = 0.0
    closed_leads = await db.leads.find({"broker_status": BrokerLeadStatus.CLOSED_WON}).to_list(length=None)
    for lead in closed_leads:
        if lead.get("closed_amount"):
            total_revenue += lead["closed_amount"]
    
    # Calculate monthly subscription revenue
    current_month = datetime.now(GUATEMALA_TZ).month
    current_year = datetime.now(GUATEMALA_TZ).year
    
    # Get all subscription charges for current month
    # Since created_at is stored as ISO string, we need to convert it first
    monthly_charges = await db.broker_transactions.find({
        "transaction_type": TransactionType.CHARGE,
        "$expr": {
            "$and": [
                {"$eq": [{"$month": {"$dateFromString": {"dateString": "$created_at"}}}, current_month]},
                {"$eq": [{"$year": {"$dateFromString": {"dateString": "$created_at"}}}, current_year]}
            ]
        }
    }).to_list(length=None)
    
    monthly_subscription_revenue = 0.0
    for charge in monthly_charges:
        # Charges are negative amounts, so we negate to get positive revenue
        monthly_subscription_revenue += abs(charge.get("amount", 0.0))
    
    # Calculate total collected payments (not just charges)
    # Since created_at is stored as ISO string, we need to convert it first
    monthly_payments = await db.broker_transactions.find({
        "transaction_type": TransactionType.PAYMENT,
        "$expr": {
            "$and": [
                {"$eq": [{"$month": {"$dateFromString": {"dateString": "$created_at"}}}, current_month]},
                {"$eq": [{"$year": {"$dateFromString": {"dateString": "$created_at"}}}, current_year]}
            ]
        }
    }).to_list(length=None)
    
    monthly_collected_revenue = 0.0
    for payment in monthly_payments:
        monthly_collected_revenue += payment.get("amount", 0.0)
    
    return {
        "total_leads": total_leads,
        "assigned_leads": assigned_leads,
        "active_brokers": active_brokers,
        "closed_won_deals": closed_won,
        "total_revenue": total_revenue,
        "monthly_subscription_revenue": monthly_subscription_revenue,
        "monthly_collected_revenue": monthly_collected_revenue,
        "assignment_rate": round((assigned_leads / max(total_leads, 1)) * 100, 1),
        "conversion_rate": round((closed_won / max(assigned_leads, 1)) * 100, 1),
        "average_deal_size": round(total_revenue / max(closed_won, 1), 2),
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

import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Initialize scheduler
scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def startup_event():
    """Initialize services, configuration, and database on startup"""
    try:
        # Initialize UltraMSG configuration from environment
        await initialize_ultramsg_config()
        
        # Check if admin user exists
        admin_exists = await db.auth_users.find_one({"role": UserRole.ADMIN})
        
        if not admin_exists:
            # Create default admin
            default_admin = {
                "id": str(uuid.uuid4()),
                "email": "admin@protegeya.com",
                "password": hash_password("admin123"),
                "name": "Administrador ProtegeYa",
                "role": UserRole.ADMIN,
                "active": True,
                "created_at": datetime.now(GUATEMALA_TZ)
            }
            
            admin_dict = prepare_for_mongo(default_admin)
            await db.auth_users.insert_one(admin_dict)
            
            print("✅ Default admin user created:")
            print("   Email: admin@protegeya.com")
            print("   Password: admin123")
        
        # Check if broker user exists
        broker_exists = await db.auth_users.find_one({"role": UserRole.BROKER})
        
        if not broker_exists:
            # Create default broker user
            default_broker_user = {
                "id": str(uuid.uuid4()),
                "email": "corredor@protegeya.com", 
                "password": hash_password("corredor123"),
                "name": "Juan Carlos Pérez",
                "role": UserRole.BROKER,
                "active": True,
                "created_at": datetime.now(GUATEMALA_TZ)
            }
            
            broker_user_dict = prepare_for_mongo(default_broker_user)
            await db.auth_users.insert_one(broker_user_dict)
            
            # Create broker profile
            default_broker_profile = {
                "id": str(uuid.uuid4()),
                "user_id": default_broker_user["id"],
                "name": "Juan Carlos Pérez",
                "email": "corredor@protegeya.com",
                "phone_number": "+502-1234-5678",
                "whatsapp_number": "+502-1234-5678",
                "corretaje_name": "Seguros Pérez & Asociados",
                "subscription_status": BrokerSubscriptionStatus.ACTIVE,
                "monthly_lead_quota": 50,
                "current_month_leads": 0,
                "commission_percentage": 10.0,
                "total_closed_deals": 0,
                "total_revenue": 0.0,
                "created_at": datetime.now(GUATEMALA_TZ),
                "updated_at": datetime.now(GUATEMALA_TZ)
            }
            
            broker_profile_dict = prepare_for_mongo(default_broker_profile)
            await db.brokers.insert_one(broker_profile_dict)
            
            print("✅ Default broker user created:")
            print("   Email: corredor@protegeya.com")
            print("   Password: corredor123")
        
        # Fix data integrity: ensure all broker auth_users have corresponding broker profiles
        broker_auth_users = await db.auth_users.find({"role": UserRole.BROKER}).to_list(length=None)
        for broker_user in broker_auth_users:
            # Check if broker profile exists (avoid duplicates by checking user_id)
            existing_broker = await db.brokers.find_one({"user_id": broker_user["id"]})
            
            if not existing_broker:
                # Create missing broker profile only if it doesn't exist
                missing_broker_profile = {
                    "id": str(uuid.uuid4()),
                    "user_id": broker_user["id"],
                    "name": broker_user.get("name", "Corredor Sin Nombre"),
                    "email": broker_user.get("email", ""),
                    "phone_number": "",
                    "whatsapp_number": "",
                    "corretaje_name": f"Corretaje {broker_user.get('name', 'Desconocido')}",
                    "subscription_status": BrokerSubscriptionStatus.ACTIVE if broker_user.get("active", True) else BrokerSubscriptionStatus.INACTIVE,
                    "monthly_lead_quota": 50,
                    "current_month_leads": 0,
                    "commission_percentage": 10.0,
                    "total_closed_deals": 0,
                    "total_revenue": 0.0,
                    "created_at": datetime.now(GUATEMALA_TZ),
                    "updated_at": datetime.now(GUATEMALA_TZ)
                }
                
                broker_profile_dict = prepare_for_mongo(missing_broker_profile)
                await db.brokers.insert_one(broker_profile_dict)
                
                print(f"✅ Created missing broker profile for: {broker_user.get('name', 'Unknown')}")
            else:
                # Update existing broker's active status based on auth user status
                current_status = BrokerSubscriptionStatus.ACTIVE if broker_user.get("active", True) else BrokerSubscriptionStatus.INACTIVE
                if existing_broker.get("subscription_status") != current_status:
                    await db.brokers.update_one(
                        {"id": existing_broker["id"]},
                        {"$set": {"subscription_status": current_status, "updated_at": datetime.now(GUATEMALA_TZ)}}
                    )
                    print(f"✅ Updated broker status for: {broker_user.get('name', 'Unknown')} to {current_status}")
        
        # Create default subscription plan
        plan_exists = await db.subscription_plans.find_one({"name": "Plan Básico ProtegeYa"})
        
        if not plan_exists:
            default_plan = {
                "id": str(uuid.uuid4()),
                "name": "Plan Básico ProtegeYa",
                "amount": 500.00,
                "currency": "GTQ", 
                "period": "monthly",
                "benefits": [
                    "Acceso al panel de corredores",
                    "Hasta 50 leads por mes",
                    "Soporte técnico básico",
                    "Reportes mensuales",
                    "WhatsApp integration"
                ],
                "active": True,
                "created_at": datetime.now(GUATEMALA_TZ),
                "updated_at": datetime.now(GUATEMALA_TZ)
            }
            
            plan_dict = prepare_for_mongo(default_plan)
            await db.subscription_plans.insert_one(plan_dict)
            
            print("✅ Default subscription plan created")
            print("   Plan: Plan Básico ProtegeYa - Q500/mes")
        
        # Schedule automated tasks
        # Generate monthly charges on 1st of each month at 2:00 AM
        scheduler.add_job(
            generate_monthly_charges,
            CronTrigger(day=1, hour=2, minute=0),
            id="generate_monthly_charges"
        )
        
        # Check overdue accounts daily at 9:00 AM
        scheduler.add_job(
            check_overdue_accounts,
            CronTrigger(hour=9, minute=0),
            id="check_overdue_accounts"
        )
        
        # Start scheduler
        scheduler.start()
        print("✅ Automated billing tasks scheduled")
        print("✅ UltraMSG integration ready")
            
    except Exception as e:
        print(f"❌ Error during startup: {e}")
        logging.error(f"Startup error: {e}")

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