import os
# Fix para incompatibilidad de Google Protobuf con Python 3.14+
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import whatsapp_api
import agent

load_dotenv()

app = FastAPI(title="TruckCenter WhatsApp Webhook")

# Sirve los PDF de cotización generados en bsale_tools.py como archivos
# públicos — wacrm necesita una URL pública para poder enviarlos como
# documento adjunto por WhatsApp.
QUOTES_DIR = os.path.join(os.path.dirname(__file__), "quotes")
os.makedirs(QUOTES_DIR, exist_ok=True)
app.mount("/quotes", StaticFiles(directory=QUOTES_DIR), name="quotes")

WEBHOOK_VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN")
# Secreto compartido que wacrm envía como "Authorization: Bearer <secret>"
# al llamar a POST /api/chat. Si se deja vacío, /api/chat queda sin
# autenticación (solo aceptable para pruebas locales) — en producción
# DEBE estar seteado, porque el endpoint queda expuesto a internet.
WACRM_SHARED_SECRET = os.getenv("WACRM_SHARED_SECRET")

@app.get("/webhook")
async def verify_webhook(request: Request):
    """
    Este endpoint es requerido por Meta (Facebook) para verificar que el Webhook te pertenece.
    Meta enviará una petición GET con un token, el cual debe coincidir con WEBHOOK_VERIFY_TOKEN.
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == WEBHOOK_VERIFY_TOKEN:
            print("WEBHOOK VERIFICADO POR META EXITOSAMENTE!")
            # FastApi response for plain text needs to be returned as integer for challenge
            return Response(content=challenge, status_code=200)
        else:
            return Response(content="Token de verificación inválido.", status_code=403)
            
    return Response(content="Faltan parámetros", status_code=400)

@app.post("/webhook")
async def receive_message(request: Request):
    """
    Este endpoint recibe los mensajes POST de WhatsApp Cloud API en tiempo real.
    """
    try:
        body = await request.json()
        
        # Verificar si es un evento de mensaje válido de WhatsApp
        if "object" in body and body["object"] == "whatsapp_business_account":
            for entry in body.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    
                    # Validar si contiene un mensaje
                    if "messages" in value:
                        msg_info = value["messages"][0]
                        phone_number = msg_info["from"] # El numero del cliente
                        
                        # Extraemos el texto si es mensaje de texto
                        if msg_info["type"] == "text":
                            user_message = msg_info["text"]["body"]
                            print(f"\n[NUEVO MENSAJE] De: {phone_number} | Texto: {user_message}")
                            bot_response = agent.process_message(phone_number, user_message)
                            whatsapp_api.send_whatsapp_message(phone_number, bot_response)
                            
                        # Extraemos la imagen si es mensaje de imagen
                        elif msg_info["type"] == "image":
                            media_id = msg_info["image"]["id"]
                            print(f"\n[NUEVA IMAGEN] De: {phone_number} | Media ID: {media_id}")
                            
                            # Descargar la imagen
                            image_bytes = whatsapp_api.download_media(media_id)
                            
                            if image_bytes:
                                user_message = "[El usuario ha enviado una imagen de su camión/vehículo. Analízala para cotizar.]"
                                bot_response = agent.process_message(phone_number, user_message, image_bytes=image_bytes)
                                whatsapp_api.send_whatsapp_message(phone_number, bot_response)
                            else:
                                whatsapp_api.send_whatsapp_message(phone_number, "Recibí tu imagen, pero tuve un problema al descargarla. ¿Me podrías decir qué camión es?")
                            
        return {"status": "ok"}
    except Exception as e:
        print(f"Error procesando webhook: {e}")
        return {"status": "error"}

from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    phone_number: str
    message: str
    image_url: Optional[str] = None

@app.post("/api/chat")
async def wacrm_chat(request: Request, body: ChatRequest):
    """
    Este endpoint convierte al Agente en un Microservicio.
    WACRM puede enviar una petición POST aquí y el Agente devolverá la respuesta inteligente.
    """
    if WACRM_SHARED_SECRET:
        auth_header = request.headers.get("authorization", "")
        if auth_header != f"Bearer {WACRM_SHARED_SECRET}":
            return Response(content="Unauthorized", status_code=401)

    print(f"\n[WACRM SOLICITUD] De: {body.phone_number} | Texto: {body.message}")

    # Procesar con Gemini
    bot_response = agent.process_message(body.phone_number, body.message)

    return {"status": "success", "response": bot_response}

if __name__ == "__main__":
    import uvicorn
    # Corre el servidor en el puerto 8000
    print("Iniciando servidor de TruckCenter...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
