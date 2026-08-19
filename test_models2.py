import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

models = ['gemini-1.5-pro', 'gemini-1.5-pro-001', 'gemini-1.5-pro-002', 'gemini-2.0-flash-exp', 'gemini-2.0-pro-exp']

for m in models:
    print(f"\nTesting {m}...")
    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model=m,
            contents="Hola"
        )
        print("SUCCESS:", response.text)
    except Exception as e:
        print("ERROR:", e)
