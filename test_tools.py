import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("Testing WITHOUT tools...")
try:
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents="Hola"
    )
    print("Success:", response.text)
except Exception as e:
    print("Error WITHOUT tools:", e)

print("\nTesting WITH simple tool...")
def dummy_tool(x: int) -> int:
    """Returns x"""
    return x

try:
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents="Hola",
        config=types.GenerateContentConfig(
            tools=[dummy_tool]
        )
    )
    print("Success WITH tool:", response.text)
except Exception as e:
    print("Error WITH tool:", e)

print("\nTesting WITH notion_tools...")
from notion_tools import update_notion_crm
try:
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents="Hola",
        config=types.GenerateContentConfig(
            tools=[update_notion_crm]
        )
    )
    print("Success WITH notion_tools:", response.text)
except Exception as e:
    print("Error WITH notion_tools:", e)
