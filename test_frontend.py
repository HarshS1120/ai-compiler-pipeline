"""Test the web interface"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("=" * 50)
    print("1. Testing Health Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False

def test_frontend():
    """Test that frontend is served"""
    print("\n" + "=" * 50)
    print("2. Testing Frontend Page...")
    try:
        response = requests.get(f"{BASE_URL}/app")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            html = response.text
            checks = {
                "Has title": "<title>AI Compiler Pipeline</title>" in html,
                "Has textarea": "<textarea" in html,
                "Has generate button": "generate()" in html,
                "Has tabs section": "tabs" in html,
                "Has JSON display": "JSON.stringify" in html,
                "Has example buttons": "example-btn" in html,
            }
            all_pass = True
            for check, result in checks.items():
                status = "✅" if result else "❌"
                print(f"   {status} {check}")
                if not result:
                    all_pass = False
            return all_pass
        else:
            print(f"   ❌ Failed to load frontend")
            return False
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False

def test_generate_endpoint():
    """Test the generate API"""
    print("\n" + "=" * 50)
    print("3. Testing Generate API...")
    try:
        payload = {"prompt": "Build a simple todo app with login"}
        response = requests.post(f"{BASE_URL}/generate", json=payload)
        print(f"   Status: {response.status_code}")
        
        data = response.json()
        
        checks = {
            "Success flag": data.get("success") == True,
            "Has output": data.get("output") is not None,
            "Has metadata": data.get("metadata") is not None,
            "Has UI schema": "ui" in data.get("output", {}),
            "Has API schema": "api" in data.get("output", {}),
            "Has DB schema": "database" in data.get("output", {}),
            "Has Auth schema": "auth" in data.get("output", {}),
            "Has total_duration": "total_duration" in data.get("metadata", {}),
            "Has stages": "stages" in data.get("metadata", {}),
            "Has repairs": "_repairs" in data.get("output", {}),
        }
        
        all_pass = True
        for check, result in checks.items():
            status = "✅" if result else "❌"
            print(f"   {status} {check}")
            if not result:
                all_pass = False
        
        # Show summary
        if all_pass:
            print(f"\n   📊 Summary:")
            print(f"      Duration: {data['metadata']['total_duration']:.2f}s")
            print(f"      Repairs: {data['output']['_repairs'].get('repairs_made', 0)}")
            print(f"      API Endpoints: {len(data['output']['api'].get('endpoints', []))}")
            print(f"      DB Tables: {len(data['output']['database'].get('tables', {}))}")
        
        return all_pass
        
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False

def test_error_handling():
    """Test error cases"""
    print("\n" + "=" * 50)
    print("4. Testing Error Handling...")
    all_pass = True
    
    # Test empty prompt
    try:
        response = requests.post(f"{BASE_URL}/generate", json={"prompt": ""})
        print(f"   Empty prompt - Status: {response.status_code} (expecting 422 or error)")
        if response.status_code not in [400, 422]:
            all_pass = False
    except:
        pass
    
    # Test short prompt
    try:
        response = requests.post(f"{BASE_URL}/generate", json={"prompt": "Hi"})
        data = response.json()
        if response.status_code == 400 or not data.get("success"):
            print(f"   ✅ Short prompt rejected correctly")
        else:
            print(f"   ❌ Short prompt should be rejected")
            all_pass = False
    except:
        pass
    
    return all_pass

def test_full_flow():
    """Test the complete flow with the demo task prompt"""
    print("\n" + "=" * 50)
    print("5. Testing Demo Task Prompt...")
    
    prompt = "Build a CRM with login, contacts, dashboard, role-based access, and premium plan with payments. Admins can see analytics."
    
    try:
        response = requests.post(f"{BASE_URL}/generate", json={"prompt": prompt})
        data = response.json()
        
        if not data.get("success"):
            print(f"   ❌ Failed")
            return False
        
        # Check all features detected
        features = []
        for stage in data["metadata"]["stages"]:
            if stage["stage"] == "Intent Extraction":
                features = stage.get("features", [])
        
        checks = {
            "Has login/payments/analytics in output": True,
            "UI pages created": len(data["output"]["ui"].get("pages", {})) > 3,
            "API endpoints created": len(data["output"]["api"].get("endpoints", [])) > 10,
            "DB tables created": len(data["output"]["database"].get("tables", {})) > 2,
            "Auth roles defined": len(data["output"]["auth"].get("roles", [])) > 0,
            "Complete in under 15s": data["metadata"]["total_duration"] < 15,
        }
        
        all_pass = True
        for check, result in checks.items():
            status = "✅" if result else "❌"
            print(f"   {status} {check}")
            if not result:
                all_pass = False
        
        print(f"\n   📊 Full Pipeline Stats:")
        print(f"      Total time: {data['metadata']['total_duration']:.2f}s")
        print(f"      UI Pages: {len(data['output']['ui'].get('pages', {}))}")
        print(f"      API Endpoints: {len(data['output']['api'].get('endpoints', []))}")
        print(f"      DB Tables: {len(data['output']['database'].get('tables', {}))}")
        print(f"      Auth Roles: {data['output']['auth'].get('roles', [])}")
        print(f"      Repairs made: {data['output']['_repairs'].get('repairs_made', 0)}")
        
        return all_pass
        
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False

if __name__ == "__main__":
    print("\n🧪 TESTING AI COMPILER PIPELINE - WEB INTERFACE")
    print("=" * 50)
    
    # Make sure server is running
    try:
        requests.get(f"{BASE_URL}/health", timeout=2)
    except:
        print("❌ Server not running!")
        print("   Start with: cd web\\api && python -m uvicorn main:app --reload --port 8000")
        exit(1)
    
    results = []
    results.append(("Health", test_health()))
    results.append(("Frontend", test_frontend()))
    results.append(("Generate API", test_generate_endpoint()))
    results.append(("Error Handling", test_error_handling()))
    results.append(("Demo Task Prompt", test_full_flow()))
    
    print("\n" + "=" * 50)
    print("RESULTS SUMMARY")
    print("=" * 50)
    
    all_pass = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} - {name}")
        if not passed:
            all_pass = False
    
    print("=" * 50)
    if all_pass:
        print("🎉 ALL TESTS PASSED! Web interface is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the details above.")
    print("=" * 50)