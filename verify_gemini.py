import asyncio
import os
import sys
from dotenv import load_dotenv

# Add src to sys.path to allow imports
sys.path.append(os.path.join(os.getcwd(), "src"))

from automation_agent.llm_client import LLMClient

# Load environment variables
load_dotenv()

async def main():
    print("Testing Gemini Integration...")
    
    # Check for API Key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not found in environment variables. Please check your .env file.")
        return

    print(f"Found GEMINI_API_KEY: {api_key[:4]}...{api_key[-4:]}")

    import google.generativeai as genai
    genai.configure(api_key=api_key)
    
    models_list = []
    print("\nAvailable models:")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
            models_list.append(m.name)
            
    with open("verification_result.txt", "w", encoding="utf-8") as f:
        f.write("Available models:\n" + "\n".join(models_list) + "\n\n")

    try:
        # Initialize Client
        client = LLMClient(provider="gemini")
        print("LLMClient initialized with provider='gemini'")
        
        # Test Generation
        prompt = "Explain the benefits of automated code review in one sentence."
        print(f"\nSending prompt: '{prompt}'")
        
        response = await client.generate(prompt)
        print("\nResponse from Gemini received.")
        
        # Write response to file to avoid encoding issues on console
        with open("verification_result.txt", "w", encoding="utf-8") as f:
            f.write(f"Success! Response: {response}")
        print("Response written to verification_result.txt")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        with open("verification_result.txt", "a", encoding="utf-8") as f:
            f.write(f"\nError: {e}\n{traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(main())
