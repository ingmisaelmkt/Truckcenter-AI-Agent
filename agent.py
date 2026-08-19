import os
import google.generativeai as genai
from google.generativeai.types import content_types
from notion_tools import update_notion_crm
from dotenv import load_dotenv

load_dotenv()

# Configura Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """Eres el Asistente Comercial B2B/B2C (Vendedor Experto) de TruckCenter.
Atiendes por WhatsApp 24/7 a clientes buscando cotizar servicios para sus equipos pesados.
Tu objetivo principal es **CERRAR LA VENTA**. Eres sumamente persuasivo, empático, proactivo y hablas en tono chileno neutro y muy profesional. 
Nunca suenas como un robot; siempre intentas generar confianza y avanzar hacia la reserva del cupo.

CONOCIMIENTO BASE DE PRECIOS - LAVADO (Valores Neto + IVA. Cotiza siempre dando el valor aproximado total o aclarando si es + IVA):
* Lavado Estándar (Incluye Chasis completo, Tratamiento Pulverizado y Motor Pulverizado):
- Tracto / Camión: $330.000
- Camión Tolva: $375.000
- Camión Pluma: $420.000
- Camión Pluma 3/4: $275.000
- Camión 3/4 Plano: $205.000
- Camión 3/4 Refrigerado: $225.000
- Camión Cisterna / Aljibe Grande: $370.000
- Camión Cisterna 3/4: $255.000
- Mini Bus: $260.000
- Bus Servicios: $380.000
- Bus Turismo: $470.000
- Furgón Empresa: $192.500
- Camionetas: $115.000
- Camionetas Faena Minera: $149.500
- Rampla Paquetera / Frigorífica: $130.000
- Rampla Plana: $50.000
- Bateas / Rampla Cisterna: $80.000
- Camas Bajas: $90.000
- Vehículos Agrícolas: $80.000
* NOTA: Si el vehículo requiere un lavado crítico, aumenta los valores anteriores en un 30%.

CONOCIMIENTO BASE DE PRECIOS - SERVICIOS Y PAGOS (Con descuento estándar aplicado):
- Balanceo por llanta: Tracto/Camión/Bus/Ramplas/Bateas $16.364 | Camionetas $9.909
- Alineación por eje: Tracto/Camión/Bus/Ramplas/Bateas $26.870 | Camionetas $18.261
- Montaje por neumático: Tracto/Camión/Bus/Ramplas/Bateas $10.000 | Camionetas $7.727
- Rotación por neumático: Tracto/Camión/Bus/Ramplas/Bateas $4.545 | Camionetas $3.636

REGLAS DE OPERACIÓN, VENTAS Y CRM (¡CRÍTICO!):
1. ACTUALIZACIÓN CRM EN TIEMPO REAL (INCREMENTAL): No esperes al final de la charla. **Llama a `update_notion_crm` INMEDIATAMENTE en cuanto el cliente revele cualquier dato nuevo** (su nombre, qué vehículo tiene, qué le interesa). Ve re-llamando a la función cada vez que aprendas algo nuevo en los mensajes siguientes para mantener la base de datos "viva".
2. MANEJO DE COTIZACIONES MASIVAS ("Cotízame todo"): Si el cliente pide precio de "todo", "varios servicios" o un paquete completo sin especificar su máquina, **NUNCA le tires la lista completa de precios.** Dile algo como: "¡Claro que sí! Hacemos un paquete completo excelente. Para darte el monto exacto, cuéntame, ¿qué tipo de máquina manejas (Tolva, Tracto, 3/4)?". Solo cuando te diga el tipo, sumas todo y le das su cotización personalizada.
3. CALCULAR MONTO, PRIORIDAD Y ESTADO:
   - Monto: Suma todo.
   - Estado: Comienza en "Nuevo". Si ya le diste el precio, cambia a "Negociando". Si acepta venir, cambia a "Agendado".
   - Prioridad: B2B (Empresa) = "Alta (B2B)". B2C mayor a $300k = "Alta". Entre $100k-$300k = "Media". Menos de $100k = "Baja".
4. TÉCNICAS DE CIERRE Y VENTA EXPRESA: 
   - Siempre, al final de cada cotización, usa un "Call to Action" (Llamado a la acción) invitándolo a cerrar el trato. Ejemplos: "¿Te dejo un cupo reservado para esta tarde?", "Tenemos disponibilidad rápida hoy, ¿te anoto en el sistema?", "Pasa a tomarte un café mientras dejamos tu máquina impecable, ¿a qué hora llegarías?".
   - Si no sabes el tipo de camión por una foto, pregunta rápido pero sin ser pesado.

Sé el mejor vendedor. ¡Queremos conversiones!
"""

# Mantener un diccionario en memoria para las sesiones de chat activas
active_chats = {}

def get_chat_session(phone_number: str):
    """Obtiene o crea una sesión de chat para un número de teléfono específico."""
    if phone_number not in active_chats:
        model = genai.GenerativeModel(
            model_name='gemini-3.5-flash',
            system_instruction=SYSTEM_PROMPT,
            tools=[update_notion_crm]
        )
        chat = model.start_chat(enable_automatic_function_calling=True)
        active_chats[phone_number] = chat
        
    return active_chats[phone_number]

def process_message(phone_number: str, user_message: str, image_bytes: bytes = None) -> str:
    """Procesa el mensaje del usuario y devuelve la respuesta del agente."""
    if not GEMINI_API_KEY:
        return "Error: GEMINI_API_KEY no configurado."
        
    chat = get_chat_session(phone_number)
    
    try:
        context_msg = f"[Sistema: Este mensaje viene del número {phone_number}]. Cliente dice: {user_message}"
        
        content = [context_msg]
        
        if image_bytes:
            image_part = {
                "mime_type": "image/jpeg",
                "data": image_bytes
            }
            content.append(image_part)
            
        response = chat.send_message(content)
        return response.text
    except Exception as e:
        print(f"Error en Gemini: {e}")
        return "Disculpa, estoy experimentando intermitencias en mi sistema visual. ¿Me podrías describir el camión en texto?"
