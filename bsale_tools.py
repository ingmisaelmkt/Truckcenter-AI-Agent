import os
import json
import uuid
import time
import requests
from dotenv import load_dotenv
from wacrm_tools import enviar_pdf_por_wacrm

load_dotenv()
BSALE_TOKEN = os.getenv("BSALE_API_TOKEN")
# El ID del tipo de documento "Cotización" (o "Nota de Venta") en TU cuenta
# de Bsale. Es específico de cada cuenta — se saca con:
#   curl -H "access_token: TU_TOKEN" https://api.bsale.cl/v1/document_types.json
BSALE_QUOTE_DOCUMENT_TYPE_ID = os.getenv("BSALE_QUOTE_DOCUMENT_TYPE_ID")
# Opcional — sucursal donde se emite el documento. Si no se setea, Bsale usa
# la sucursal por defecto de la cuenta.
BSALE_OFFICE_ID = os.getenv("BSALE_OFFICE_ID")

HEADERS = {
    "access_token": BSALE_TOKEN,
    "Accept": "application/json",
    "Content-Type": "application/json",
}

QUOTES_DIR = os.path.join(os.path.dirname(__file__), "quotes")
os.makedirs(QUOTES_DIR, exist_ok=True)


def consultar_stock_bsale(producto: str) -> str:
    """
    Busca un producto o servicio en el inventario de Bsale y devuelve su
    precio, stock y una referencia [ref:ID] que se debe usar tal cual al
    llamar a generar_cotizacion_pdf — nunca inventes ese número.
    Útil para cualquier ítem del catálogo: neumáticos, lubricantes,
    baterías, repuestos o servicios.

    Args:
        producto (str): Nombre del producto o servicio a buscar.
    """
    if not BSALE_TOKEN:
        return "Error: BSALE_API_TOKEN no configurado en el sistema."

    url = f"https://api.bsale.cl/v1/variants.json?description={producto}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])

            if not items:
                return f"No encontré '{producto}' en el inventario actual de Bsale. Sugiere una alternativa técnica."

            resultados = []
            for item in items[:5]:  # Mostrar máximo 5 resultados
                nombre = item.get("description", "Sin nombre")
                precio = item.get("netUnitValue", 0)
                variant_id = item.get("id")
                resultados.append(f"- {nombre}: ${precio} (Neto) [ref:{variant_id}]")

            return f"Resultados encontrados en Bsale para '{producto}':\n" + "\n".join(resultados)
        else:
            return f"Error consultando Bsale. Código HTTP: {response.status_code}"
    except Exception as e:
        return f"Error de conexión con Bsale: {str(e)}"


def _epoch(days_from_now: int = 0) -> int:
    return int(time.time()) + days_from_now * 86400


def generar_cotizacion_pdf(
    rut_cliente: str,
    items_json: str,
    phone_number: str,
    email_cliente: str = "",
) -> str:
    """
    Genera la cotización REAL en Bsale (no simulada), descarga el PDF y lo
    envía al cliente por WhatsApp a través de wacrm. Si el cliente dio su
    email, Bsale se lo manda también por correo automáticamente.
    Usa esta herramienta SOLO cuando el cliente confirme que quiere la
    cotización formal, y solo con [ref:ID] reales que ya te dio
    consultar_stock_bsale — nunca inventes un ID.

    Args:
        rut_cliente (str): RUT del cliente si es empresa (ej: 76449954-9).
            Si no lo tienes, usa 'Consumidor Final'.
        items_json (str): Lista en formato JSON de los ítems a cotizar,
            ej: '[{"variant_id": 4521, "quantity": 2}, {"variant_id": 890, "quantity": 1}]'.
            variant_id es el número que viene en [ref:N] de consultar_stock_bsale.
        email_cliente (str): Email del cliente, SOLO si lo dio voluntariamente.
            Déjalo vacío si no lo tienes — la cotización se manda igual por WhatsApp.
    """
    if not BSALE_TOKEN:
        return "Error: BSALE_API_TOKEN no configurado en el sistema."
    if not BSALE_QUOTE_DOCUMENT_TYPE_ID:
        return "Error: BSALE_QUOTE_DOCUMENT_TYPE_ID no configurado — no se puede generar el documento en Bsale."

    try:
        items = json.loads(items_json)
        if not isinstance(items, list) or not items:
            raise ValueError("items_json debe ser una lista no vacía")
    except Exception as e:
        return f"No pude leer los ítems de la cotización ({e}). Vuelve a intentar con un JSON válido de [{{'variant_id':..,'quantity':..}}]."

    details = []
    for it in items:
        variant_id = it.get("variant_id")
        quantity = it.get("quantity", 1)
        if not variant_id:
            continue
        details.append({"variantId": variant_id, "quantity": quantity})

    if not details:
        return "No se encontraron ítems válidos (variant_id) para cotizar."

    payload = {
        "documentTypeId": int(BSALE_QUOTE_DOCUMENT_TYPE_ID),
        "emissionDate": _epoch(0),
        "expirationDate": _epoch(7),
        "declareSii": 0,  # una cotización no es un documento tributario
        "client": {
            "code": rut_cliente,
            **({"email": email_cliente} if email_cliente else {}),
        },
        "details": details,
    }
    if BSALE_OFFICE_ID:
        payload["officeId"] = int(BSALE_OFFICE_ID)
    if email_cliente:
        payload["sendEmail"] = True

    try:
        res = requests.post(
            "https://api.bsale.cl/v1/documents.json",
            headers=HEADERS,
            json=payload,
            timeout=20,
        )
    except Exception as e:
        return f"Error de conexión con Bsale al generar la cotización: {e}"

    if res.status_code not in (200, 201):
        print(f"[BSALE API] Error {res.status_code}: {res.text}")
        return f"Bsale rechazó la cotización (código {res.status_code}). Avísale al cliente que hubo un problema técnico y que un asesor la confirma en breve."

    doc = res.json()
    url_pdf = doc.get("urlPdf")
    if not url_pdf:
        return "Bsale creó el documento pero no devolvió el PDF. Un asesor debe revisarlo manualmente en Bsale."

    # Descarga el PDF con nuestro propio token (no confiamos en que
    # urlPdf sea públicamente accesible sin autenticación).
    try:
        pdf_res = requests.get(url_pdf, headers=HEADERS, timeout=20)
        pdf_res.raise_for_status()
    except Exception as e:
        return f"La cotización se generó en Bsale, pero no pude descargar el PDF ({e}). Revísala directo en Bsale."

    filename = f"{uuid.uuid4().hex}.pdf"
    filepath = os.path.join(QUOTES_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(pdf_res.content)

    enviado = enviar_pdf_por_wacrm(phone_number, filename)

    if enviado:
        aviso_email = " También se le envió una copia por correo." if email_cliente else ""
        return f"✅ Cotización real generada en Bsale y enviada como PDF por este mismo WhatsApp.{aviso_email} Cierra la conversación invitando al cliente a confirmar la reserva."
    else:
        return f"✅ Cotización real generada en Bsale (folio guardado), pero el envío automático por WhatsApp falló — comparte este link con el cliente manualmente: {url_pdf}"
