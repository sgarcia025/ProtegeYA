#!/usr/bin/env python3
"""
ProtegeYa - Complete WhatsApp Flow Testing
Testing the complete data capture and PDF generation flow as requested in the review.

OBJETIVO: Verificar que el flujo completo funcione correctamente con los arreglos implementados

PRUEBAS ESPECÍFICAS:
1. Captura de Nombre
2. Generación de Cotización  
3. Selección de Aseguradora
4. Verificación de Base de Datos

DATOS DE PRUEBA:
- Teléfono: +50212345678
- Nombre: Juan Carlos Pérez  
- Vehículo: Toyota Corolla 2020, Q150,000
- Selección: Seguros El Roble, seguro completo
"""

import requests
import json
import time
from datetime import datetime

class WhatsAppFlowTester:
    def __init__(self, base_url="https://whatsapp-bot-debug-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.test_phone = "+50212345678"
        self.test_name = "Juan Carlos Pérez"
        self.test_vehicle = {
            "make": "Toyota",
            "model": "Corolla",
            "year": 2020,
            "value": 150000
        }
        self.test_selection = {
            "insurer": "Seguros El Roble",
            "type": "seguro completo"
        }
        
    def login_admin(self):
        """Login as admin to get authentication token"""
        print("🔐 Authenticating as admin...")
        
        login_data = {
            "email": "admin@protegeya.com",
            "password": "admin123"
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/auth/login",
                json=login_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get('access_token')
                print(f"✅ Admin authentication successful")
                return True
            else:
                print(f"❌ Admin login failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Admin login error: {e}")
            return False
    
    def send_webhook_message(self, message, message_id=None):
        """Send a simulated WhatsApp webhook message"""
        if not message_id:
            message_id = f"msg_{int(time.time())}"
            
        webhook_data = {
            "data": {
                "event_type": "message",
                "type": "message",
                "from": f"{self.test_phone.replace('+', '')}@c.us",
                "body": message,
                "id": message_id,
                "fromMe": False,
                "timestamp": str(int(time.time()))
            }
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/whatsapp/webhook",
                json=webhook_data,
                timeout=30
            )
            
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, {"error": f"Status {response.status_code}"}
                
        except Exception as e:
            return False, {"error": str(e)}
    
    def get_leads(self):
        """Get all leads from the system"""
        if not self.admin_token:
            return False, []
            
        headers = {
            'Authorization': f'Bearer {self.admin_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(
                f"{self.api_url}/leads",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, []
                
        except Exception as e:
            print(f"Error getting leads: {e}")
            return False, []
    
    def get_auth_users(self):
        """Get all auth users from the system"""
        if not self.admin_token:
            return False, []
            
        headers = {
            'Authorization': f'Bearer {self.admin_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(
                f"{self.api_url}/auth/users",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, []
                
        except Exception as e:
            print(f"Error getting auth users: {e}")
            return False, []
    
    def find_lead_by_phone(self, phone_number):
        """Find a lead by phone number"""
        success, leads = self.get_leads()
        if success:
            # Try both with and without + prefix
            phone_variants = [phone_number, phone_number.replace('+', ''), '+' + phone_number.replace('+', '')]
            for lead in leads:
                if lead.get('phone_number') in phone_variants:
                    return lead
        return None
    
    def find_user_by_phone(self, phone_number):
        """Find a user by phone number - check leads since user profiles aren't exposed via API"""
        # Since user profiles aren't exposed via API, we'll check if a lead exists with the name
        # This indicates the name was captured from WhatsApp
        lead = self.find_lead_by_phone(phone_number)
        if lead and lead.get('name'):
            return {"phone_number": phone_number, "name": lead.get('name')}
        return None
    
    def test_step_1_name_capture(self):
        """Test Step 1: Name Capture"""
        print("\n1️⃣ TESTING NAME CAPTURE")
        print("=" * 50)
        
        # Send initial message
        print(f"📱 Sending initial message: 'Hola, quiero cotizar un seguro'")
        success, data = self.send_webhook_message("Hola, quiero cotizar un seguro", "msg_001")
        
        if not success:
            print(f"❌ Initial message failed: {data.get('error')}")
            return False
        
        print("✅ Initial message sent successfully")
        
        # Wait a moment for processing
        time.sleep(2)
        
        # Send name response
        print(f"📱 Sending name: 'Mi nombre es {self.test_name}'")
        success, data = self.send_webhook_message(f"Mi nombre es {self.test_name}", "msg_002")
        
        if not success:
            print(f"❌ Name message failed: {data.get('error')}")
            return False
        
        print("✅ Name message sent successfully")
        
        # Wait for processing
        time.sleep(3)
        
        # Verify name was captured
        print("🔍 Verifying name capture in database...")
        user = self.find_user_by_phone(self.test_phone)
        
        if user and user.get('name') == self.test_name:
            print(f"✅ Name captured successfully: {user.get('name')}")
            return True
        else:
            print(f"❌ Name not captured properly. Found: {user.get('name') if user else 'No user found'}")
            return False
    
    def test_step_2_quote_generation(self):
        """Test Step 2: Quote Generation"""
        print("\n2️⃣ TESTING QUOTE GENERATION")
        print("=" * 50)
        
        # Send vehicle information
        vehicle_message = f"Tengo un {self.test_vehicle['make']} {self.test_vehicle['model']} {self.test_vehicle['year']} que vale Q{self.test_vehicle['value']}"
        print(f"📱 Sending vehicle info: '{vehicle_message}'")
        
        success, data = self.send_webhook_message(vehicle_message, "msg_003")
        
        if not success:
            print(f"❌ Vehicle message failed: {data.get('error')}")
            return False
        
        print("✅ Vehicle message sent successfully")
        
        # Wait for processing
        time.sleep(5)
        
        # Verify lead was created with vehicle data
        print("🔍 Verifying lead creation with vehicle data...")
        lead = self.find_lead_by_phone(self.test_phone)
        
        if not lead:
            print("❌ No lead found for phone number")
            return False
        
        # Check vehicle data
        vehicle_checks = {
            "make": lead.get('vehicle_make') == self.test_vehicle['make'],
            "model": lead.get('vehicle_model') == self.test_vehicle['model'],
            "year": lead.get('vehicle_year') == self.test_vehicle['year'],
            "value": lead.get('vehicle_value') == self.test_vehicle['value']
        }
        
        print(f"📋 Vehicle data verification:")
        for field, passed in vehicle_checks.items():
            status = "✅" if passed else "❌"
            expected = self.test_vehicle[field]
            actual = lead.get(f'vehicle_{field}')
            print(f"   {field}: {status} Expected: {expected}, Got: {actual}")
        
        # Check if quotes were generated
        quotes = lead.get('quotes', [])
        quote_generated = lead.get('quote_generated', False)
        
        print(f"📊 Quote generation:")
        print(f"   Quotes count: {len(quotes)}")
        print(f"   Quote generated flag: {quote_generated}")
        
        if all(vehicle_checks.values()) and (quotes or quote_generated):
            print("✅ Quote generation successful")
            return True
        else:
            print("❌ Quote generation failed")
            return False
    
    def test_step_3_insurer_selection(self):
        """Test Step 3: Insurer Selection and PDF Generation"""
        print("\n3️⃣ TESTING INSURER SELECTION AND PDF GENERATION")
        print("=" * 50)
        
        # Send insurer selection
        selection_message = f"Me interesa {self.test_selection['insurer']}, el {self.test_selection['type']}"
        print(f"📱 Sending selection: '{selection_message}'")
        
        success, data = self.send_webhook_message(selection_message, "msg_004")
        
        if not success:
            print(f"❌ Selection message failed: {data.get('error')}")
            return False
        
        print("✅ Selection message sent successfully")
        
        # Wait for processing (PDF generation takes time)
        print("⏳ Waiting for PDF generation...")
        time.sleep(10)
        
        # Verify selection was processed
        print("🔍 Verifying insurer selection and PDF generation...")
        lead = self.find_lead_by_phone(self.test_phone)
        
        if not lead:
            print("❌ No lead found for verification")
            return False
        
        # Check selection data
        selected_insurer = lead.get('selected_insurer')
        selected_price = lead.get('selected_quote_price')
        pdf_sent = lead.get('pdf_sent', False)
        
        print(f"📋 Selection verification:")
        print(f"   Selected insurer: {selected_insurer}")
        print(f"   Selected price: Q{selected_price}")
        print(f"   PDF sent: {pdf_sent}")
        
        # Verify insurer selection
        insurer_match = selected_insurer and self.test_selection['insurer'].lower() in selected_insurer.lower()
        
        if insurer_match:
            print("✅ Insurer selection captured correctly")
        else:
            print("❌ Insurer selection not captured properly")
        
        if pdf_sent:
            print("✅ PDF generation and sending confirmed")
        else:
            print("❌ PDF not generated or sent")
        
        return insurer_match and pdf_sent
    
    def test_step_4_database_verification(self):
        """Test Step 4: Complete Database Verification"""
        print("\n4️⃣ FINAL DATABASE VERIFICATION")
        print("=" * 50)
        
        print("🔍 Performing comprehensive database verification...")
        
        # Get final lead state
        lead = self.find_lead_by_phone(self.test_phone)
        user = self.find_user_by_phone(self.test_phone)
        
        if not lead:
            print("❌ Lead not found in database")
            return False
        
        if not user:
            print("❌ User not found in database")
            return False
        
        print("\n📋 FINAL DATABASE STATE:")
        print(f"👤 USER:")
        print(f"   Name: {user.get('name')}")
        print(f"   Phone: {user.get('phone_number')}")
        print(f"   Created: {user.get('created_at')}")
        
        print(f"\n📄 LEAD:")
        print(f"   Name: {lead.get('name')}")
        print(f"   Phone: {lead.get('phone_number')}")
        print(f"   Vehicle: {lead.get('vehicle_make')} {lead.get('vehicle_model')} {lead.get('vehicle_year')}")
        print(f"   Vehicle Value: Q{lead.get('vehicle_value')}")
        print(f"   Selected Insurer: {lead.get('selected_insurer')}")
        print(f"   Selected Price: Q{lead.get('selected_quote_price')}")
        print(f"   Status: {lead.get('status')}")
        print(f"   PDF Sent: {lead.get('pdf_sent')}")
        print(f"   Assigned Broker: {lead.get('assigned_broker_id')}")
        
        # Verification checklist
        verification_checks = {
            "user_name_saved": user.get('name') == self.test_name,
            "lead_name_saved": lead.get('name') == self.test_name,
            "vehicle_make": lead.get('vehicle_make') == self.test_vehicle['make'],
            "vehicle_model": lead.get('vehicle_model') == self.test_vehicle['model'],
            "vehicle_year": lead.get('vehicle_year') == self.test_vehicle['year'],
            "vehicle_value": lead.get('vehicle_value') == self.test_vehicle['value'],
            "insurer_selected": lead.get('selected_insurer') is not None,
            "pdf_sent": lead.get('pdf_sent') == True
        }
        
        print(f"\n✅ VERIFICATION CHECKLIST:")
        all_passed = True
        for check, passed in verification_checks.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {check.replace('_', ' ').title()}: {status}")
            if not passed:
                all_passed = False
        
        if all_passed:
            print("\n🎉 ALL DATABASE VERIFICATIONS PASSED!")
            return True
        else:
            print("\n❌ Some database verifications failed")
            return False
    
    def run_complete_flow_test(self):
        """Run the complete WhatsApp flow test"""
        print("🎯 PROTEGEYA - COMPLETE WHATSAPP FLOW TEST")
        print("=" * 70)
        print("Testing complete data capture and PDF generation flow")
        print(f"Phone: {self.test_phone}")
        print(f"Name: {self.test_name}")
        print(f"Vehicle: {self.test_vehicle['make']} {self.test_vehicle['model']} {self.test_vehicle['year']}")
        print(f"Value: Q{self.test_vehicle['value']}")
        print(f"Selection: {self.test_selection['insurer']}, {self.test_selection['type']}")
        print("=" * 70)
        
        # Authenticate
        if not self.login_admin():
            print("❌ Cannot proceed without admin authentication")
            return False
        
        # Run test steps
        results = {
            "name_capture": False,
            "quote_generation": False,
            "insurer_selection": False,
            "database_verification": False
        }
        
        # Step 1: Name Capture
        results["name_capture"] = self.test_step_1_name_capture()
        
        # Step 2: Quote Generation
        if results["name_capture"]:
            results["quote_generation"] = self.test_step_2_quote_generation()
        else:
            print("⚠️ Skipping quote generation - name capture failed")
        
        # Step 3: Insurer Selection
        if results["quote_generation"]:
            results["insurer_selection"] = self.test_step_3_insurer_selection()
        else:
            print("⚠️ Skipping insurer selection - quote generation failed")
        
        # Step 4: Database Verification
        results["database_verification"] = self.test_step_4_database_verification()
        
        # Final Summary
        print("\n" + "=" * 70)
        print("📊 COMPLETE WHATSAPP FLOW TEST RESULTS")
        print("=" * 70)
        
        total_steps = len(results)
        passed_steps = sum(results.values())
        
        print(f"\n🎯 STEP RESULTS:")
        for step, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {step.replace('_', ' ').title()}: {status}")
        
        print(f"\n📈 OVERALL RESULTS:")
        print(f"   Steps Passed: {passed_steps}/{total_steps}")
        print(f"   Success Rate: {(passed_steps/total_steps*100):.1f}%")
        
        if passed_steps == total_steps:
            print(f"\n🎉 COMPLETE WHATSAPP FLOW TEST: SUCCESS!")
            print(f"   ✅ Name capture working")
            print(f"   ✅ Quote generation working")
            print(f"   ✅ Insurer selection working")
            print(f"   ✅ PDF generation working")
            print(f"   ✅ Database verification passed")
            return True
        else:
            print(f"\n⚠️ COMPLETE WHATSAPP FLOW TEST: PARTIAL SUCCESS")
            print(f"   {total_steps - passed_steps} step(s) failed")
            failed_steps = [step for step, passed in results.items() if not passed]
            print(f"   Failed steps: {', '.join(failed_steps)}")
            return False

def main():
    """Main function to run the WhatsApp flow test"""
    tester = WhatsAppFlowTester()
    success = tester.run_complete_flow_test()
    
    if success:
        print("\n🎉 ALL TESTS PASSED - WhatsApp flow working correctly!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED - Review the results above")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())