import os
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

# Inicializa el cliente de Notion
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

notion = Client(auth=NOTION_TOKEN) if NOTION_TOKEN else None

def get_lead_by_phone(phone: str):
    """Busca si el cliente ya existe en Notion por su número de teléfono."""
    if not notion:
        print("Error: NOTION_TOKEN no configurado.")
        return None
    try:
        response = notion.databases.query(
            database_id=NOTION_DATABASE_ID,
            filter={
                "property": "Telefono",
                "rich_text": {
                    "equals": phone
                }
            }
        )
        results = response.get("results")
        if results and len(results) > 0:
            return results[0]
        return None
    except Exception as e:
        print(f"Error consultando Notion: {e}")
        return None

def update_notion_crm(phone: str, nombre: str, empresa: str, vehiculo: str, interes: str, estado: str, monto_cotizado: int, prioridad: str) -> str:
    """
    Crea o actualiza un registro en la base de datos CRM de Notion.
    Esta función será llamada automáticamente por Gemini cuando detecte la información.
    """
    if not notion:
        return "Error: Integración con Notion no configurada."

    try:
        # 1. Verificar si ya existe
        existing_page = get_lead_by_phone(phone)
        
        # 2. Preparar las propiedades
        properties = {}
        
        if nombre:
            properties["Nombre"] = {"title": [{"text": {"content": nombre}}]}
        if phone:
            properties["Telefono"] = {"rich_text": [{"text": {"content": phone}}]}
        if empresa:
            properties["Empresa"] = {"rich_text": [{"text": {"content": empresa}}]}
        if vehiculo:
            properties["Vehiculo"] = {"rich_text": [{"text": {"content": vehiculo}}]}
        if interes:
            properties["Interes"] = {"rich_text": [{"text": {"content": interes}}]}
        if estado:
            properties["Estado"] = {"select": {"name": estado}}
        if monto_cotizado > 0:
            properties["Monto Cotizado"] = {"number": monto_cotizado}
        if prioridad:
            properties["Prioridad"] = {"select": {"name": prioridad}}

        # 3. Actualizar o Crear
        if existing_page:
            page_id = existing_page["id"]
            notion.pages.update(page_id=page_id, properties=properties)
            print(f"Lead actualizado en Notion: {phone}")
            return f"Información del cliente {nombre} actualizada exitosamente en Notion."
        else:
            notion.pages.create(
                parent={"database_id": NOTION_DATABASE_ID},
                properties=properties
            )
            print(f"Nuevo Lead creado en Notion: {phone}")
            return f"Nuevo cliente {nombre} registrado exitosamente en Notion."
            
    except Exception as e:
        print(f"Error escribiendo en Notion: {e}")
        return f"Hubo un error al guardar en Notion: {str(e)}"
