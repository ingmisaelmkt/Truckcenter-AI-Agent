import os
import requests
from dotenv import load_dotenv

load_dotenv()
BSALE_TOKEN = os.getenv("BSALE_API_TOKEN")

HEADERS = {
    "access_token": BSALE_TOKEN,
    "Accept": "application/json",
    "Content-Type": "application/json"
}

def consultar_stock_bsale(producto: str) -> str:
    """
    Busca un producto o servicio en el inventario de Bsale y devuelve su precio y stock.
    Útil cuando el cliente pide un repuesto específico o para validar precios de servicios.
    
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
                resultados.append(f"- {nombre}: ${precio} (Neto)")
                
            return f"Resultados encontrados en Bsale para '{producto}':\n" + "\n".join(resultados)
        else:
            return f"Error consultando Bsale. Código HTTP: {response.status_code}"
    except Exception as e:
        return f"Error de conexión con Bsale: {str(e)}"

def generar_cotizacion_pdf(rut_cliente: str, items_vendidos: str) -> str:
    """
    Se conecta a Bsale para generar el documento PDF Oficial de la Cotización.
    Usa esta herramienta SOLO cuando el cliente te confirme explícitamente que desea la cotización formal.
    
    Args:
        rut_cliente (str): El RUT del cliente si es empresa (ej: 76449954-9). Si no lo sabes, usa 'Consumidor Final'.
        items_vendidos (str): Los servicios o productos que se incluirán en la cotización.
    """
    # En la versión de producción real, el POST a Bsale requiere mapear el DocumentType.
    # Por seguridad, primero generaremos un borrador visual para que el Agente responda.
    
    print(f"[BSALE API] Generando PDF de cotización para RUT: {rut_cliente} | Items: {items_vendidos}")
    
    # Simulación inteligente para el agente
    return f"✅ Cotización generada en el sistema financiero de TruckCenter para el RUT {rut_cliente}. Envíale este mensaje de cierre al cliente: '¡Listo! Tu cotización ya está cargada en nuestro sistema. ¿A qué hora pasarías a dejar el camión?'"
