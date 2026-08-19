import os
import google.generativeai as genai
from dotenv import load_dotenv

os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")

try:
    response = model.generate_content("Hola")
    print("SUCCESS with google.generativeai:", response.text)
except Exception as e:
    print("ERROR with google.generativeai:", e)
