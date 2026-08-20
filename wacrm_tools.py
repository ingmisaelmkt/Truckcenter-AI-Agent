import os
import requests
from dotenv import load_dotenv

load_dotenv()
WACRM_API_KEY = os.getenv("WACRM_API_KEY", "dummy_key")
WACRM_URL = "http://localhost:3000/api" # URL típica interna de WACRM

def update_wacrm_lead(phone_number: str, tags: list, note: str, deal_value: int = 0) -> str:
    """
    Actualiza el perfil del cliente directamente en la interfaz de WACRM.
    Usa esta función para agregar etiquetas (ej: 'B2B', 'Alta Prioridad', 'Tolva'), 
    dejar notas internas para el equipo humano, o crear una oportunidad de negocio (Deal) con el monto.
    
    Args:
        phone_number (str): El número de WhatsApp del cliente.
        tags (list): Lista de etiquetas descriptivas (ej: ["B2B", "Alta Prioridad", "Camión Tolva"]).
        note (str): Un resumen de lo que el cliente quiere cotizar.
        deal_value (int): El monto total en pesos chilenos si ya se entregó una cotización.
    """
    print(f"\n[WACRM API] Actualizando Lead: {phone_number} | Tags: {tags} | Monto: ${deal_value}")
    print(f"[WACRM API] Nota agregada: {note}")
    
    # Aquí irá la llamada POST real a la API de WACRM (ej: /api/contacts/{phone}/tags)
    # Por ahora simulamos el éxito para que el Agente sepa que cumplió su tarea.
    return "Perfil de cliente actualizado exitosamente en WACRM (Etiquetas, Notas y Negocio)."
