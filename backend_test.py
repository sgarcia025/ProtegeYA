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
        # The broker_id should be passed as a query parameter based on the FastAPI function signature
        success, data = self.run_test(
            f"Manual Lead Assignment - Lead {lead_id} to Broker {broker_id}", 
            "POST", 
            f"admin/leads/{lead_id}/assign?broker_id={broker_id}", 
            200
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

    # NEW FUNCTIONALITY TESTS - ProtegeYa Review Request
    def test_get_all_users(self):
        """Test getting all users (admin only) - NEW FUNCTIONALITY"""
        success, data = self.run_test("Get All Users", "GET", "auth/users", 200)
        if success and isinstance(data, list):
            print(f"   ✅ Found {len(data)} users in system")
            admin_users = [u for u in data if u.get('role') == 'admin']
            broker_users = [u for u in data if u.get('role') == 'broker']
            print(f"   - Admin users: {len(admin_users)}")
            print(f"   - Broker users: {len(broker_users)}")
            
            # Show user details
            for user in data[:3]:  # Show first 3 users
                print(f"   - {user.get('name')} ({user.get('email')}) - Role: {user.get('role')} - Active: {user.get('active', True)}")
        return success, data

    def test_toggle_user_status(self, user_id, expected_new_status=None):
        """Test toggling user active status (admin only) - NEW FUNCTIONALITY"""
        success, data = self.run_test(f"Toggle User Status - {user_id}", "PUT", f"auth/users/{user_id}/toggle-status", 200)
        if success and data:
            new_status = data.get('active')
            print(f"   ✅ User status toggled to: {'Active' if new_status else 'Inactive'}")
            if expected_new_status is not None and new_status == expected_new_status:
                print(f"   ✅ Status matches expected: {expected_new_status}")
            return True, data
        return success, data

    def test_get_lead_details(self, lead_id=None):
        """Test getting detailed lead information - NEW FUNCTIONALITY"""
        # Get all leads first to find existing ones
        success, data = self.run_test("Get Lead Details", "GET", "leads", 200)
        if success and isinstance(data, list) and data:
            if lead_id:
                # Find specific lead
                lead = next((l for l in data if l.get('id') == lead_id), None)
                if lead:
                    print(f"   ✅ Lead details found for ID: {lead_id}")
                    self._print_lead_details(lead)
                    return True, lead
                else:
                    print(f"   ❌ Lead {lead_id} not found")
                    return False, {}
            else:
                # Show details of first lead
                lead = data[0]
                print(f"   ✅ Lead details retrieved for: {lead.get('name', 'Unknown')}")
                self._print_lead_details(lead)
                return True, lead
        else:
            print("   ❌ No leads found in system")
            return False, {}

    def test_lead_reassignment(self, lead_id, new_broker_id, original_broker_id=None):
        """Test reassigning a lead to a different broker - NEW FUNCTIONALITY"""
        print(f"\n🔄 Testing Lead Reassignment...")
        print(f"   Lead ID: {lead_id}")
        print(f"   New Broker ID: {new_broker_id}")
        if original_broker_id:
            print(f"   Original Broker ID: {original_broker_id}")
        
        # First get current lead state
        lead_success, lead_data = self.test_get_lead_details(lead_id)
        if not lead_success:
            print("   ❌ Cannot get lead details for reassignment test")
            return False, {}
        
        original_assigned_broker = lead_data.get('assigned_broker_id')
        print(f"   Current assigned broker: {original_assigned_broker}")
        
        # Perform reassignment
        success, data = self.run_test(
            f"Reassign Lead {lead_id} to Broker {new_broker_id}", 
            "POST", 
            f"admin/leads/{lead_id}/assign?broker_id={new_broker_id}", 
            200
        )
        
        if success:
            print(f"   ✅ Lead reassignment API call successful")
            
            # Verify reassignment by checking lead details again
            verification_success, updated_lead = self.test_get_lead_details(lead_id)
            if verification_success:
                new_assigned_broker = updated_lead.get('assigned_broker_id')
                if new_assigned_broker == new_broker_id:
                    print(f"   ✅ Lead successfully reassigned to broker {new_broker_id}")
                    
                    # Check if broker lead counts were updated
                    self._verify_broker_counts_after_reassignment(original_assigned_broker, new_broker_id)
                    return True, updated_lead
                else:
                    print(f"   ❌ Reassignment failed - Lead still assigned to {new_assigned_broker}")
                    return False, {}
        
        return success, data

    def _print_lead_details(self, lead):
        """Helper method to print detailed lead information"""
        print(f"     Name: {lead.get('name', 'N/A')}")
        print(f"     Phone: {lead.get('phone_number', 'N/A')}")
        print(f"     Vehicle: {lead.get('vehicle_make', 'N/A')} {lead.get('vehicle_model', 'N/A')} {lead.get('vehicle_year', 'N/A')}")
        print(f"     Vehicle Value: Q{lead.get('vehicle_value', 'N/A')}")
        print(f"     Selected Insurer: {lead.get('selected_insurer', 'N/A')}")
        print(f"     Quote Price: Q{lead.get('selected_quote_price', 'N/A')}")
        print(f"     Status: {lead.get('status', 'N/A')}")
        print(f"     Broker Status: {lead.get('broker_status', 'N/A')}")
        print(f"     Assigned Broker: {lead.get('assigned_broker_id', 'None')}")
        print(f"     Created: {lead.get('created_at', 'N/A')}")
        print(f"     Updated: {lead.get('updated_at', 'N/A')}")

    def _verify_broker_counts_after_reassignment(self, original_broker_id, new_broker_id):
        """Helper method to verify broker lead counts after reassignment"""
        print(f"   🔍 Verifying broker lead counts after reassignment...")
        
        brokers_success, brokers_data = self.test_get_brokers()
        if brokers_success and isinstance(brokers_data, list):
            # Find original broker
            if original_broker_id:
                original_broker = next((b for b in brokers_data if b.get('id') == original_broker_id), None)
                if original_broker:
                    print(f"     Original broker {original_broker.get('name')} leads: {original_broker.get('current_month_leads', 0)}")
            
            # Find new broker
            new_broker = next((b for b in brokers_data if b.get('id') == new_broker_id), None)
            if new_broker:
                print(f"     New broker {new_broker.get('name')} leads: {new_broker.get('current_month_leads', 0)}")

    def test_new_functionalities_flow(self):
        """Test all new functionalities in a comprehensive flow - REVIEW REQUEST TESTING"""
        print("\n🆕 Testing NEW FUNCTIONALITIES - ProtegeYa Review Request")
        print("=" * 60)
        
        # Test 1: Get all users functionality
        print("\n1️⃣ Testing Get All Users Functionality...")
        users_success, users_data = self.test_get_all_users()
        if not users_success or not users_data:
            print("❌ Cannot proceed with user management tests - no users found")
            return False
        
        # Find a broker user to test toggle functionality
        broker_users = [u for u in users_data if u.get('role') == 'broker']
        admin_users = [u for u in users_data if u.get('role') == 'admin']
        
        print(f"   Found {len(broker_users)} broker users and {len(admin_users)} admin users")
        
        # Test 2: Toggle user status functionality
        if broker_users:
            print("\n2️⃣ Testing Toggle User Status Functionality...")
            test_broker = broker_users[0]
            broker_id = test_broker.get('id')
            current_status = test_broker.get('active', True)
            
            print(f"   Testing with broker: {test_broker.get('name')} (Current status: {'Active' if current_status else 'Inactive'})")
            
            # Toggle status
            toggle_success, toggle_data = self.test_toggle_user_status(broker_id, not current_status)
            if toggle_success:
                # Toggle back to original status
                print("   🔄 Toggling back to original status...")
                self.test_toggle_user_status(broker_id, current_status)
        else:
            print("\n2️⃣ ⚠️ No broker users found to test toggle functionality")
        
        # Test 3: Get existing leads for details testing
        print("\n3️⃣ Testing Lead Details Functionality...")
        leads_success, leads_data = self.run_test("Get Existing Leads", "GET", "leads", 200)
        
        if leads_success and isinstance(leads_data, list) and leads_data:
            print(f"   Found {len(leads_data)} existing leads in system")
            
            # Test lead details with first lead
            test_lead = leads_data[0]
            lead_id = test_lead.get('id')
            details_success, details_data = self.test_get_lead_details(lead_id)
            
            # Test 4: Lead reassignment functionality
            if details_success and len(broker_users) >= 2:
                print("\n4️⃣ Testing Lead Reassignment Functionality...")
                
                current_broker_id = test_lead.get('assigned_broker_id')
                
                # Find a different broker for reassignment
                available_brokers = [b for b in broker_users if b.get('id') != current_broker_id]
                if available_brokers:
                    new_broker = available_brokers[0]
                    new_broker_id = new_broker.get('id')
                    
                    print(f"   Reassigning lead from broker {current_broker_id} to {new_broker_id}")
                    reassign_success, reassign_data = self.test_lead_reassignment(lead_id, new_broker_id, current_broker_id)
                    
                    if reassign_success:
                        print("   ✅ Lead reassignment test completed successfully")
                        
                        # Reassign back to original broker if possible
                        if current_broker_id:
                            print("   🔄 Reassigning back to original broker...")
                            self.test_lead_reassignment(lead_id, current_broker_id, new_broker_id)
                    else:
                        print("   ❌ Lead reassignment test failed")
                else:
                    print("   ⚠️ Not enough different brokers available for reassignment test")
            elif not details_success:
                print("   ❌ Cannot test reassignment - lead details test failed")
            else:
                print("   ⚠️ Cannot test reassignment - need at least 2 broker users")
        else:
            print("   ⚠️ No existing leads found for details and reassignment testing")
            
            # Create a test lead for functionality testing
            print("   📝 Creating test lead for functionality testing...")
            test_lead_data = {
                "name": "María González",
                "phone_number": "+502-5555-1234",
                "vehicle_make": "Honda",
                "vehicle_model": "Civic",
                "vehicle_year": 2022,
                "vehicle_value": 150000,
                "selected_insurer": "G&T Seguros",
                "selected_quote_price": 3200
            }
            
            create_success, create_data = self.test_create_manual_lead(test_lead_data)
            if create_success and broker_users:
                new_lead_id = create_data.get('id')
                
                # Test assignment and reassignment with new lead
                if len(broker_users) >= 2:
                    broker1_id = broker_users[0].get('id')
                    broker2_id = broker_users[1].get('id')
                    
                    # Assign to first broker
                    print(f"   📋 Assigning new lead to first broker...")
                    assign_success, assign_data = self.test_manual_lead_assignment(new_lead_id, broker1_id)
                    
                    if assign_success:
                        # Test reassignment to second broker
                        print(f"   🔄 Testing reassignment to second broker...")
                        reassign_success, reassign_data = self.test_lead_reassignment(new_lead_id, broker2_id, broker1_id)
        
        print("\n🎉 New Functionalities Testing Complete!")
        return True

    def test_manual_lead_creation_and_assignment_flow(self):
        """Test the complete manual lead creation and assignment flow"""
        print("\n🎯 Testing Manual Lead Creation and Assignment Flow...")
        
        # Test data as specified in the review request
        test_lead_data = {
            "name": "Test Cliente",
            "phone_number": "+502-9999-8888",
            "vehicle_make": "Toyota",
            "vehicle_model": "Corolla",
            "vehicle_year": 2023,
            "vehicle_value": 120000,
            "selected_insurer": "Test Insurance",
            "selected_quote_price": 2500
        }
        
        # Step 1: Get available brokers for assignment
        print("\n📋 Step 1: Getting available brokers...")
        brokers_success, brokers_data = self.test_get_brokers()
        if not brokers_success or not brokers_data:
            print("❌ No brokers available for assignment testing")
            return False
        
        active_brokers = [b for b in brokers_data if b.get('subscription_status') == 'Active']
        if not active_brokers:
            print("❌ No active brokers available for assignment")
            return False
        
        print(f"   ✅ Found {len(active_brokers)} active brokers")
        for broker in active_brokers:
            print(f"   - {broker.get('name')} (ID: {broker.get('id')}) - Current leads: {broker.get('current_month_leads', 0)}")
        
        # Step 2: Get available insurers
        print("\n🏢 Step 2: Getting available insurers...")
        insurers_success, insurers_data = self.test_get_insurers()
        if insurers_success and insurers_data:
            print(f"   ✅ Found {len(insurers_data)} insurers")
            for insurer in insurers_data[:3]:  # Show first 3
                print(f"   - {insurer.get('name')} (Active: {insurer.get('active', False)})")
        
        # Step 3: Create manual lead
        print("\n📝 Step 3: Creating manual lead...")
        lead_success, lead_data = self.test_create_manual_lead(test_lead_data)
        if not lead_success or not lead_data.get('id'):
            print("❌ Failed to create manual lead")
            return False
        
        lead_id = lead_data['id']
        print(f"   ✅ Manual lead created successfully with ID: {lead_id}")
        
        # Step 4: Test manual assignment to specific broker
        print("\n👤 Step 4: Testing manual assignment to specific broker...")
        target_broker = active_brokers[0]  # Use first active broker
        target_broker_id = target_broker['id']
        
        # Get broker's current lead count before assignment
        initial_lead_count = target_broker.get('current_month_leads', 0)
        print(f"   Broker {target_broker.get('name')} initial lead count: {initial_lead_count}")
        
        assignment_success, assignment_data = self.test_manual_lead_assignment(lead_id, target_broker_id)
        if not assignment_success:
            print("❌ Manual assignment failed")
            return False
        
        # Step 5: Verify lead was assigned correctly
        print("\n🔍 Step 5: Verifying lead assignment...")
        verification_success, updated_lead = self.test_get_lead_by_id(lead_id)
        if verification_success and updated_lead:
            if updated_lead.get('assigned_broker_id') == target_broker_id:
                print(f"   ✅ Lead correctly assigned to broker {target_broker_id}")
                if updated_lead.get('status') == 'AssignedToBroker':
                    print(f"   ✅ Lead status correctly updated to 'AssignedToBroker'")
                else:
                    print(f"   ⚠️  Lead status is '{updated_lead.get('status')}', expected 'AssignedToBroker'")
            else:
                print(f"   ❌ Lead assignment mismatch. Expected: {target_broker_id}, Got: {updated_lead.get('assigned_broker_id')}")
        
        # Step 6: Verify broker lead count was incremented
        print("\n📊 Step 6: Verifying broker lead count increment...")
        broker_verification_success, updated_broker = self.test_verify_broker_lead_count(target_broker_id)
        if broker_verification_success and updated_broker:
            new_lead_count = updated_broker.get('current_month_leads', 0)
            if new_lead_count == initial_lead_count + 1:
                print(f"   ✅ Broker lead count correctly incremented from {initial_lead_count} to {new_lead_count}")
            else:
                print(f"   ⚠️  Broker lead count: expected {initial_lead_count + 1}, got {new_lead_count}")
        
        # Step 7: Create another lead for round-robin testing
        print("\n🔄 Step 7: Testing round-robin assignment...")
        test_lead_data_2 = test_lead_data.copy()
        test_lead_data_2["name"] = "Test Cliente 2"
        test_lead_data_2["phone_number"] = "+502-9999-7777"
        
        lead2_success, lead2_data = self.test_create_manual_lead(test_lead_data_2)
        if not lead2_success or not lead2_data.get('id'):
            print("❌ Failed to create second lead for round-robin test")
            return False
        
        lead2_id = lead2_data['id']
        print(f"   ✅ Second lead created with ID: {lead2_id}")
        
        # Step 8: Test round-robin assignment
        print("\n🎲 Step 8: Testing automatic round-robin assignment...")
        roundrobin_success, roundrobin_data = self.test_round_robin_assignment(lead2_id)
        if not roundrobin_success:
            print("❌ Round-robin assignment failed")
            return False
        
        assigned_broker_id = roundrobin_data.get('assigned_broker_id')
        if assigned_broker_id:
            print(f"   ✅ Round-robin assignment successful to broker: {assigned_broker_id}")
            
            # Verify the assignment
            verification2_success, updated_lead2 = self.test_get_lead_by_id(lead2_id)
            if verification2_success and updated_lead2:
                if updated_lead2.get('assigned_broker_id') == assigned_broker_id:
                    print(f"   ✅ Round-robin assignment verified")
                else:
                    print(f"   ❌ Round-robin assignment verification failed")
        
        print("\n🎉 Manual Lead Creation and Assignment Flow Test Complete!")
        return True

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
    
    # Test Manual Lead Creation and Assignment Flow
    print("\n🎯 Testing Manual Lead Creation and Assignment...")
    manual_lead_success = tester.test_manual_lead_creation_and_assignment_flow()
    
    # Test NEW FUNCTIONALITIES - ProtegeYa Review Request
    print("\n🆕 Testing NEW FUNCTIONALITIES - Review Request...")
    new_functionalities_success = tester.test_new_functionalities_flow()
    
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

    def test_lead_assignment_investigation(self):
        """Comprehensive investigation of lead assignment issues - ProtegeYa Review Request"""
        print("\n🔍 INVESTIGATING LEAD ASSIGNMENT PROBLEM - ProtegeYa")
        print("=" * 70)
        
        investigation_results = {
            'active_brokers_count': 0,
            'unassigned_leads_count': 0,
            'total_leads_count': 0,
            'round_robin_working': False,
            'manual_assignment_working': False,
            'data_integrity_issues': [],
            'errors_found': []
        }
        
        # Step 1: Check available brokers
        print("\n1️⃣ INVESTIGATING AVAILABLE BROKERS...")
        brokers_success, brokers_data = self.test_get_brokers()
        
        if brokers_success and isinstance(brokers_data, list):
            active_brokers = [b for b in brokers_data if b.get('subscription_status') == 'Active']
            investigation_results['active_brokers_count'] = len(active_brokers)
            
            print(f"   📊 TOTAL BROKERS: {len(brokers_data)}")
            print(f"   ✅ ACTIVE BROKERS: {len(active_brokers)}")
            
            if active_brokers:
                print("\n   📋 ACTIVE BROKERS DETAILS:")
                for broker in active_brokers:
                    print(f"   - {broker.get('name', 'Unknown')} (ID: {broker.get('id')})")
                    print(f"     Email: {broker.get('email', 'N/A')}")
                    print(f"     Current leads: {broker.get('current_month_leads', 0)}")
                    print(f"     Monthly quota: {broker.get('monthly_lead_quota', 0)}")
                    print(f"     Status: {broker.get('subscription_status', 'Unknown')}")
                    print()
            else:
                investigation_results['errors_found'].append("NO ACTIVE BROKERS FOUND")
                print("   ❌ NO ACTIVE BROKERS FOUND!")
        else:
            investigation_results['errors_found'].append("FAILED TO RETRIEVE BROKERS")
            print("   ❌ FAILED TO RETRIEVE BROKERS")
        
        # Step 2: Check existing leads
        print("\n2️⃣ INVESTIGATING EXISTING LEADS...")
        leads_success, leads_data = self.test_get_leads()
        
        if leads_success and isinstance(leads_data, list):
            investigation_results['total_leads_count'] = len(leads_data)
            unassigned_leads = [l for l in leads_data if not l.get('assigned_broker_id')]
            investigation_results['unassigned_leads_count'] = len(unassigned_leads)
            
            print(f"   📊 TOTAL LEADS: {len(leads_data)}")
            print(f"   ❌ UNASSIGNED LEADS: {len(unassigned_leads)}")
            print(f"   ✅ ASSIGNED LEADS: {len(leads_data) - len(unassigned_leads)}")
            
            if unassigned_leads:
                print("\n   📋 UNASSIGNED LEADS DETAILS:")
                for lead in unassigned_leads[:5]:  # Show first 5
                    print(f"   - {lead.get('name', 'Unknown')} (ID: {lead.get('id')})")
                    print(f"     Phone: {lead.get('phone_number', 'N/A')}")
                    print(f"     Status: {lead.get('status', 'Unknown')}")
                    print(f"     Created: {lead.get('created_at', 'N/A')}")
                    print()
            
            # Check for data integrity issues
            print("\n   🔍 CHECKING DATA INTEGRITY...")
            for lead in leads_data:
                if lead.get('assigned_broker_id'):
                    # Check if assigned broker exists and is active
                    assigned_broker = next((b for b in brokers_data if b.get('id') == lead.get('assigned_broker_id')), None)
                    if not assigned_broker:
                        investigation_results['data_integrity_issues'].append(f"Lead {lead.get('id')} assigned to non-existent broker {lead.get('assigned_broker_id')}")
                    elif assigned_broker.get('subscription_status') != 'Active':
                        investigation_results['data_integrity_issues'].append(f"Lead {lead.get('id')} assigned to inactive broker {assigned_broker.get('name')}")
        else:
            investigation_results['errors_found'].append("FAILED TO RETRIEVE LEADS")
            print("   ❌ FAILED TO RETRIEVE LEADS")
        
        # Step 3: Test manual assignment functionality
        print("\n3️⃣ TESTING MANUAL ASSIGNMENT FUNCTIONALITY...")
        if active_brokers and unassigned_leads:
            test_lead = unassigned_leads[0]
            test_broker = active_brokers[0]
            
            print(f"   🧪 Testing assignment of lead {test_lead.get('id')} to broker {test_broker.get('id')}")
            
            # Get initial broker lead count
            initial_count = test_broker.get('current_month_leads', 0)
            
            assignment_success, assignment_data = self.test_manual_lead_assignment(
                test_lead.get('id'), 
                test_broker.get('id')
            )
            
            if assignment_success:
                investigation_results['manual_assignment_working'] = True
                print("   ✅ MANUAL ASSIGNMENT API WORKING")
                
                # Verify assignment
                verification_success, updated_lead = self.test_get_lead_by_id(test_lead.get('id'))
                if verification_success and updated_lead.get('assigned_broker_id') == test_broker.get('id'):
                    print("   ✅ LEAD ASSIGNMENT VERIFIED")
                    
                    # Check broker count increment
                    broker_check_success, updated_broker = self.test_verify_broker_lead_count(test_broker.get('id'))
                    if broker_check_success:
                        new_count = updated_broker.get('current_month_leads', 0)
                        if new_count == initial_count + 1:
                            print("   ✅ BROKER LEAD COUNT CORRECTLY INCREMENTED")
                        else:
                            investigation_results['data_integrity_issues'].append(f"Broker lead count not incremented correctly: expected {initial_count + 1}, got {new_count}")
                else:
                    investigation_results['errors_found'].append("MANUAL ASSIGNMENT VERIFICATION FAILED")
            else:
                investigation_results['errors_found'].append("MANUAL ASSIGNMENT API FAILED")
                print("   ❌ MANUAL ASSIGNMENT API FAILED")
        else:
            print("   ⚠️ Cannot test manual assignment - no active brokers or unassigned leads")
        
        # Step 4: Test round-robin assignment functionality
        print("\n4️⃣ TESTING ROUND-ROBIN ASSIGNMENT FUNCTIONALITY...")
        
        # Create a test lead for round-robin testing
        test_lead_data = {
            "name": "Test Lead para Round-Robin",
            "phone_number": "+502-1111-2222",
            "vehicle_make": "Toyota",
            "vehicle_model": "Corolla",
            "vehicle_year": 2023,
            "vehicle_value": 100000,
            "selected_insurer": "Test Insurer",
            "selected_quote_price": 2000
        }
        
        create_success, create_data = self.test_create_manual_lead(test_lead_data)
        if create_success and create_data.get('id'):
            test_lead_id = create_data['id']
            print(f"   📝 Created test lead: {test_lead_id}")
            
            if active_brokers:
                # Test round-robin assignment
                roundrobin_success, roundrobin_data = self.test_round_robin_assignment(test_lead_id)
                
                if roundrobin_success:
                    investigation_results['round_robin_working'] = True
                    assigned_broker_id = roundrobin_data.get('assigned_broker_id')
                    print(f"   ✅ ROUND-ROBIN ASSIGNMENT WORKING - Assigned to broker: {assigned_broker_id}")
                    
                    # Verify the assignment
                    verification_success, updated_lead = self.test_get_lead_by_id(test_lead_id)
                    if verification_success and updated_lead.get('assigned_broker_id') == assigned_broker_id:
                        print("   ✅ ROUND-ROBIN ASSIGNMENT VERIFIED")
                    else:
                        investigation_results['errors_found'].append("ROUND-ROBIN ASSIGNMENT VERIFICATION FAILED")
                else:
                    investigation_results['errors_found'].append("ROUND-ROBIN ASSIGNMENT API FAILED")
                    print("   ❌ ROUND-ROBIN ASSIGNMENT API FAILED")
            else:
                print("   ⚠️ Cannot test round-robin - no active brokers available")
        else:
            print("   ❌ Failed to create test lead for round-robin testing")
        
        # Step 5: Test complete flow - create lead and auto-assign
        print("\n5️⃣ TESTING COMPLETE FLOW: CREATE LEAD + AUTO-ASSIGN...")
        
        complete_flow_lead_data = {
            "name": "Test Complete Flow",
            "phone_number": "+502-3333-4444",
            "vehicle_make": "Honda",
            "vehicle_model": "Civic",
            "vehicle_year": 2022,
            "vehicle_value": 110000,
            "selected_insurer": "Test Complete Insurer",
            "selected_quote_price": 2200
        }
        
        flow_create_success, flow_create_data = self.test_create_manual_lead(complete_flow_lead_data)
        if flow_create_success and flow_create_data.get('id'):
            flow_lead_id = flow_create_data['id']
            print(f"   📝 Created lead for complete flow test: {flow_lead_id}")
            
            # Immediately try auto-assignment
            flow_assign_success, flow_assign_data = self.test_round_robin_assignment(flow_lead_id)
            if flow_assign_success:
                print("   ✅ COMPLETE FLOW WORKING: CREATE + AUTO-ASSIGN")
            else:
                investigation_results['errors_found'].append("COMPLETE FLOW FAILED AT AUTO-ASSIGNMENT")
                print("   ❌ COMPLETE FLOW FAILED AT AUTO-ASSIGNMENT")
        else:
            print("   ❌ Failed to create lead for complete flow test")
        
        # Step 6: Generate investigation report
        print("\n" + "=" * 70)
        print("📋 INVESTIGATION REPORT - LEAD ASSIGNMENT PROBLEM")
        print("=" * 70)
        
        print(f"\n📊 SYSTEM STATUS:")
        print(f"   Active Brokers: {investigation_results['active_brokers_count']}")
        print(f"   Total Leads: {investigation_results['total_leads_count']}")
        print(f"   Unassigned Leads: {investigation_results['unassigned_leads_count']}")
        
        print(f"\n🔧 FUNCTIONALITY STATUS:")
        print(f"   Manual Assignment: {'✅ WORKING' if investigation_results['manual_assignment_working'] else '❌ FAILED'}")
        print(f"   Round-Robin Assignment: {'✅ WORKING' if investigation_results['round_robin_working'] else '❌ FAILED'}")
        
        if investigation_results['data_integrity_issues']:
            print(f"\n⚠️ DATA INTEGRITY ISSUES FOUND:")
            for issue in investigation_results['data_integrity_issues']:
                print(f"   - {issue}")
        
        if investigation_results['errors_found']:
            print(f"\n❌ ERRORS FOUND:")
            for error in investigation_results['errors_found']:
                print(f"   - {error}")
        
        print(f"\n💡 RECOMMENDATIONS:")
        if investigation_results['active_brokers_count'] == 0:
            print("   - CRITICAL: No active brokers found. Check broker subscription statuses.")
        if investigation_results['unassigned_leads_count'] > 0 and investigation_results['active_brokers_count'] > 0:
            print("   - Run bulk assignment process for unassigned leads.")
        if investigation_results['data_integrity_issues']:
            print("   - Fix data integrity issues between leads and brokers.")
        if not investigation_results['round_robin_working']:
            print("   - Investigate round-robin assignment algorithm.")
        if not investigation_results['manual_assignment_working']:
            print("   - Check manual assignment API and database operations.")
        
        return investigation_results

if __name__ == "__main__":
    sys.exit(main())