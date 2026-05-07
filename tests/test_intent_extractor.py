"""Test the Intent Extraction Stage"""
import sys
import os

# Add the project root directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from pipeline.stages.intent_extractor import IntentExtractor
from pipeline.stages.intent_validator import IntentValidator
from pipeline.utils.helpers import print_safe_json
import json

def test_basic_extraction():
    """Test with a simple prompt"""
    print("\n" + "="*60)
    print("TEST 1: Basic CRM Prompt")
    print("="*60)
    
    prompt = "Build a CRM with login, contacts, dashboard, and role-based access. Admins can see analytics."
    
    # Initialize stages
    extractor = IntentExtractor()
    validator = IntentValidator()
    
    # Run extraction
    print(f"\n📝 Input: {prompt}")
    result = extractor.execute(prompt)
    
    if result["success"]:
        intent = result["output"]
        print(f"\n✅ Extraction succeeded in {result['metrics']['duration']:.2f}s")
        print(f"\n📊 Extracted Intent:")
        print(f"   App Name: {intent.get('app_name')}")
        print(f"   App Type: {intent.get('app_type')}")
        print(f"   Features: {len(intent.get('features', []))}")
        print(f"   Roles: {len(intent.get('roles', []))}")
        print(f"   Entities: {len(intent.get('entities', []))}")
        print(f"   Business Rules: {len(intent.get('business_rules', []))}")
        
        # Validate
        validated = validator.execute(intent)
        if validated["success"]:
            validation = validated["output"].get("_validation", {})
            print(f"\n🔍 Validation:")
            print(f"   Valid: {validation.get('valid', False)}")
            print(f"   Issues: {len(validation.get('issues', []))}")
            print(f"   Warnings: {len(validation.get('warnings', []))}")
            
            if validation.get("warnings"):
                print("   Warnings:")
                for w in validation["warnings"]:
                    print(f"     ⚠ {w}")
        
        # Show full JSON
        print("\n📄 Full Intent JSON:")
        print_safe_json(intent, "Full Intent JSON")
        
        return True
    else:
        print(f"\n❌ Extraction failed: {result.get('error')}")
        return False

def test_vague_prompt():
    """Test with a vague prompt"""
    print("\n" + "="*60)
    print("TEST 2: Vague Prompt")
    print("="*60)
    
    prompt = "I want an app for my business"
    
    extractor = IntentExtractor()
    
    print(f"\n📝 Input: {prompt}")
    result = extractor.execute(prompt)
    
    if result["success"]:
        intent = result["output"]
        print(f"\n✅ Extraction succeeded")
        print(f"   App Name: {intent.get('app_name')}")
        print(f"   Assumptions: {intent.get('assumptions', [])}")
        return True
    else:
        print(f"\n❌ Failed: {result.get('error')}")
        return False

def test_complex_prompt():
    """Test with the demo task example"""
    print("\n" + "="*60)
    print("TEST 3: Complex Prompt (from demo task)")
    print("="*60)
    
    prompt = "Build a CRM with login, contacts, dashboard, role-based access, and premium plan with payments. Admins can see analytics."
    
    extractor = IntentExtractor()
    
    print(f"\n📝 Input: {prompt}")
    result = extractor.execute(prompt)
    
    if result["success"]:
        intent = result["output"]
        print(f"\n✅ Extraction succeeded in {result['metrics']['duration']:.2f}s")
        
        # Check specific features
        features = [f['name'] for f in intent.get('features', [])]
        print(f"\n   Features found: {features}")
        
        # Check if premium/payment was detected
        has_premium = any('premium' in f.lower() or 'payment' in f.lower() for f in features)
        print(f"   Premium/Payment detected: {'✅' if has_premium else '❌'}")
        
        # Check roles
        roles = [r['name'] for r in intent.get('roles', [])]
        print(f"   Roles: {roles}")
        
        return True
    else:
        print(f"\n❌ Failed: {result.get('error')}")
        return False

if __name__ == "__main__":
    print("\n🧪 Testing Intent Extraction Stage")
    print("="*60)
    
    results = []
    results.append(test_basic_extraction())
    results.append(test_vague_prompt())
    results.append(test_complex_prompt())
    
    print("\n" + "="*60)
    print(f"RESULTS: {sum(results)}/{len(results)} tests passed")
    print("="*60)