import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Dominio real de tu wacrm (ej: https://wacrm-wacrm.ymduev.easypanel.host) —
# SIN slash final. Y una API key creada en wacrm -> Settings -> API keys,
# con los scopes messages:send y contacts:write.
WACRM_BASE_URL = os.getenv("WACRM_BASE_URL", "").rstrip("/")
WACRM_API_KEY = os.getenv("WACRM_API_KEY")
# Dominio público del propio agente (este servicio) en EasyPanel — se
# usa para construir la URL del PDF que wacrm/Meta necesitan poder
# descargar. SIN slash final.
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")

WACRM_HEADERS = {
    "Authorization": f"Bearer {WACRM_API_KEY}",
    "Content-Type": "application/json",
}


def update_wacrm_lead(phone_number: str, tags: list, note: str = "", deal_value: int = 0) -> str:
    """
    Agrega etiquetas al contacto en wacrm (ej: "B2B", "Alta Prioridad",
    "Neumáticos"). Llama a esta función en cuanto el cliente revele un
    dato relevante para clasificarlo — no esperes al final de la charla.

    Nota de alcance: la API pública de wacrm hoy solo permite gestionar
    etiquetas de contacto. `note` y `deal_value` quedan registrados en el
    log del agente para que un humano los traspase — wacrm todavía no
    expone un endpoint público para notas internas ni para crear Deals
    (es una mejora pendiente del lado de wacrm, no de este agente).

    Args:
        phone_number (str): El número de WhatsApp del cliente, en formato E.164 (ej: +56912345678).
        tags (list): Etiquetas descriptivas a agregar (ej: ["B2B", "Alta Prioridad", "Neumáticos"]).
        note (str): Resumen de lo que el cliente quiere — se loguea, no se persiste todavía en wacrm.
        deal_value (int): Monto total en pesos chilenos si ya se cotizó — se loguea, no se persiste todavía en wacrm.
    """
    if not WACRM_BASE_URL or not WACRM_API_KEY:
        print("[wacrm] WACRM_BASE_URL / WACRM_API_KEY no configurados — se omite la actualización.")
        return "No se pudo actualizar wacrm (credenciales no configuradas)."

    try:
        # 1) Find-or-create el contacto por teléfono.
        res = requests.post(
            f"{WACRM_BASE_URL}/api/v1/contacts",
            headers=WACRM_HEADERS,
            json={"phone": phone_number},
            timeout=10,
        )
        if res.status_code not in (200, 201):
            print(f"[wacrm] Error creando/buscando contacto: {res.status_code} {res.text}")
            return "No se pudo actualizar el contacto en wacrm."

        contact = res.json().get("data", {})
        contact_id = contact.get("id")
        existing_tags = [t["name"] for t in contact.get("tags", [])]

        # 2) Unimos las etiquetas nuevas con las que ya tenía (PATCH
        #    reemplaza la lista completa, así que hay que mandarla mezclada
        #    para no borrar etiquetas puestas antes).
        merged_tags = list(dict.fromkeys(existing_tags + list(tags)))

        patch_res = requests.patch(
            f"{WACRM_BASE_URL}/api/v1/contacts/{contact_id}",
            headers=WACRM_HEADERS,
            json={"tags": merged_tags},
            timeout=10,
        )
        if patch_res.status_code != 200:
            print(f"[wacrm] Error actualizando etiquetas: {patch_res.status_code} {patch_res.text}")
            return "No se pudieron guardar las etiquetas en wacrm."

        if note or deal_value:
            print(f"[wacrm] (pendiente de API) Nota: {note!r} | Monto: ${deal_value} | Tel: {phone_number}")

        return f"Etiquetas actualizadas en wacrm: {merged_tags}."
    except Exception as e:
        print(f"[wacrm] Error de conexión: {e}")
        return "No se pudo conectar con wacrm para actualizar el contacto."


def enviar_pdf_por_wacrm(phone_number: str, filename: str) -> bool:
    """
    Envía un PDF ya guardado en la carpeta pública `quotes/` de este
    agente como mensaje de documento por WhatsApp, a través de la API
    pública de wacrm (que es quien realmente habla con Meta).

    No es una tool para el modelo — la llama generar_cotizacion_pdf
    directamente después de descargar el PDF de Bsale.
    """
    if not WACRM_BASE_URL or not WACRM_API_KEY or not PUBLIC_BASE_URL:
        print("[wacrm] Faltan WACRM_BASE_URL / WACRM_API_KEY / PUBLIC_BASE_URL — no se envía el PDF.")
        return False

    media_url = f"{PUBLIC_BASE_URL}/quotes/{filename}"
    try:
        res = requests.post(
            f"{WACRM_BASE_URL}/api/v1/messages",
            headers=WACRM_HEADERS,
            json={
                "to": phone_number,
                "type": "document",
                "media_url": media_url,
                "filename": "Cotizacion_TruckCenter.pdf",
            },
            timeout=15,
        )
        if res.status_code != 201:
            print(f"[wacrm] Error enviando PDF: {res.status_code} {res.text}")
            return False
        return True
    except Exception as e:
        print(f"[wacrm] Error de conexión enviando PDF: {e}")
        return False
