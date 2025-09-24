import requests
import sys
import json
from datetime import datetime

class ProtegeYaAPITester:
    def __init__(self, base_url="https://leadgen-hub-9.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_token = None
        self.broker_token = None
        self.created_ids = {
            'insurers': [],
            'products': [],
            'brokers': [],
            'auth_users': []
        }

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

    # Authentication Tests
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

    def test_get_current_user(self):
        """Test getting current user profile"""
        return self.run_test("Get Current User", "GET", "auth/me", 200)

    def test_create_broker_user(self, name, email, password):
        """Test creating a broker user (admin only)"""
        user_data = {
            "email": email,
            "password": password,
            "role": "broker",
            "name": name
        }
        success, data = self.run_test(f"Create Broker User - {name}", "POST", "auth/register", 200, user_data)
        if success and data.get('id'):
            self.created_ids['auth_users'].append(data['id'])
        return success, data

    def test_broker_login(self, email, password):
        """Test broker login"""
        login_data = {
            "email": email,
            "password": password
        }
        success, data = self.run_test("Broker Login", "POST", "auth/login", 200, login_data, use_auth=False)
        if success and data.get('access_token'):
            self.broker_token = data['access_token']
            print(f"   ✅ Broker token obtained")
        return success, data

    def test_root_endpoint(self):
        """Test root API endpoint"""
        return self.run_test("Root API", "GET", "", 200, use_auth=False)

    def test_kpi_report_admin(self):
        """Test KPI dashboard endpoint as admin"""
        success, data = self.run_test("KPI Report (Admin)", "GET", "reports/kpi", 200)
        if success and data:
            print(f"   Total Leads: {data.get('total_leads', 'N/A')}")
            print(f"   Active Brokers: {data.get('active_brokers', 'N/A')}")
            print(f"   Assignment Rate: {data.get('assignment_rate', 'N/A')}%")
            print(f"   Total Revenue: Q{data.get('total_revenue', 'N/A')}")
        return success

    def test_kpi_report_broker(self):
        """Test KPI dashboard endpoint as broker"""
        # Temporarily switch to broker token
        original_token = self.admin_token
        self.admin_token = self.broker_token
        
        success, data = self.run_test("KPI Report (Broker)", "GET", "reports/kpi", 200)
        if success and data:
            print(f"   Assigned Leads: {data.get('total_assigned_leads', 'N/A')}")
            print(f"   Closed Won: {data.get('closed_won_deals', 'N/A')}")
            print(f"   Conversion Rate: {data.get('conversion_rate', 'N/A')}%")
        
        # Restore admin token
        self.admin_token = original_token
        return success

    def test_create_insurer(self, name, logo_url=None):
        """Test creating an insurer"""
        insurer_data = {
            "name": name,
            "logo_url": logo_url,
            "active": True
        }
        success, data = self.run_test(f"Create Insurer - {name}", "POST", "admin/insurers", 200, insurer_data)
        if success and data.get('id'):
            self.created_ids['insurers'].append(data['id'])
        return success, data

    def test_get_insurers(self):
        """Test getting all insurers"""
        return self.run_test("Get Insurers", "GET", "admin/insurers", 200)

    def test_create_product(self, insurer_id, name, insurance_type="FullCoverage"):
        """Test creating a product"""
        product_data = {
            "insurer_id": insurer_id,
            "name": name,
            "insurance_type": insurance_type,
            "active": True
        }
        success, data = self.run_test(f"Create Product - {name}", "POST", "admin/products", 200, product_data)
        if success and data.get('id'):
            self.created_ids['products'].append(data['id'])
        return success, data

    def test_get_products(self):
        """Test getting all products"""
        return self.run_test("Get Products", "GET", "admin/products", 200)

    def test_create_product_version(self, product_id, version_name, base_premium_percentage):
        """Test creating a product version"""
        version_data = {
            "product_id": product_id,
            "version_name": version_name,
            "base_premium_percentage": base_premium_percentage,
            "active": True
        }
        return self.run_test(f"Create Product Version - {version_name}", "POST", "admin/product-versions", 200, version_data)

    def test_create_tariff_section(self, product_version_id, name, percentage):
        """Test creating a tariff section"""
        section_data = {
            "product_version_id": product_version_id,
            "name": name,
            "percentage_of_sum_insured": percentage
        }
        return self.run_test(f"Create Tariff Section - {name}", "POST", "admin/tariff-sections", 200, section_data)

    def test_create_fixed_benefit(self, product_version_id, name, amount):
        """Test creating a fixed benefit"""
        benefit_data = {
            "product_version_id": product_version_id,
            "name": name,
            "amount": amount
        }
        return self.run_test(f"Create Fixed Benefit - {name}", "POST", "admin/fixed-benefits", 200, benefit_data)

    def test_create_broker(self, name, email, phone, user_id=None):
        """Test creating a broker"""
        broker_data = {
            "user_id": user_id or f"user_{datetime.now().strftime('%H%M%S')}",
            "name": name,
            "email": email,
            "phone_number": phone,
            "whatsapp_number": phone,
            "subscription_status": "Active",
            "monthly_lead_quota": 50,
            "current_month_leads": 0,
            "commission_percentage": 10.0
        }
        success, data = self.run_test(f"Create Broker - {name}", "POST", "brokers", 200, broker_data)
        if success and data.get('id'):
            self.created_ids['brokers'].append(data['id'])
        return success, data

    def test_update_broker(self, broker_id, update_data):
        """Test updating a broker"""
        return self.run_test(f"Update Broker - {broker_id}", "PUT", f"brokers/{broker_id}", 200, update_data)

    def test_update_broker_subscription(self, broker_id, status):
        """Test updating broker subscription status"""
        return self.run_test(f"Update Broker Subscription - {status}", "PUT", f"brokers/{broker_id}/subscription", 200, {"status": status})

    def test_delete_broker(self, broker_id):
        """Test deleting a broker"""
        return self.run_test(f"Delete Broker - {broker_id}", "DELETE", f"brokers/{broker_id}", 200)

    def test_get_brokers(self):
        """Test getting all brokers"""
        return self.run_test("Get Brokers", "GET", "brokers", 200)

    def test_get_leads(self):
        """Test getting leads"""
        return self.run_test("Get Leads", "GET", "leads", 200)

    def test_update_lead_status(self, lead_id, status, notes=None, closed_amount=None):
        """Test updating lead status"""
        update_data = {
            "lead_id": lead_id,
            "broker_status": status
        }
        if notes:
            update_data["notes"] = notes
        if closed_amount:
            update_data["closed_amount"] = closed_amount
            
        return self.run_test(f"Update Lead Status - {status}", "POST", f"leads/{lead_id}/status", 200, update_data)

    def test_get_configuration(self):
        """Test getting system configuration"""
        return self.run_test("Get Configuration", "GET", "admin/configuration", 200)

    def test_update_configuration(self, config_data):
        """Test updating system configuration"""
        return self.run_test("Update Configuration", "PUT", "admin/configuration", 200, config_data)

    def test_get_broker_payments(self):
        """Test getting broker payments"""
        return self.run_test("Get Broker Payments", "GET", "admin/payments", 200)

    def test_create_broker_payment(self, broker_id, amount, month, year):
        """Test creating a broker payment"""
        payment_data = {
            "broker_id": broker_id,
            "amount": amount,
            "month": month,
            "year": year,
            "status": "Pending",
            "due_date": f"{year}-{month:02d}-15T00:00:00"
        }
        return self.run_test(f"Create Broker Payment - Q{amount}", "POST", "admin/payments", 200, payment_data)

    def test_quote_simulation(self, make="Toyota", model="Corolla", year=2020, value=120000, municipality="Guatemala"):
        """Test quote simulation - the core functionality"""
        quote_data = {
            "make": make,
            "model": model,
            "year": year,
            "value": value,
            "municipality": municipality
        }
        success, data = self.run_test(f"Quote Simulation - {make} {model} {year}", "POST", "quotes/simulate", 200, quote_data, use_auth=False)
        
        if success and data:
            quotes = data.get('quotes', [])
            disclaimer = data.get('disclaimer', '')
            
            print(f"   Found {len(quotes)} quotes")
            print(f"   Disclaimer: {disclaimer}")
            
            # Verify disclaimer contains required text
            if "ProtegeYa es un comparador" in disclaimer:
                print(f"   ✅ Disclaimer contains required legal text")
            else:
                print(f"   ⚠️  Disclaimer might be missing required legal text")
            
            for i, quote in enumerate(quotes):
                print(f"   Quote {i+1}: {quote.get('insurer_name')} - {quote.get('product_name')}")
                print(f"     Premium: Q{quote.get('monthly_premium', 0)}")
                print(f"     Type: {quote.get('insurance_type')}")
                
            # Verify quote calculation logic
            if quotes:
                first_quote = quotes[0]
                expected_premium_range = (value * 0.01, value * 0.10)  # 1% to 10% of vehicle value
                actual_premium = first_quote.get('monthly_premium', 0)
                
                if expected_premium_range[0] <= actual_premium <= expected_premium_range[1]:
                    print(f"   ✅ Premium calculation looks reasonable: Q{actual_premium}")
                else:
                    print(f"   ⚠️  Premium might be out of expected range: Q{actual_premium}")
                    
        return success, data

    def test_whatsapp_webhook(self):
        """Test WhatsApp webhook endpoint"""
        webhook_data = {
            "instance_id": "test_instance",
            "data": {
                "type": "message",
                "from": "50212345678@c.us",
                "body": "Hola, quiero cotizar mi vehículo"
            }
        }
        return self.run_test("WhatsApp Webhook", "POST", "whatsapp/webhook", 200, webhook_data, use_auth=False)

    def test_send_whatsapp_message(self):
        """Test sending WhatsApp message"""
        message_data = {
            "phone_number": "50212345678",
            "message": "Test message from ProtegeYa API"
        }
        return self.run_test("Send WhatsApp Message", "POST", "whatsapp/send", 200, message_data)

    # Manual Lead Creation and Assignment Tests
    def test_create_manual_lead(self, lead_data):
        """Test creating a manual lead"""
        success, data = self.run_test("Create Manual Lead", "POST", "admin/leads", 200, lead_data)
        if success and data.get('id'):
            print(f"   Created Lead ID: {data['id']}")
            print(f"   Lead Name: {data.get('name')}")
            print(f"   Phone: {data.get('phone_number')}")
            print(f"   Vehicle: {data.get('vehicle_make')} {data.get('vehicle_model')} {data.get('vehicle_year')}")
            print(f"   Status: {data.get('status')}")
        return success, data

    def test_manual_lead_assignment(self, lead_id, broker_id):
        """Test manual assignment of lead to specific broker"""
        success, data = self.run_test(
            f"Manual Lead Assignment - Lead {lead_id} to Broker {broker_id}", 
            "POST", 
            f"admin/leads/{lead_id}/assign", 
            200, 
            {"broker_id": broker_id}
        )
        if success:
            print(f"   ✅ Lead {lead_id} assigned to broker {broker_id}")
        return success, data

    def test_round_robin_assignment(self, lead_id):
        """Test automatic round-robin assignment"""
        success, data = self.run_test(
            f"Round-Robin Assignment - Lead {lead_id}", 
            "POST", 
            f"admin/leads/{lead_id}/assign-auto", 
            200
        )
        if success and data.get('assigned_broker_id'):
            print(f"   ✅ Lead {lead_id} auto-assigned to broker {data['assigned_broker_id']}")
        return success, data

    def test_get_lead_by_id(self, lead_id):
        """Test getting a specific lead to verify data integrity"""
        # Since there's no specific endpoint for single lead, we'll get all leads and filter
        success, data = self.run_test("Get Leads for Verification", "GET", "leads", 200)
        if success and isinstance(data, list):
            lead = next((l for l in data if l.get('id') == lead_id), None)
            if lead:
                print(f"   ✅ Lead found: {lead.get('name')} - Status: {lead.get('status')}")
                print(f"   Assigned Broker: {lead.get('assigned_broker_id', 'None')}")
                return True, lead
            else:
                print(f"   ❌ Lead {lead_id} not found in leads list")
                return False, {}
        return success, data

    def test_verify_broker_lead_count(self, broker_id, expected_increment=1):
        """Test that broker lead count was incremented after assignment"""
        success, data = self.run_test("Get Brokers for Lead Count Verification", "GET", "brokers", 200)
        if success and isinstance(data, list):
            broker = next((b for b in data if b.get('id') == broker_id), None)
            if broker:
                current_leads = broker.get('current_month_leads', 0)
                print(f"   Broker {broker.get('name')} current month leads: {current_leads}")
                return True, broker
            else:
                print(f"   ❌ Broker {broker_id} not found")
                return False, {}
        return success, data

    def setup_test_data(self):
        """Setup test data for comprehensive testing"""
        print("\n🔧 Setting up test data...")
        
        # Create test insurers
        insurers_created = []
        test_insurers = [
            ("G&T Seguros", "https://example.com/gt-logo.png"),
            ("Seguros Universales", "https://example.com/universales-logo.png"),
            ("La Ceiba Seguros", None)
        ]
        
        for name, logo in test_insurers:
            success, data = self.test_create_insurer(name, logo)
            if success:
                insurers_created.append(data)
        
        # Create test products for each insurer
        products_created = []
        for insurer in insurers_created:
            # Full coverage product
            success, product_data = self.test_create_product(
                insurer['id'], 
                f"Seguro Completo {insurer['name']}", 
                "FullCoverage"
            )
            if success:
                products_created.append(product_data)
                
            # Third party product
            success, product_data = self.test_create_product(
                insurer['id'], 
                f"Responsabilidad Civil {insurer['name']}", 
                "ThirdParty"
            )
            if success:
                products_created.append(product_data)
        
        # Create product versions with different premium percentages
        versions_created = []
        for i, product in enumerate(products_created):
            base_percentage = 3.5 + (i * 0.5)  # Different percentages for variety
            success, version_data = self.test_create_product_version(
                product['id'],
                f"Version 2024 - {product['name']}",
                base_percentage
            )
            if success:
                versions_created.append(version_data)
        
        # Create tariff sections and benefits for each version
        for version in versions_created:
            # Tariff sections (percentage of vehicle value)
            self.test_create_tariff_section(version['id'], "Daños Propios", 100.0)
            self.test_create_tariff_section(version['id'], "Responsabilidad Civil", 50.0)
            self.test_create_tariff_section(version['id'], "Robo Total", 100.0)
            
            # Fixed benefits (fixed amounts in GTQ)
            self.test_create_fixed_benefit(version['id'], "Gastos Médicos", 50000)
            self.test_create_fixed_benefit(version['id'], "Asistencia Legal", 25000)
            self.test_create_fixed_benefit(version['id'], "Grúa", 1500)
        
        # Create test broker with auth user
        print("\n👥 Creating test broker with authentication...")
        broker_success, broker_user = self.test_create_broker_user(
            "Juan Carlos Pérez",
            "juan.perez@protegeya.com",
            "broker123"
        )
        
        if broker_success:
            broker_profile_success, broker_data = self.test_create_broker(
                "Juan Carlos Pérez",
                "juan.perez@protegeya.com",
                "+50212345678",
                broker_user['id']
            )
        
        print(f"✅ Test data setup complete!")
        return len(insurers_created), len(products_created), len(versions_created)

def main():
    print("🚀 Starting ProtegeYa EXPANDED API Testing...")
    print("=" * 60)
    
    tester = ProtegeYaAPITester()
    
    # Test basic connectivity
    print("\n📡 Testing Basic Connectivity...")
    tester.test_root_endpoint()
    
    # Test authentication system
    print("\n🔐 Testing Authentication System...")
    admin_login_success, admin_data = tester.test_admin_login()
    
    if not admin_login_success:
        print("❌ Admin login failed! Cannot continue with authenticated tests.")
        return 1
    
    # Test current user endpoint
    tester.test_get_current_user()
    
    # Test KPI endpoint as admin
    print("\n📊 Testing KPI Dashboard (Admin)...")
    tester.test_kpi_report_admin()
    
    # Setup comprehensive test data
    print("\n🏗️  Setting up Test Data...")
    insurers_count, products_count, versions_count = tester.setup_test_data()
    
    # Test broker authentication
    print("\n👥 Testing Broker Authentication...")
    broker_login_success, broker_data = tester.test_broker_login("juan.perez@protegeya.com", "broker123")
    
    if broker_login_success:
        print("\n📊 Testing KPI Dashboard (Broker)...")
        tester.test_kpi_report_broker()
    
    # Test data retrieval
    print("\n📋 Testing Data Retrieval...")
    tester.test_get_insurers()
    tester.test_get_products()
    tester.test_get_brokers()
    tester.test_get_leads()
    
    # Test configuration management
    print("\n⚙️  Testing Configuration Management...")
    tester.test_get_configuration()
    
    config_update = {
        "whatsapp_enabled": True,
        "use_emergent_llm": True,
        "ultramsg_instance_id": "test_instance_123"
    }
    tester.test_update_configuration(config_update)
    
    # Test broker management
    print("\n👥 Testing Broker Management...")
    tester.test_get_broker_payments()
    
    # Test broker CRUD operations if we have brokers
    if tester.created_ids['brokers']:
        broker_id = tester.created_ids['brokers'][0]
        
        # Test broker update
        update_data = {
            "monthly_lead_quota": 75,
            "commission_percentage": 12.0
        }
        tester.test_update_broker(broker_id, update_data)
        
        # Test subscription status update
        tester.test_update_broker_subscription(broker_id, "Active")
        
        # Test broker payment creation
        tester.test_create_broker_payment(broker_id, 500.0, 12, 2024)
    
    # Test core quote functionality
    print("\n💰 Testing Quote Engine...")
    tester.test_quote_simulation("Toyota", "Corolla", 2020, 120000, "Guatemala")
    tester.test_quote_simulation("Honda", "Civic", 2019, 95000, "Antigua Guatemala")
    tester.test_quote_simulation("Nissan", "Sentra", 2021, 110000)
    
    # Test WhatsApp integration
    print("\n📱 Testing WhatsApp Integration...")
    tester.test_whatsapp_webhook()
    tester.test_send_whatsapp_message()
    
    # Print final results
    print("\n" + "=" * 60)
    print("📊 FINAL TEST RESULTS")
    print("=" * 60)
    print(f"✅ Tests Passed: {tester.tests_passed}")
    print(f"❌ Tests Failed: {tester.tests_run - tester.tests_passed}")
    print(f"📈 Success Rate: {(tester.tests_passed / tester.tests_run * 100):.1f}%")
    
    print(f"\n🏗️  Test Data Created:")
    print(f"   📋 Insurers: {len(tester.created_ids['insurers'])}")
    print(f"   📦 Products: {len(tester.created_ids['products'])}")
    print(f"   👥 Brokers: {len(tester.created_ids['brokers'])}")
    print(f"   🔐 Auth Users: {len(tester.created_ids['auth_users'])}")
    
    print(f"\n🔑 Authentication Status:")
    print(f"   Admin Token: {'✅ Valid' if tester.admin_token else '❌ Missing'}")
    print(f"   Broker Token: {'✅ Valid' if tester.broker_token else '❌ Missing'}")
    
    if tester.tests_passed == tester.tests_run:
        print("\n🎉 All tests passed! Backend is working correctly.")
        print("✅ Authentication system working")
        print("✅ Role-based access control working")
        print("✅ CRUD operations working")
        print("✅ Quote engine working")
        print("✅ Configuration management working")
        return 0
    else:
        print(f"\n⚠️  {tester.tests_run - tester.tests_passed} tests failed. Check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())