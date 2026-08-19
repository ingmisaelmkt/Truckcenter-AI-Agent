import os
# Fix para incompatibilidad de Google Protobuf con Python 3.14+
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

from dotenv import load_dotenv
load_dotenv()

import agent

print("=============================================")
print("🚛 SIMULADOR DE CHAT TRUCKCENTER (TERMINAL) 🚛")
print("=============================================")

if not os.getenv("GEMINI_API_KEY"):
    print("\n❌ ALERTA: No has configurado tu GEMINI_API_KEY en el archivo .env.")
    print("El bot no podrá pensar ni responder hasta que pongas la clave de Google.\n")
else:
    print("\n✅ API Key de Gemini detectada. El cerebro del bot está listo.")

if not os.getenv("NOTION_TOKEN") or not os.getenv("NOTION_DATABASE_ID"):
    print("⚠️  AVISO: No has configurado Notion. El bot funcionará y cotizará, pero")
    print("los clientes no se guardarán en tu base de datos CRM aún.\n")

print("Escribe 'salir' para terminar el chat.\n")

numero_simulado = "+56900000000"

while True:
    user_input = input("Tú (Cliente): ")
    if user_input.lower() in ["salir", "exit", "quit"]:
        print("Cerrando simulador...")
        break
        
    # Llamamos a nuestro agente como si el mensaje viniera de WhatsApp
    bot_response = agent.process_message(numero_simulado, user_input)
    print(f"\nBot TruckCenter:\n{bot_response}\n")
    print("-" * 50)
