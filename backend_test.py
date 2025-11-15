#!/usr/bin/env python3
"""
Backend API Testing for Siete CX Platform
Tests all Phase 0-4 endpoints as specified in the review request
"""

import requests
import json
import sys
from datetime import datetime

# Get backend URL from frontend .env (as per instructions)
BACKEND_URL = "https://siete-cx-deploy.preview.emergentagent.com/api"

# Test data as specified in review request
TEST_COMPANY = {
    "name": "Test Company",
    "subdomain": "testco", 
    "contact_email": "test@testco.com"
}

TEST_USER = {
    "email": "admin@testco.com",
    "password": "Admin123!",
    "full_name": "Test Admin",
    "role": "admin"
}

class SieteCXTester:
    def __init__(self):
        self.session = requests.Session()
        self.jwt_token = None
        self.company_id = None
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "base_url": BACKEND_URL,
            "tests": {},
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0
            }
        }
    
    def log_test(self, endpoint, method, status_code, response_data=None, error=None):
        """Log test results"""
        test_key = f"{method} {endpoint}"
        success = 200 <= status_code < 300
        
        self.results["tests"][test_key] = {
            "status_code": status_code,
            "success": success,
            "response_data": response_data,
            "error": str(error) if error else None
        }
        
        self.results["summary"]["total"] += 1
        if success:
            self.results["summary"]["passed"] += 1
            print(f"✅ {test_key}: {status_code}")
        else:
            self.results["summary"]["failed"] += 1
            print(f"❌ {test_key}: {status_code} - {error}")
    
    def test_endpoint(self, endpoint, method="GET", data=None, headers=None):
        """Generic endpoint tester"""
        url = f"{BACKEND_URL}{endpoint}"
        
        try:
            if method == "GET":
                response = self.session.get(url, headers=headers)
            elif method == "POST":
                response = self.session.post(url, json=data, headers=headers)
            elif method == "PUT":
                response = self.session.put(url, json=data, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            self.log_test(endpoint, method, response.status_code, response_data)
            return response
            
        except Exception as e:
            self.log_test(endpoint, method, 0, None, e)
            return None
    
    def test_basic_endpoints(self):
        """Test basic endpoints that should exist"""
        print("\n=== Testing Basic Endpoints ===")
        self.test_endpoint("/")
        self.test_endpoint("/status")
        
    def test_auth_endpoints(self):
        """Test Phase 0: Authentication endpoints"""
        print("\n=== Testing Phase 0: Auth & Users ===")
        
        # Test user creation (as per review request)
        user_data = {
            "email": TEST_USER["email"],
            "password": TEST_USER["password"],
            "full_name": TEST_USER["full_name"],
            "company_id": self.company_id,  # Will be set after company creation
            "role": 0  # Admin role as per review request
        }
        register_response = self.test_endpoint("/v1/users/", "POST", user_data)
        
        # Test user login
        login_data = {
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        }
        login_response = self.test_endpoint("/v1/auth/login", "POST", login_data)
        
        # Extract JWT token if login successful
        if login_response and login_response.status_code == 200:
            try:
                token_data = login_response.json()
                self.jwt_token = token_data.get("access_token") or token_data.get("token")
                if self.jwt_token:
                    print(f"🔑 JWT Token obtained: {self.jwt_token[:20]}...")
            except:
                pass
    
    def test_company_endpoints(self):
        """Test Phase 1: Company endpoints"""
        print("\n=== Testing Phase 1: Companies ===")
        
        # Create company (no auth needed as per review request)
        company_response = self.test_endpoint("/v1/company/", "POST", TEST_COMPANY)
        
        # Extract company_id if successful
        if company_response and company_response.status_code in [200, 201]:
            try:
                company_data = company_response.json()
                self.company_id = company_data.get("id") or company_data.get("company_id")
                if self.company_id:
                    print(f"🏢 Company ID obtained: {self.company_id}")
            except:
                pass
    
    def test_dashboard_endpoints(self):
        """Test Phase 2: Dashboard Config endpoints"""
        print("\n=== Testing Phase 2: Dashboard Configs ===")
        
        headers = {"Authorization": f"Bearer {self.jwt_token}"} if self.jwt_token else None
        
        # Test dashboard widgets (as per review request)
        self.test_endpoint("/v1/dashboard-config/widgets", "GET", headers=headers)
        
        # Test dashboard configs
        self.test_endpoint("/v1/dashboard-config/", "GET", headers=headers)
        
        # Test default dashboard layout
        self.test_endpoint("/v1/dashboard-config/default", "GET", headers=headers)
        
        # Create dashboard config
        dashboard_config = {
            "layout": "grid",
            "widgets": ["widget1", "widget2"],
            "theme": "default"
        }
        self.test_endpoint("/v1/dashboard-config/", "POST", dashboard_config, headers)
    
    def test_intelligence_endpoints(self):
        """Test Phase 3: Intelligence endpoints"""
        print("\n=== Testing Phase 3: Intelligence ===")
        
        headers = {"Authorization": f"Bearer {self.jwt_token}"} if self.jwt_token else None
        
        # Test intelligence insights (as per review request)
        self.test_endpoint("/v1/intelligence/insights", "GET", headers=headers)
        
        # Test intelligence insights summary
        self.test_endpoint("/v1/intelligence/insights/summary", "GET", headers=headers)
        
        # Test intelligence trends
        self.test_endpoint("/v1/intelligence/trends", "GET", headers=headers)
        
        # Test intelligence tags
        self.test_endpoint("/v1/intelligence/tags", "GET", headers=headers)
    
    def test_prompt_endpoints(self):
        """Test Phase 3: Prompt Manager endpoints"""
        print("\n=== Testing Phase 3: Prompt Manager ===")
        
        headers = {"Authorization": f"Bearer {self.jwt_token}"} if self.jwt_token else None
        
        # List prompts (as per review request)
        self.test_endpoint("/v1/prompts/", "GET", headers=headers)
        
        # Get active prompts
        self.test_endpoint("/v1/prompts/active", "GET", headers=headers)
        
        # Create prompt
        prompt_data = {
            "name": "Test Prompt AI",
            "content": "This is a test prompt for AI processing in Siete CX",
            "category": "customer_service"
        }
        self.test_endpoint("/v1/prompts/", "POST", prompt_data, headers)
    
    def test_theme_endpoints(self):
        """Test Phase 4: Theme endpoints"""
        print("\n=== Testing Phase 4: Themes ===")
        
        headers = {"Authorization": f"Bearer {self.jwt_token}"} if self.jwt_token else None
        
        # Get themes (as per review request)
        self.test_endpoint("/v1/theme/", "GET", headers=headers)
        
        # Update theme colors
        theme_data = {
            "primary_color": "#007bff",
            "secondary_color": "#6c757d",
            "accent_color": "#28a745"
        }
        self.test_endpoint("/v1/theme/", "PUT", theme_data, headers)
        
        # Get theme CSS
        self.test_endpoint("/v1/theme/css", "GET", headers=headers)
    
    def run_all_tests(self):
        """Run all test suites"""
        print(f"🚀 Starting Siete CX Platform API Tests")
        print(f"📍 Base URL: {BACKEND_URL}")
        print("=" * 60)
        
        # Test in the specified order (as per review request)
        self.test_basic_endpoints()
        self.test_company_endpoints()  # Create company first
        self.test_auth_endpoints()     # Then create user with company_id
        self.test_dashboard_endpoints()
        self.test_intelligence_endpoints()
        self.test_prompt_endpoints()
        self.test_theme_endpoints()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.results['summary']['total']}")
        print(f"✅ Passed: {self.results['summary']['passed']}")
        print(f"❌ Failed: {self.results['summary']['failed']}")
        
        if self.results['summary']['failed'] > 0:
            print(f"\n🔍 FAILED ENDPOINTS:")
            for test_name, result in self.results['tests'].items():
                if not result['success']:
                    print(f"  - {test_name}: {result['status_code']} - {result['error']}")
        
        # Save detailed results
        with open('/app/test_results_detailed.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        return self.results

if __name__ == "__main__":
    tester = SieteCXTester()
    results = tester.run_all_tests()
    
    # Exit with error code if tests failed
    if results['summary']['failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)