import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

versions = ['v1', 'v1beta', 'v1alpha']
models = ['gemini-1.5-flash', 'gemini-1.5-flash-001', 'gemini-1.5-flash-002']

for v in versions:
    for m in models:
        print(f"\nTesting {v} with {m}...")
        try:
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"), http_options={'api_version': v})
            response = client.models.generate_content(
                model=m,
                contents="Hola"
            )
            print("SUCCESS:", response.text)
        except Exception as e:
            print("ERROR:", e)
