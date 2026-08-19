import os
import requests
from dotenv import load_dotenv

load_dotenv()

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")

def send_whatsapp_message(to: str, body: str):
    """
    Envía un mensaje de texto plano a un número usando la API Cloud de WhatsApp (Meta).
    Asegura que el número de destino esté en formato internacional sin el '+'.
    """
    if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_ID:
        print("Advertencia: Faltan credenciales de WhatsApp en el archivo .env. Imprimiendo mensaje por consola.")
        print(f">>> Mensaje para {to}: {body}")
        return

    url = f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {
            "body": body
        }
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        print(f"Mensaje enviado a {to} exitosamente.")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error enviando mensaje de WhatsApp a {to}: {e}")
        if e.response is not None:
            print(f"Detalle del error de Meta: {e.response.text}")
        return None

def download_media(media_id: str) -> bytes:
    """
    Obtiene la URL del media desde la API de Meta y descarga los bytes de la imagen.
    """
    if not WHATSAPP_TOKEN:
        print("Error: No hay WHATSAPP_TOKEN para descargar la imagen.")
        return None
        
    # Paso 1: Obtener la URL del media
    url = f"https://graph.facebook.com/v19.0/{media_id}"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    
    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        media_url = res.json().get("url")
        
        if not media_url:
            return None
            
        # Paso 2: Descargar los bytes de la imagen usando la URL (requiere Auth)
        img_res = requests.get(media_url, headers=headers)
        img_res.raise_for_status()
        return img_res.content
        
    except Exception as e:
        print(f"Error descargando media {media_id}: {e}")
        return None
