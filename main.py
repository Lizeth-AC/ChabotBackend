from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import re
import logging

# ⚙️ Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn")

logger.info("🚀 Servicio FastAPI iniciado")

app = FastAPI(title="ChatBot Alexa Backend")

# ⚙️ Stopwords
stopwords = [
    "de", "la", "que", "el", "en", "y", "a", "los", "del", "se", "las", "por",
    "un", "para", "con", "no", "una", "su", "al", "lo", "como", "más", "pero",
    "sus", "le", "ya", "o", "este", "sí", "porque", "esta", "entre", "cuando",
    "muy", "sin", "sobre", "también", "me", "hasta", "hay", "donde", "quien",
    "desde", "todo", "nos", "durante", "todos", "uno", "les", "ni", "contra", "es",
    "otros", "ese", "eso", "ante", "ellos", "e", "esto", "mí", "antes", "algunos",
    "qué", "unos", "yo", "otro", "otras", "otra", "él", "tanto", "esa", "estos",
    "mucho", "quienes", "nada", "muchos", "cual", "poco", "ella", "estar", "estas",
    "algunas", "algo", "nosotros", "mi", "mis", "tú", "te", "ti", "tu", "tus", "si"
]

# ⚙️ Modelo para endpoint de prueba
class Mensaje(BaseModel):
    texto: str

# ⚙️ Cargar oraciones desde archivo
def cargar_texto(path="respuesta.txt"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            contenido = f.read()
        return [linea.strip() for linea in re.split(r'\n{2,}', contenido) if linea.strip()]
    except FileNotFoundError:
        logger.warning("Archivo 'respuesta.txt' no encontrado. Se usará base vacía.")
        return ["Base de datos vacía"]

# ⚙️ Tokenizar y limpiar
def tokenizar(texto):
    return re.findall(r'\b\w+\b', texto.lower())

def limpiar_palabras(palabras):
    return [p for p in palabras if p not in stopwords]

# ⚙️ Obtener respuesta
def obtener_respuesta(mensaje, oraciones):
    mensaje_limpio = mensaje.lower()

    # Respuestas rápidas
    if any(saludo in mensaje_limpio for saludo in ["hola", "buenos días", "buen dia", "buenas tardes", "buenas noches"]):
        return "¡Hola!👋 ¿En qué puedo ayudarte hoy?💬"
    if any(agradecer in mensaje_limpio for agradecer in ["gracias", "te lo agradezco"]):
        return "¡Con gusto!😊 Aquí estoy para lo que necesites.📝"
    if any(despedida in mensaje_limpio for despedida in ["adios", "chau", "chao", "hasta luego"]):
        return "¡Hasta luego!🙌 Espero que tengas un gran día.✨"

    # Búsqueda por coincidencias
    palabras_mensaje = limpiar_palabras(tokenizar(mensaje_limpio))
    max_coincidencias = 0
    oraciones_coincidentes = []

    for oracion in oraciones:
        palabras_oracion = tokenizar(oracion)
        coincidencias = [p for p in palabras_mensaje if p in palabras_oracion]

        if len(coincidencias) > max_coincidencias:
            max_coincidencias = len(coincidencias)
            oraciones_coincidentes = [oracion]
        elif len(coincidencias) == max_coincidencias and max_coincidencias > 0:
            oraciones_coincidentes.append(oracion)

    if not oraciones_coincidentes:
        return "No he encontrado coincidencias relevantes en mi base de datos.🙁\nPor favor especifique su pregunta.💬"

    return "\n\n".join(oraciones_coincidentes)

# ⚙️ Cargar oraciones al iniciar
oraciones = cargar_texto()

# 🔹 Endpoint de prueba
@app.post("/preguntar")
async def preguntar(mensaje: Mensaje):
    logger.info(f"POST /preguntar recibido: {mensaje.texto}")
    respuesta = obtener_respuesta(mensaje.texto, oraciones)
    return {"respuesta": respuesta}

# 🔹 Endpoint raíz (para test de Render)
@app.get("/")
async def root():
    logger.info("GET / recibido")
    return JSONResponse({
        "version": "1.0",
        "response": {
            "shouldEndSession": False,
            "outputSpeech": {
                "type": "PlainText",
                "text": "Hola, el servicio de ChatBot Alexa en Render está activo 🚀"
            }
        }
    })

# 🔹 Endpoint para Alexa
@app.post("/alexa")
async def alexa_webhook(request: Request):
    try:
        body = await request.json()
        logger.info(f"POST /alexa recibido: {body}")
        req_type = body.get("request", {}).get("type", "")

        if req_type == "LaunchRequest":
            respuesta = "¡Hola! Bienvenido a ChatBot Teddy. ¿En qué puedo ayudarte?"
        elif req_type == "IntentRequest":
            slots = body.get("request", {}).get("intent", {}).get("slots", {})
            consulta = slots.get("consulta", {}).get("value", "")
            if consulta:
                respuesta = obtener_respuesta(consulta, oraciones)
            else:
                respuesta = "No entendí tu consulta. Por favor repite."
        else:
            respuesta = "No entiendo tu solicitud."

        return {
            "version": "1.0",
            "response": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": respuesta
                },
                "shouldEndSession": False
            }
        }

    except Exception as e:
        logger.error(f"Error en /alexa: {e}", exc_info=True)
        return {
            "version": "1.0",
            "response": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": f"Ocurrió un error: {str(e)}"
                },
                "shouldEndSession": True
            }
        }
