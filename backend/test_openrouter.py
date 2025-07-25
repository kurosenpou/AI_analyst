"""
Test script for OpenRouter integration
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.openrouter_client import get_openrouter_client
from services.ai_generator import AIReportGenerator

async def test_openrouter_integration():
    """Test OpenRouter integration"""
    
    print("🔧 Testing OpenRouter Integration...")
    print("=" * 50)
    
    # Test 1: Client initialization
    try:
        client = get_openrouter_client()
        print("✅ OpenRouter client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return
    
    # Test 2: Connection test
    print("\n🌐 Testing connectivity...")
    try:
        connection_results = await client.test_connection()
        print(f"OpenRouter connection: {'✅' if connection_results['openrouter'] else '❌'}")
        print(f"OpenAI fallback: {'✅' if connection_results['openai_fallback'] else '❌'}")
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return
    
    # Test 3: AI Generator
    print("\n🤖 Testing AI Generator...")
    try:
        ai_gen = AIReportGenerator()
        model_results = await ai_gen.test_models()
        
        for model_name, success in model_results.items():
            print(f"{model_name} model: {'✅' if success else '❌'}")
            
    except Exception as e:
        print(f"❌ AI Generator test failed: {e}")
        return
    
    # Test 4: Sample generation
    print("\n📝 Testing sample report generation...")
    try:
        sample_data = {
            "revenue": [100000, 120000, 150000],
            "expenses": [80000, 90000, 100000],
            "description": "Sample business data for testing"
        }
        
        report = await ai_gen.generate_business_plan(sample_data, "This is a test")
        print(f"✅ Sample report generated successfully ({len(report)} characters)")
        print(f"Preview: {report[:200]}...")
        
    except Exception as e:
        print(f"❌ Sample generation failed: {e}")
    
    print("\n🎉 OpenRouter integration test completed!")

if __name__ == "__main__":
    asyncio.run(test_openrouter_integration())
