#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class QuoteSeedingTester:
    def __init__(self, base_url="https://protege-ya-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None

    def login_admin(self):
        """Login as admin"""
        login_data = {
            "email": "admin@protegeya.com",
            "password": "admin123"
        }
        
        try:
            response = requests.post(f"{self.api_url}/auth/login", json=login_data, timeout=30)
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get('access_token')
                print("✅ Admin login successful")
                return True
            else:
                print(f"❌ Admin login failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Admin login error: {e}")
            return False

    def test_direct_quote_endpoint(self):
        """Test direct quote endpoint with BMW 325i 2015"""
        print("\n🎯 TESTING DIRECT QUOTE ENDPOINT - BMW 325i 2015")
        print("-" * 50)
        
        bmw_quote_data = {
            "make": "BMW",
            "model": "325i", 
            "year": 2015,
            "value": 85000,
            "municipality": "Guatemala"
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/quotes/simulate", 
                json=bmw_quote_data, 
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                quotes = data.get('quotes', [])
                print(f"✅ Generated {len(quotes)} quotes for BMW 325i 2015")
                
                if len(quotes) >= 4:
                    print("✅ Expected 4 quotes from 4 insurers - SUCCESS")
                    for i, quote in enumerate(quotes, 1):
                        insurer = quote.get('insurer_name', 'Unknown')
                        premium = quote.get('monthly_premium', 0)
                        print(f"   {i}. {insurer}: Q{premium:,.2f}/month")
                        
                        # Verify realistic pricing for Q85,000 vehicle
                        if 500 <= premium <= 8500:  # 0.6% to 10% of vehicle value monthly
                            print(f"      ✅ Realistic pricing for Q85,000 vehicle")
                        else:
                            print(f"      ⚠️  Price may be unrealistic for Q85,000 vehicle")
                    return True, quotes
                else:
                    print(f"❌ Expected 4 quotes, got {len(quotes)}")
                    return False, []
            else:
                print(f"❌ Quote endpoint failed: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, []
                
        except Exception as e:
            print(f"❌ Quote endpoint error: {e}")
            return False, []

    def test_whatsapp_flow(self):
        """Test WhatsApp complete flow simulation"""
        print("\n📱 TESTING WHATSAPP COMPLETE FLOW SIMULATION")
        print("-" * 50)
        
        test_phone = "+50288888888"
        
        # Message 1: Initial greeting
        print("\n   📱 Message 1: Initial greeting")
        webhook_data_1 = {
            "instance_id": "instance108171",
            "data": {
                "type": "message",
                "from": f"{test_phone.replace('+', '')}@c.us",
                "body": "Hola, quiero cotizar un seguro"
            }
        }
        
        try:
            response1 = requests.post(
                f"{self.api_url}/whatsapp/webhook", 
                json=webhook_data_1, 
                timeout=30
            )
            
            if response1.status_code == 200:
                print("   ✅ Initial WhatsApp message processed successfully")
            else:
                print(f"   ❌ Initial WhatsApp message failed: {response1.status_code}")
                return False, {}
        except Exception as e:
            print(f"   ❌ Initial WhatsApp message error: {e}")
            return False, {}
        
        # Message 2: Name capture
        print("\n   📱 Message 2: Name capture")
        webhook_data_2 = {
            "instance_id": "instance108171", 
            "data": {
                "type": "message",
                "from": f"{test_phone.replace('+', '')}@c.us",
                "body": "Sergio Garcia"
            }
        }
        
        try:
            response2 = requests.post(
                f"{self.api_url}/whatsapp/webhook", 
                json=webhook_data_2, 
                timeout=30
            )
            
            if response2.status_code == 200:
                print("   ✅ Name capture message processed successfully")
            else:
                print(f"   ❌ Name capture message failed: {response2.status_code}")
                return False, {}
        except Exception as e:
            print(f"   ❌ Name capture message error: {e}")
            return False, {}
        
        # Message 3: Vehicle data
        print("\n   📱 Message 3: Vehicle data")
        webhook_data_3 = {
            "instance_id": "instance108171",
            "data": {
                "type": "message", 
                "from": f"{test_phone.replace('+', '')}@c.us",
                "body": "BMW 325i 2015 Q85000"
            }
        }
        
        try:
            response3 = requests.post(
                f"{self.api_url}/whatsapp/webhook", 
                json=webhook_data_3, 
                timeout=30
            )
            
            if response3.status_code == 200:
                print("   ✅ Vehicle data message processed successfully")
                print("   🔍 Checking if quotes were generated...")
                
                # Check if lead was created and quotes generated
                headers = {'Authorization': f'Bearer {self.admin_token}'} if self.admin_token else {}
                leads_response = requests.get(f"{self.api_url}/leads", headers=headers, timeout=30)
                
                if leads_response.status_code == 200:
                    leads_data = leads_response.json()
                    if isinstance(leads_data, list):
                        # Find lead for our test phone number
                        test_lead = None
                        for lead in leads_data:
                            if lead.get('phone_number') == test_phone or lead.get('phone_number') == test_phone.replace('+', ''):
                                test_lead = lead
                                break
                        
                        if test_lead:
                            print(f"   ✅ Lead found for {test_phone}")
                            print(f"      Name: {test_lead.get('name', 'N/A')}")
                            print(f"      Vehicle: {test_lead.get('vehicle_make')} {test_lead.get('vehicle_model')} {test_lead.get('vehicle_year')}")
                            print(f"      Value: Q{test_lead.get('vehicle_value', 0):,.2f}")
                            print(f"      Quote Generated: {test_lead.get('quote_generated', False)}")
                            print(f"      Status: {test_lead.get('status', 'Unknown')}")
                            
                            if test_lead.get('quote_generated'):
                                print("   ✅ QUOTES SUCCESSFULLY GENERATED!")
                                quotes = test_lead.get('quotes', [])
                                if quotes:
                                    print(f"      Found {len(quotes)} quotes in lead data")
                                    for i, quote in enumerate(quotes[:4], 1):
                                        insurer = quote.get('insurer_name', 'Unknown')
                                        premium = quote.get('monthly_premium', 0)
                                        print(f"      {i}. {insurer}: Q{premium:,.2f}/month")
                                return True, {"quotes_generated": True, "lead_data": test_lead}
                            else:
                                print("   ❌ CRITICAL: Quotes were NOT generated")
                                print("   🚨 This confirms the reported issue!")
                                return False, {"quotes_generated": False, "lead_data": test_lead}
                        else:
                            print(f"   ❌ No lead found for phone {test_phone}")
                            return False, {"quotes_generated": False, "lead_data": None}
                    else:
                        print("   ❌ Invalid leads data format")
                        return False, {}
                else:
                    print(f"   ❌ Failed to retrieve leads: {leads_response.status_code}")
                    return False, {}
            else:
                print(f"   ❌ Vehicle data message failed: {response3.status_code}")
                return False, {}
        except Exception as e:
            print(f"   ❌ Vehicle data message error: {e}")
            return False, {}

    def run_tests(self):
        """Run all seeding tests"""
        print("🌱 TESTING QUOTE GENERATION AFTER DATABASE SEEDING - ProtegeYa Review Request")
        print("=" * 80)
        
        # Login first
        if not self.login_admin():
            print("❌ Cannot proceed without admin login")
            return False
        
        # Test 1: Direct quote endpoint
        quote_success, quotes = self.test_direct_quote_endpoint()
        
        # Test 2: WhatsApp flow
        whatsapp_success, whatsapp_result = self.test_whatsapp_flow()
        
        # Final results
        print("\n" + "=" * 80)
        print("🎯 FINAL TEST RESULTS")
        print("=" * 80)
        
        print(f"Direct Quote Endpoint: {'✅ WORKING' if quote_success else '❌ FAILED'}")
        print(f"WhatsApp Complete Flow: {'✅ WORKING' if whatsapp_success else '❌ FAILED'}")
        
        if quote_success and whatsapp_success:
            print("\n🎉 ALL TESTS PASSED - Quote generation is working correctly!")
            return True
        else:
            print("\n❌ SOME TESTS FAILED - Quote generation issues confirmed!")
            if not quote_success:
                print("   - Direct quote endpoint is not working")
            if not whatsapp_success:
                print("   - WhatsApp flow is not generating quotes")
            return False

if __name__ == "__main__":
    tester = QuoteSeedingTester()
    success = tester.run_tests()
    sys.exit(0 if success else 1)