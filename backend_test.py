import requests
import sys
import json
from datetime import datetime

class ProtegeYaAPITester:
    def __init__(self, base_url="https://insure-connect-6.preview.emergentagent.com"):
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

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}

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

    def test_root_endpoint(self):
        """Test root API endpoint"""
        return self.run_test("Root API", "GET", "", 200)

    def test_kpi_report(self):
        """Test KPI dashboard endpoint"""
        success, data = self.run_test("KPI Report", "GET", "reports/kpi", 200)
        if success and data:
            print(f"   Total Leads: {data.get('total_leads', 'N/A')}")
            print(f"   Active Brokers: {data.get('active_brokers', 'N/A')}")
            print(f"   Assignment Rate: {data.get('assignment_rate', 'N/A')}%")
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

    def test_create_broker(self, name, email, phone):
        """Test creating a broker"""
        broker_data = {
            "name": name,
            "email": email,
            "phone_number": phone,
            "whatsapp_number": phone,
            "subscription_status": "Active",
            "monthly_lead_quota": 50,
            "current_month_leads": 0
        }
        success, data = self.run_test(f"Create Broker - {name}", "POST", "brokers", 200, broker_data)
        if success and data.get('id'):
            self.created_ids['brokers'].append(data['id'])
        return success, data

    def test_get_brokers(self):
        """Test getting all brokers"""
        return self.run_test("Get Brokers", "GET", "brokers", 200)

    def test_get_leads(self):
        """Test getting leads"""
        return self.run_test("Get Leads", "GET", "leads", 200)

    def test_quote_simulation(self, make="Toyota", model="Corolla", year=2020, value=120000, municipality="Guatemala"):
        """Test quote simulation - the core functionality"""
        quote_data = {
            "make": make,
            "model": model,
            "year": year,
            "value": value,
            "municipality": municipality
        }
        success, data = self.run_test(f"Quote Simulation - {make} {model} {year}", "POST", "quotes/simulate", 200, quote_data)
        
        if success and data:
            quotes = data.get('quotes', [])
            disclaimer = data.get('disclaimer', '')
            
            print(f"   Found {len(quotes)} quotes")
            print(f"   Disclaimer: {disclaimer}")
            
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
        return self.run_test("WhatsApp Webhook", "POST", "whatsapp/webhook", 200, webhook_data)

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
        
        # Create test broker
        self.test_create_broker(
            "Juan Carlos Pérez",
            "juan.perez@protegeya.com",
            "+50212345678"
        )
        
        print(f"✅ Test data setup complete!")
        return len(insurers_created), len(products_created), len(versions_created)

def main():
    print("🚀 Starting ProtegeYa API Testing...")
    print("=" * 60)
    
    tester = ProtegeYaAPITester()
    
    # Test basic connectivity
    print("\n📡 Testing Basic Connectivity...")
    tester.test_root_endpoint()
    
    # Test KPI endpoint
    print("\n📊 Testing KPI Dashboard...")
    tester.test_kpi_report()
    
    # Setup comprehensive test data
    print("\n🏗️  Setting up Test Data...")
    insurers_count, products_count, versions_count = tester.setup_test_data()
    
    # Test data retrieval
    print("\n📋 Testing Data Retrieval...")
    tester.test_get_insurers()
    tester.test_get_products()
    tester.test_get_brokers()
    tester.test_get_leads()
    
    # Test core quote functionality
    print("\n💰 Testing Quote Engine...")
    tester.test_quote_simulation("Toyota", "Corolla", 2020, 120000, "Guatemala")
    tester.test_quote_simulation("Honda", "Civic", 2019, 95000, "Antigua Guatemala")
    tester.test_quote_simulation("Nissan", "Sentra", 2021, 110000)
    
    # Test WhatsApp integration
    print("\n📱 Testing WhatsApp Integration...")
    tester.test_whatsapp_webhook()
    
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
    
    if tester.tests_passed == tester.tests_run:
        print("\n🎉 All tests passed! Backend is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {tester.tests_run - tester.tests_passed} tests failed. Check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())