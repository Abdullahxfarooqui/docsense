"""
API Connection Test - Verify GROQ and OpenRouter APIs

Run this script to test both API connections before using the app.
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_groq():
    """Test GROQ API connection."""
    print("\n🔍 Testing GROQ API...")
    try:
        client = OpenAI(
            base_url=os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
            api_key=os.getenv("GROQ_API_KEY")
        )
        
        response = client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            messages=[
                {"role": "user", "content": "Say 'Hello from GROQ!' in exactly 3 words."}
            ],
            max_tokens=50
        )
        
        answer = response.choices[0].message.content
        print(f"✅ GROQ API: Working!")
        print(f"   Response: {answer}")
        return True
        
    except Exception as e:
        print(f"❌ GROQ API: Failed!")
        print(f"   Error: {str(e)}")
        return False


def test_openrouter():
    """Test OpenRouter API connection."""
    print("\n🔍 Testing OpenRouter API...")
    try:
        client = OpenAI(
            base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            api_key=os.getenv("OPENROUTER_API_KEY")
        )
        
        response = client.chat.completions.create(
            model=os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct:free"),
            messages=[
                {"role": "user", "content": "Say 'Hello from Mistral!' in exactly 3 words."}
            ],
            max_tokens=50
        )
        
        answer = response.choices[0].message.content
        print(f"✅ OpenRouter API: Working!")
        print(f"   Response: {answer}")
        return True
        
    except Exception as e:
        print(f"❌ OpenRouter API: Failed!")
        print(f"   Error: {str(e)}")
        return False


def main():
    """Run all API tests."""
    print("=" * 50)
    print("🧪 DocSense API Connection Test")
    print("=" * 50)
    
    # Check environment variables
    print("\n📋 Checking environment variables...")
    
    groq_key = os.getenv("GROQ_API_KEY")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    
    if not groq_key:
        print("❌ GROQ_API_KEY not found in .env")
    else:
        print(f"✅ GROQ_API_KEY found ({groq_key[:20]}...)")
    
    if not openrouter_key:
        print("❌ OPENROUTER_API_KEY not found in .env")
    else:
        print(f"✅ OPENROUTER_API_KEY found ({openrouter_key[:20]}...)")
    
    # Test APIs
    groq_ok = test_groq()
    openrouter_ok = test_openrouter()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    
    if groq_ok and openrouter_ok:
        print("✅ All APIs working! You're ready to use DocSense!")
    else:
        print("⚠️ Some APIs failed. Check your API keys in .env")
        if not groq_ok:
            print("   - GROQ API needs attention")
        if not openrouter_ok:
            print("   - OpenRouter API needs attention")
    
    print("=" * 50)


if __name__ == "__main__":
    main()
