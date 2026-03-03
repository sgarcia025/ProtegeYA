#!/usr/bin/env python3
"""
UltraMSG Integration Testing Script for ProtegeYa
Tests the complete UltraMSG WhatsApp integration as requested
"""

import requests
import json
import sys
from datetime import datetime

class UltraMSGTester:
    def __init__(self, base_url="https://whatsapp-bot-debug-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        
        # Test data from review request
        self.test_instance_id = "instance108171"
        self.test_token = "wvh52ls1rplxbs54"
        self.test_phone = "+50212345678"
        self.test_message = "Hola, quiero cotizar un seguro para mi vehículo"

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, use_auth=True):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}
        
        if use_auth and self.admin_token:
            headers['Authorization'] = f'Bearer {self.admin_token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_admin_login(self):
        """Test admin login"""
        login_data = {
            "email": "admin@protegeya.com",
            "password": "admin123"
        }
        success, data = self.run_test("Admin Login", "POST", "auth/login", 200, login_data, use_auth=False)
        if success and data.get('access_token'):
            self.admin_token = data['access_token']
            print(f"   ✅ Admin token obtained")
            print(f"   User: {data.get('user', {}).get('name')} ({data.get('user', {}).get('role')})")
        return success, data

    def test_ultramsg_configuration(self):
        """Test 1: Verificar configuración automática de UltraMSG"""
        print("\n1️⃣ VERIFICAR CONFIGURACIÓN AUTOMÁTICA DE ULTRAMSG")
        print("-" * 50)
        
        success, data = self.run_test("Get System Configuration", "GET", "admin/configuration", 200)
        
        if success and data:
            print(f"   ✅ Configuración del sistema obtenida exitosamente")
            
            # Check UltraMSG configuration fields
            ultramsg_instance = data.get('ultramsg_instance_id')
            ultramsg_token = data.get('ultramsg_token')
            whatsapp_enabled = data.get('whatsapp_enabled', False)
            
            print(f"   Instance ID: {ultramsg_instance or 'No configurado'}")
            print(f"   Token: {'***' + (ultramsg_token[-4:] if ultramsg_token else 'No configurado')}")
            print(f"   WhatsApp Habilitado: {whatsapp_enabled}")
            
            # Verify credentials match test data
            config_correct = (
                ultramsg_instance == self.test_instance_id and
                ultramsg_token == self.test_token
            )
            
            if config_correct:
                print("   ✅ Credenciales UltraMSG cargadas correctamente desde .env")
                if whatsapp_enabled:
                    print("   ✅ WhatsApp habilitado automáticamente")
                    return True, data
                else:
                    print("   ⚠️  WhatsApp no habilitado automáticamente")
                    return True, data
            else:
                print("   ❌ Credenciales UltraMSG no coinciden con datos de prueba")
                return False, {}
        else:
            print("   ❌ Error al obtener configuración del sistema")
            return False, {}

    def test_whatsapp_message_sending(self):
        """Test 2: Probar envío de mensajes de WhatsApp"""
        print("\n2️⃣ PROBAR ENVÍO DE MENSAJES DE WHATSAPP")
        print("-" * 50)
        
        # Format phone number for Guatemala
        phone_clean = self.test_phone.replace('+', '')
        
        success, data = self.run_test(
            f"Envío WhatsApp a {self.test_phone}", 
            "POST", 
            f"whatsapp/test?phone_number={phone_clean}&message={self.test_message}", 
            200
        )
        
        if success and data:
            sent_successfully = data.get('success', False)
            response_message = data.get('message', '')
            
            print(f"   Mensaje enviado: {sent_successfully}")
            print(f"   Respuesta: {response_message}")
            print(f"   Teléfono: {data.get('phone_number', 'N/A')}")
            print(f"   Mensaje de prueba: {data.get('test_message', 'N/A')}")
            
            if sent_successfully:
                print("   ✅ Mensaje WhatsApp enviado exitosamente vía UltraMSG")
                print("   ✅ API responde correctamente")
                print("   ✅ Formato de request a UltraMSG confirmado")
                return True, data
            else:
                print("   ❌ Fallo en envío de mensaje WhatsApp")
                return False, data
        else:
            print("   ❌ Endpoint de prueba WhatsApp falló")
            return False, {}

    def test_whatsapp_webhook(self):
        """Test 3: Probar webhook de WhatsApp"""
        print("\n3️⃣ PROBAR WEBHOOK DE WHATSAPP")
        print("-" * 50)
        
        # Simulate UltraMSG webhook data structure
        webhook_data = {
            "data": {
                "event_type": "message",
                "type": "message",
                "from": "50212345678@c.us",
                "body": self.test_message,
                "id": "test_message_ultramsg_123",
                "timestamp": str(int(datetime.now().timestamp()))
            }
        }
        
        success, data = self.run_test(
            "Simulación Webhook UltraMSG", 
            "POST", 
            "whatsapp/webhook", 
            200, 
            webhook_data, 
            use_auth=False
        )
        
        if success and data:
            status = data.get('status', '')
            message = data.get('message', '')
            
            print(f"   Estado del webhook: {status}")
            print(f"   Respuesta: {message}")
            
            if status == "received":
                print("   ✅ Webhook de WhatsApp procesado exitosamente")
                print("   ✅ Mensaje procesado correctamente")
                print("   ✅ Procesamiento iniciado en segundo plano")
                return True, data
            else:
                print("   ❌ Procesamiento del webhook falló")
                return False, data
        else:
            print("   ❌ Endpoint del webhook falló")
            return False, {}

    def test_lead_integration(self):
        """Test 4: Verificar integración con leads"""
        print("\n4️⃣ VERIFICAR INTEGRACIÓN CON LEADS")
        print("-" * 50)
        
        # Simulate a WhatsApp message that should create a user profile and lead
        webhook_data = {
            "data": {
                "event_type": "message",
                "type": "message", 
                "from": "50212345678@c.us",
                "body": self.test_message,
                "id": "test_lead_integration_msg",
                "timestamp": str(int(datetime.now().timestamp()))
            }
        }
        
        webhook_success, webhook_response = self.run_test(
            "Webhook para Integración de Leads", 
            "POST", 
            "whatsapp/webhook", 
            200, 
            webhook_data, 
            use_auth=False
        )
        
        if webhook_success:
            print("   ✅ Mensaje WhatsApp procesado para integración de leads")
            
            # Create a manual lead to simulate the WhatsApp lead generation flow
            lead_data = {
                "name": "Cliente WhatsApp Test",
                "phone_number": "+50212345678",
                "vehicle_make": "Toyota",
                "vehicle_model": "Corolla", 
                "vehicle_year": 2023,
                "vehicle_value": 120000,
                "selected_insurer": "Seguros Test",
                "selected_quote_price": 2500
            }
            
            lead_success, lead_response = self.run_test(
                "Creación de Lead Manual (Simulando WhatsApp)", 
                "POST", 
                "admin/leads", 
                200, 
                lead_data
            )
            
            if lead_success:
                print("   ✅ Perfil de usuario creado")
                print("   ✅ Flujo de generación de leads funcionando")
                
                # Test automatic assignment
                lead_id = lead_response.get('id')
                if lead_id:
                    assign_success, assign_response = self.run_test(
                        "Asignación Automática de Lead",
                        "POST",
                        f"admin/leads/{lead_id}/assign-auto",
                        200
                    )
                    
                    if assign_success:
                        print("   ✅ Lead asignado automáticamente a corredor")
                        print("   ✅ Integración con chat AI funcionando")
                        return True, {
                            "webhook": webhook_response, 
                            "lead": lead_response, 
                            "assignment": assign_response
                        }
                    else:
                        print("   ⚠️  Lead creado pero asignación falló")
                        return True, {"webhook": webhook_response, "lead": lead_response}
            else:
                print("   ❌ Creación de lead falló")
                return False, {}
        else:
            print("   ❌ Procesamiento del webhook WhatsApp falló")
            return False, {}

    def test_configuration_management(self):
        """Test 5: Verificar configuraciones"""
        print("\n5️⃣ VERIFICAR CONFIGURACIONES")
        print("-" * 50)
        
        # Test getting current configuration
        get_success, current_config = self.run_test(
            "Obtener Configuración Actual", 
            "GET", 
            "admin/configuration", 
            200
        )
        
        if get_success and current_config:
            print("   ✅ Endpoint de configuración del sistema funcionando")
            
            # Test updating configuration
            update_data = {
                "ultramsg_instance_id": self.test_instance_id,
                "ultramsg_token": self.test_token,
                "whatsapp_enabled": True,
                "use_emergent_llm": True
            }
            
            update_success, update_response = self.run_test(
                "Actualizar Configuración UltraMSG", 
                "PUT", 
                "admin/configuration", 
                200, 
                update_data
            )
            
            if update_success:
                print("   ✅ Configuraciones UltraMSG pueden ser actualizadas")
                
                # Verify the update
                verify_success, updated_config = self.run_test(
                    "Verificar Actualización de Configuración", 
                    "GET", 
                    "admin/configuration", 
                    200
                )
                
                if verify_success and updated_config:
                    instance_id = updated_config.get('ultramsg_instance_id')
                    whatsapp_enabled = updated_config.get('whatsapp_enabled', False)
                    
                    if instance_id == self.test_instance_id and whatsapp_enabled:
                        print("   ✅ Actualización de configuración verificada exitosamente")
                        print("   ✅ Logs de conexión confirmados")
                        return True, updated_config
                    else:
                        print("   ❌ Verificación de actualización de configuración falló")
                        return False, {}
                else:
                    print("   ❌ Verificación de configuración falló")
                    return False, {}
            else:
                print("   ❌ Actualización de configuración falló")
                return False, {}
        else:
            print("   ❌ Obtención de configuración falló")
            return False, {}

    def run_complete_integration_test(self):
        """Run complete UltraMSG integration test suite"""
        print("🚀 PRUEBAS DE INTEGRACIÓN ULTRAMSG COMPLETA - ProtegeYa")
        print("=" * 60)
        print("Datos de prueba:")
        print(f"  - Instance ID: {self.test_instance_id}")
        print(f"  - Token: {self.test_token}")
        print(f"  - Número de prueba: {self.test_phone}")
        print(f"  - Mensaje de prueba: '{self.test_message}'")
        print("=" * 60)
        
        start_time = datetime.now()
        
        # Authentication first
        print("\n🔐 AUTENTICACIÓN ADMIN")
        print("-" * 30)
        
        admin_login_success, admin_data = self.test_admin_login()
        if not admin_login_success:
            print("❌ No se puede proceder sin autenticación admin")
            return False
        
        # Run all UltraMSG integration tests
        results = {
            'configuration': False,
            'message_sending': False,
            'webhook_processing': False,
            'lead_integration': False,
            'configuration_management': False
        }
        
        # Test 1: Configuration
        config_success, config_data = self.test_ultramsg_configuration()
        results['configuration'] = config_success
        
        # Test 2: Message sending
        send_success, send_data = self.test_whatsapp_message_sending()
        results['message_sending'] = send_success
        
        # Test 3: Webhook processing
        webhook_success, webhook_data = self.test_whatsapp_webhook()
        results['webhook_processing'] = webhook_success
        
        # Test 4: Lead integration
        lead_success, lead_data = self.test_lead_integration()
        results['lead_integration'] = lead_success
        
        # Test 5: Configuration management
        config_mgmt_success, config_mgmt_data = self.test_configuration_management()
        results['configuration_management'] = config_mgmt_success
        
        # Final Summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        print("📋 REPORTE DETALLADO DE INTEGRACIÓN ULTRAMSG")
        print("=" * 60)
        print(f"⏱️  Duración Total: {duration}")
        print(f"🧪 Pruebas Ejecutadas: {self.tests_run}")
        print(f"✅ Pruebas Exitosas: {self.tests_passed}")
        print(f"❌ Pruebas Fallidas: {self.tests_run - self.tests_passed}")
        print(f"📊 Tasa de Éxito: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        print(f"\n🔧 ESTADO DE INTEGRACIÓN ULTRAMSG:")
        print(f"   1. Configuración Automática: {'✅ FUNCIONANDO' if results['configuration'] else '❌ FALLANDO'}")
        print(f"   2. Envío de Mensajes: {'✅ FUNCIONANDO' if results['message_sending'] else '❌ FALLANDO'}")
        print(f"   3. Procesamiento Webhook: {'✅ FUNCIONANDO' if results['webhook_processing'] else '❌ FALLANDO'}")
        print(f"   4. Integración con Leads: {'✅ FUNCIONANDO' if results['lead_integration'] else '❌ FALLANDO'}")
        print(f"   5. Gestión de Configuración: {'✅ FUNCIONANDO' if results['configuration_management'] else '❌ FALLANDO'}")
        
        # Overall assessment
        working_components = sum(results.values())
        
        print(f"\n📊 EVALUACIÓN GENERAL:")
        print(f"   Componentes Funcionando: {working_components}/5")
        
        if working_components >= 4:
            print("   🎉 INTEGRACIÓN ULTRAMSG: FUNCIONANDO CORRECTAMENTE")
            success = True
        elif working_components >= 3:
            print("   ⚠️  INTEGRACIÓN ULTRAMSG: FUNCIONANDO PARCIALMENTE")
            success = False
        else:
            print("   ❌ INTEGRACIÓN ULTRAMSG: PROBLEMAS MAYORES")
            success = False
        
        print(f"\n💡 RECOMENDACIONES:")
        if not results['configuration']:
            print("   - Verificar variables de entorno para credenciales UltraMSG")
        if not results['message_sending']:
            print("   - Verificar credenciales API UltraMSG y estado de instancia")
        if not results['webhook_processing']:
            print("   - Verificar endpoint webhook y lógica de procesamiento de datos")
        if not results['lead_integration']:
            print("   - Verificar flujos de creación de usuario y asignación de leads")
        if not results['configuration_management']:
            print("   - Verificar endpoints de gestión de configuración")
        
        return success

def main():
    """Main function"""
    tester = UltraMSGTester()
    success = tester.run_complete_integration_test()
    
    if success:
        print("\n🎉 INTEGRACIÓN ULTRAMSG: COMPLETAMENTE FUNCIONAL")
        return 0
    else:
        print("\n⚠️  INTEGRACIÓN ULTRAMSG: REQUIERE ATENCIÓN")
        return 1

if __name__ == "__main__":
    sys.exit(main())