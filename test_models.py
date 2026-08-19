import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

try:
    print("Listing models...")
    for model in client.models.list():
        if "flash" in model.name:
            print(model.name)
except Exception as e:
    print(f"Error listing models: {e}")

try:
    print("\nTesting gemini-1.5-flash-8b...")
    response = client.models.generate_content(
        model="gemini-1.5-flash-8b",
        contents="Hola"
    )
    print("Success 8b:", response.text)
except Exception as e:
    print("Error 8b:", e)

try:
    print("\nTesting gemini-1.5-flash...")
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents="Hola"
    )
    print("Success flash:", response.text)
except Exception as e:
    print("Error flash:", e)
