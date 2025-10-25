#!/usr/bin/env python3
"""
Test script for the newly implemented Aseguradoras and Vehiculos No Asegurables modules
ProtegeYa Review Request Testing
"""

import requests
import json
import sys
from datetime import datetime

class NewModulesTester:
    def __init__(self, base_url="https://vehicle-quote-bot.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_token = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, use_auth=True):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}
        
        # Add authentication if available and requested
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
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and 'id' in response_data:
                        print(f"   Created ID: {response_data['id']}")
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

    def test_admin_login(self, email="admin@protegeya.com", password="admin123"):
        """Test admin login"""
        login_data = {
            "email": email,
            "password": password
        }
        success, data = self.run_test("Admin Login", "POST", "auth/login", 200, login_data, use_auth=False)
        if success and data.get('access_token'):
            self.admin_token = data['access_token']
            print(f"   ✅ Admin token obtained")
            print(f"   User: {data.get('user', {}).get('name')} ({data.get('user', {}).get('role')})")
        return success, data

    # ASEGURADORAS MODULE TESTS
    def test_create_aseguradora(self, aseguradora_data):
        """Test creating an aseguradora (insurance company)"""
        success, data = self.run_test(f"Create Aseguradora - {aseguradora_data['nombre']}", "POST", "admin/aseguradoras", 200, aseguradora_data)
        if success and data.get('id'):
            print(f"   Created Aseguradora ID: {data['id']}")
            print(f"   Name: {data.get('nombre')}")
            print(f"   IVA: {data.get('iva')}%")
            print(f"   Cuotas: {data.get('cuotas')}")
        return success, data

    def test_get_all_aseguradoras(self):
        """Test getting all aseguradoras"""
        success, data = self.run_test("Get All Aseguradoras", "GET", "admin/aseguradoras", 200)
        if success and isinstance(data, list):
            print(f"   ✅ Found {len(data)} aseguradoras")
            for aseg in data:
                print(f"   - {aseg.get('nombre')} (Active: {aseg.get('activo')})")
        return success, data

    def test_get_single_aseguradora(self, aseguradora_id):
        """Test getting a single aseguradora by ID"""
        success, data = self.run_test(f"Get Aseguradora - {aseguradora_id}", "GET", f"admin/aseguradoras/{aseguradora_id}", 200)
        if success and data:
            print(f"   ✅ Retrieved aseguradora: {data.get('nombre')}")
            print(f"   IVA: {data.get('iva')}%")
            print(f"   Completo Tasas: {len(data.get('completo_tasas', []))} ranges")
            print(f"   RC Tasas: {len(data.get('rc_tasas', []))} ranges")
        return success, data

    def test_update_aseguradora(self, aseguradora_id, update_data):
        """Test updating an aseguradora"""
        success, data = self.run_test(f"Update Aseguradora - {aseguradora_id}", "PUT", f"admin/aseguradoras/{aseguradora_id}", 200, update_data)
        if success and data:
            print(f"   ✅ Updated aseguradora: {data.get('nombre')}")
            if 'iva' in update_data:
                print(f"   New IVA: {data.get('iva')}%")
        return success, data

    def test_quote_with_aseguradoras(self, suma_asegurada):
        """Test quote calculation with all active aseguradoras"""
        quote_data = {"suma_asegurada": suma_asegurada}
        success, data = self.run_test(f"Quote with Aseguradoras - Q{suma_asegurada}", "POST", f"admin/aseguradoras/cotizar?suma_asegurada={suma_asegurada}", 200, quote_data)
        if success and isinstance(data, list):
            print(f"   ✅ Generated {len(data)} quotes from active aseguradoras")
            for quote in data:
                print(f"   - {quote.get('aseguradora')}: RC Q{quote.get('cuota_rc', 0):.2f}, Completo Q{quote.get('cuota_completo', 0):.2f}")
        return success, data

    def test_delete_aseguradora(self, aseguradora_id):
        """Test deleting an aseguradora"""
        success, data = self.run_test(f"Delete Aseguradora - {aseguradora_id}", "DELETE", f"admin/aseguradoras/{aseguradora_id}", 200)
        if success:
            print(f"   ✅ Aseguradora {aseguradora_id} deleted successfully")
        return success, data

    # VEHICULOS NO ASEGURABLES MODULE TESTS
    def test_create_vehiculo_no_asegurable(self, vehiculo_data):
        """Test creating a vehiculo no asegurable (non-insurable vehicle)"""
        success, data = self.run_test(f"Create Vehiculo No Asegurable - {vehiculo_data['marca']} {vehiculo_data['modelo']}", "POST", "admin/vehiculos-no-asegurables", 200, vehiculo_data)
        if success and data.get('id'):
            print(f"   Created Vehiculo No Asegurable ID: {data['id']}")
            print(f"   Vehicle: {data.get('marca')} {data.get('modelo')} {data.get('año', 'All years')}")
            print(f"   Reason: {data.get('razon')}")
        return success, data

    def test_get_all_vehiculos_no_asegurables(self):
        """Test getting all vehiculos no asegurables"""
        success, data = self.run_test("Get All Vehiculos No Asegurables", "GET", "admin/vehiculos-no-asegurables", 200)
        if success and isinstance(data, list):
            print(f"   ✅ Found {len(data)} non-insurable vehicles")
            for vehiculo in data:
                year_text = vehiculo.get('año') if vehiculo.get('año') else 'All years'
                print(f"   - {vehiculo.get('marca')} {vehiculo.get('modelo')} ({year_text}): {vehiculo.get('razon')}")
        return success, data

    def test_verify_vehicle_insurability(self, marca, modelo, año):
        """Test vehicle insurability verification"""
        verification_data = {
            "marca": marca,
            "modelo": modelo,
            "año": año
        }
        success, data = self.run_test(f"Verify Vehicle Insurability - {marca} {modelo} {año}", "POST", f"admin/vehiculos-no-asegurables/verificar?marca={marca}&modelo={modelo}&año={año}", 200, verification_data)
        if success and data:
            is_insurable = data.get('asegurable', True)
            reason = data.get('razon', '')
            print(f"   ✅ Vehicle {marca} {modelo} {año}: {'INSURABLE' if is_insurable else 'NOT INSURABLE'}")
            if not is_insurable and reason:
                print(f"   Reason: {reason}")
        return success, data

    def test_delete_vehiculo_no_asegurable(self, vehiculo_id):
        """Test deleting a vehiculo no asegurable"""
        success, data = self.run_test(f"Delete Vehiculo No Asegurable - {vehiculo_id}", "DELETE", f"admin/vehiculos-no-asegurables/{vehiculo_id}", 200)
        if success:
            print(f"   ✅ Vehiculo No Asegurable {vehiculo_id} deleted successfully")
        return success, data

    def test_aseguradoras_module_comprehensive(self):
        """Comprehensive test of Aseguradoras module as specified in review request"""
        print("\n🏢 TESTING ASEGURADORAS MODULE - ProtegeYa Review Request")
        print("=" * 70)
        
        created_aseguradora_id = None
        
        try:
            # Step 1: Create Aseguradora
            print("\n1️⃣ Testing Create Aseguradora...")
            aseguradora_data = {
                "nombre": "Seguros El Roble",
                "iva": 0.12,
                "cuotas": 12,
                "completo_gastos_emision": 150.0,
                "completo_asistencia": 75.0,
                "rc_gastos_emision": 100.0,
                "rc_asistencia": 50.0,
                "completo_tasas": [
                    {"desde": 0, "hasta": 100000, "tasa": 3.5},
                    {"desde": 100000, "hasta": 500000, "tasa": 2.8}
                ],
                "rc_tasas": [
                    {"desde": 0, "hasta": 100000, "tasa": 1.5},
                    {"desde": 100000, "hasta": 500000, "tasa": 1.2}
                ],
                "activo": True
            }
            
            create_success, create_data = self.test_create_aseguradora(aseguradora_data)
            if not create_success:
                print("❌ Failed to create aseguradora - cannot continue with module tests")
                return False
            
            created_aseguradora_id = create_data.get('id')
            
            # Step 2: Get All Aseguradoras
            print("\n2️⃣ Testing Get All Aseguradoras...")
            get_all_success, get_all_data = self.test_get_all_aseguradoras()
            if not get_all_success:
                print("❌ Failed to get all aseguradoras")
                return False
            
            # Verify our created aseguradora is in the list
            found_created = any(aseg.get('id') == created_aseguradora_id for aseg in get_all_data)
            if found_created:
                print("   ✅ Created aseguradora found in list")
            else:
                print("   ❌ Created aseguradora not found in list")
            
            # Step 3: Get Single Aseguradora
            print("\n3️⃣ Testing Get Single Aseguradora...")
            get_single_success, get_single_data = self.test_get_single_aseguradora(created_aseguradora_id)
            if not get_single_success:
                print("❌ Failed to get single aseguradora")
                return False
            
            # Step 4: Update Aseguradora
            print("\n4️⃣ Testing Update Aseguradora...")
            update_data = {
                "nombre": "Seguros El Roble - Actualizado",
                "iva": 0.15
            }
            update_success, update_result = self.test_update_aseguradora(created_aseguradora_id, update_data)
            if not update_success:
                print("❌ Failed to update aseguradora")
                return False
            
            # Step 5: Quote with All Active Aseguradoras
            print("\n5️⃣ Testing Quote with All Active Aseguradoras...")
            quote_success, quote_data = self.test_quote_with_aseguradoras(150000)
            if not quote_success:
                print("❌ Failed to generate quotes with aseguradoras")
                return False
            
            # Verify our aseguradora is included in quotes
            found_in_quotes = any(quote.get('aseguradora_id') == created_aseguradora_id for quote in quote_data)
            if found_in_quotes:
                print("   ✅ Created aseguradora included in quote calculations")
            else:
                print("   ⚠️  Created aseguradora not found in quote results")
            
            # Step 6: Delete Aseguradora
            print("\n6️⃣ Testing Delete Aseguradora...")
            delete_success, delete_data = self.test_delete_aseguradora(created_aseguradora_id)
            if delete_success:
                created_aseguradora_id = None  # Mark as deleted
                print("   ✅ Aseguradora deleted successfully")
            else:
                print("❌ Failed to delete aseguradora")
                return False
            
            print("\n🎉 ASEGURADORAS MODULE TESTS COMPLETED SUCCESSFULLY!")
            return True
            
        except Exception as e:
            print(f"\n❌ Error during Aseguradoras module testing: {e}")
            return False
        finally:
            # Cleanup: Delete created aseguradora if it still exists
            if created_aseguradora_id:
                print(f"\n🧹 Cleanup: Deleting test aseguradora {created_aseguradora_id}")
                self.test_delete_aseguradora(created_aseguradora_id)

    def test_vehiculos_no_asegurables_module_comprehensive(self):
        """Comprehensive test of Vehiculos No Asegurables module as specified in review request"""
        print("\n🚗 TESTING VEHICULOS NO ASEGURABLES MODULE - ProtegeYa Review Request")
        print("=" * 70)
        
        created_vehiculo_ids = []
        
        try:
            # Step 1: Create Vehiculos No Asegurables
            print("\n1️⃣ Testing Create Vehiculos No Asegurables...")
            
            # Create first test vehicle
            vehiculo1_data = {
                "marca": "Taxi",
                "modelo": "Amarillo",
                "año": None,  # All years
                "razon": "Vehículos de transporte público"
            }
            
            create1_success, create1_data = self.test_create_vehiculo_no_asegurable(vehiculo1_data)
            if not create1_success:
                print("❌ Failed to create first vehiculo no asegurable")
                return False
            
            created_vehiculo_ids.append(create1_data.get('id'))
            
            # Create second test vehicle
            vehiculo2_data = {
                "marca": "Nissan",
                "modelo": "Tsuru",
                "año": 1995,
                "razon": "Modelo descontinuado"
            }
            
            create2_success, create2_data = self.test_create_vehiculo_no_asegurable(vehiculo2_data)
            if not create2_success:
                print("❌ Failed to create second vehiculo no asegurable")
                return False
            
            created_vehiculo_ids.append(create2_data.get('id'))
            
            # Step 2: Get All Vehiculos No Asegurables
            print("\n2️⃣ Testing Get All Vehiculos No Asegurables...")
            get_all_success, get_all_data = self.test_get_all_vehiculos_no_asegurables()
            if not get_all_success:
                print("❌ Failed to get all vehiculos no asegurables")
                return False
            
            # Verify our created vehicles are in the list
            found_vehicles = sum(1 for vehiculo in get_all_data if vehiculo.get('id') in created_vehiculo_ids)
            if found_vehicles == 2:
                print("   ✅ Both created vehicles found in list")
            else:
                print(f"   ⚠️  Only {found_vehicles}/2 created vehicles found in list")
            
            # Step 3: Verify Vehicle Insurability
            print("\n3️⃣ Testing Vehicle Insurability Verification...")
            
            # Test 1: Taxi Amarillo 2020 - Should return asegurable: false
            print("   Test 1: Taxi Amarillo 2020 (should be non-insurable)")
            verify1_success, verify1_data = self.test_verify_vehicle_insurability("Taxi", "Amarillo", 2020)
            if verify1_success:
                if not verify1_data.get('asegurable', True):
                    print("   ✅ Correctly identified as non-insurable")
                else:
                    print("   ❌ Should be non-insurable but returned as insurable")
            
            # Test 2: Nissan Tsuru 1995 - Should return asegurable: false
            print("   Test 2: Nissan Tsuru 1995 (should be non-insurable)")
            verify2_success, verify2_data = self.test_verify_vehicle_insurability("Nissan", "Tsuru", 1995)
            if verify2_success:
                if not verify2_data.get('asegurable', True):
                    print("   ✅ Correctly identified as non-insurable")
                else:
                    print("   ❌ Should be non-insurable but returned as insurable")
            
            # Test 3: Toyota Corolla 2020 - Should return asegurable: true
            print("   Test 3: Toyota Corolla 2020 (should be insurable)")
            verify3_success, verify3_data = self.test_verify_vehicle_insurability("Toyota", "Corolla", 2020)
            if verify3_success:
                if verify3_data.get('asegurable', False):
                    print("   ✅ Correctly identified as insurable")
                else:
                    print("   ❌ Should be insurable but returned as non-insurable")
            
            # Step 4: Delete Vehiculos No Asegurables
            print("\n4️⃣ Testing Delete Vehiculos No Asegurables...")
            
            for vehiculo_id in created_vehiculo_ids:
                delete_success, delete_data = self.test_delete_vehiculo_no_asegurable(vehiculo_id)
                if delete_success:
                    print(f"   ✅ Vehiculo {vehiculo_id} deleted successfully")
                else:
                    print(f"   ❌ Failed to delete vehiculo {vehiculo_id}")
            
            # Clear the list since we've deleted them
            created_vehiculo_ids = []
            
            print("\n🎉 VEHICULOS NO ASEGURABLES MODULE TESTS COMPLETED SUCCESSFULLY!")
            return True
            
        except Exception as e:
            print(f"\n❌ Error during Vehiculos No Asegurables module testing: {e}")
            return False
        finally:
            # Cleanup: Delete created vehicles if they still exist
            for vehiculo_id in created_vehiculo_ids:
                print(f"\n🧹 Cleanup: Deleting test vehiculo {vehiculo_id}")
                self.test_delete_vehiculo_no_asegurable(vehiculo_id)

    def run_comprehensive_tests(self):
        """Run comprehensive tests for both new modules"""
        print("🚀 TESTING NEW MODULES - ASEGURADORAS & VEHICULOS NO ASEGURABLES")
        print("=" * 80)
        
        # Step 1: Authentication
        print("\n🔐 AUTHENTICATION")
        print("-" * 30)
        
        login_success, login_data = self.test_admin_login("admin@protegeya.com", "admin123")
        if not login_success:
            print("❌ Cannot proceed without admin authentication")
            return False
        
        # Step 2: Test Aseguradoras Module
        print("\n🏢 ASEGURADORAS MODULE TESTING")
        print("-" * 30)
        
        aseguradoras_success = self.test_aseguradoras_module_comprehensive()
        
        # Step 3: Test Vehiculos No Asegurables Module
        print("\n🚗 VEHICULOS NO ASEGURABLES MODULE TESTING")
        print("-" * 30)
        
        vehiculos_success = self.test_vehiculos_no_asegurables_module_comprehensive()
        
        # Final Summary
        print("\n" + "=" * 80)
        print("📊 NEW MODULES TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        print(f"\n📋 MODULE RESULTS:")
        print(f"   Aseguradoras Module: {'✅ PASSED' if aseguradoras_success else '❌ FAILED'}")
        print(f"   Vehiculos No Asegurables Module: {'✅ PASSED' if vehiculos_success else '❌ FAILED'}")
        
        overall_success = aseguradoras_success and vehiculos_success
        
        if overall_success:
            print("\n🎉 ALL NEW MODULES TESTS PASSED! Both modules are working correctly.")
        else:
            print(f"\n⚠️  Some module tests failed. Please review the issues above.")
        
        return overall_success

if __name__ == "__main__":
    tester = NewModulesTester()
    success = tester.run_comprehensive_tests()
    
    if success:
        print("\n🎉 NEW MODULES TESTING: SUCCESS!")
        sys.exit(0)
    else:
        print("\n❌ NEW MODULES TESTING: FAILED!")
        sys.exit(1)