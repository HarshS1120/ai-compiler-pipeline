"""Basic test to verify Groq setup"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

from pipeline.config import PipelineConfig, IntentSchema
from pipeline.utils.llm import LLMHelper

def test_config():
    """Test configuration"""
    config = PipelineConfig()
    assert "llama" in config.MODEL_NAME.lower()
    print(f"✓ Config loaded. Model: {config.MODEL_NAME}")
    return True

def test_schemas():
    """Test Pydantic schemas"""
    intent = IntentSchema(
        app_name="Test CRM",
        app_type="CRM",
        features=[],
        roles=[],
        entities=[],
        business_rules=[]
    )
    print(f"✓ Schema created: {intent.app_name}")
    return True

def test_groq_connection():
    """Test Groq API connection"""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your_key_here":
        print("⚠ GROQ_API_KEY not set. Skipping API test.")
        print("  Get your key at: https://console.groq.com/keys")
        return False
    
    try:
        llm = LLMHelper()
        result = llm.complete(
            system_prompt="You are a test assistant. Respond with ONLY valid JSON.",
            user_prompt='Say hello in JSON format: {"message": "your hello"}',
            max_tokens=50
        )
        
        if "message" in result:
            print(f"✓ Groq API connected! Response: {result['message']}")
            return True
        else:
            print(f"⚠ Unexpected response: {result}")
            return False
            
    except Exception as e:
        print(f"✗ Groq API error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Testing Groq Pipeline Setup")
    print("=" * 50)
    
    test_config()
    test_schemas()
    test_groq_connection()
    
    print("\n✅ Setup tests complete!")