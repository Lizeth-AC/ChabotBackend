from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import re

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

# ⚙️ Modelo para endpoint normal
class Mensaje(BaseModel):
    texto: str

# ⚙️ Cargar oraciones desde archivo
def cargar_texto(path="Respuestas_ChatBot.txt"):
    with open(path, "r", encoding="utf-8") as f:
        contenido = f.read()
    return [linea.strip() for linea in re.split(r'\n{2,}', contenido) if linea.strip()]

# ⚙️ Tokenizar y limpiar
def tokenizar(texto):
    return re.findall(r'\b\w+\b', texto.lower())

def limpiar_palabras(palabras):
    return [p for p in palabras if p not in stopwords]

# ⚙️ Obtener respuesta
def obtener_respuesta(mensaje, oraciones):
    mensaje_limpio = mensaje.lower()

    if any(saludo in mensaje_limpio for saludo in ["hola", "buenos días", "buen dia", "buenas tardes", "buenas noches"]):
        return "¡Hola!👋 ¿En qué puedo ayudarte hoy?💬"
    if any(agradecer in mensaje_limpio for agradecer in ["gracias", "te lo agradezco"]):
        return "¡Con gusto!😊 Aquí estoy para lo que necesites.📝"
    if any(despedida in mensaje_limpio for despedida in ["adios", "chau", "chao", "hasta luego"]):
        return "¡Hasta luego!🙌 Espero que tengas un gran día.✨"

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

# 🔹 Endpoint normal (para pruebas con Postman o navegador)
@app.post("/preguntar")
async def preguntar(mensaje: Mensaje):
    respuesta = obtener_respuesta(mensaje.texto, oraciones)
    return {"respuesta": respuesta}

# 🔹 Endpoint para Alexa (respuesta en formato Alexa JSON)
@app.post("/alexa")
async def alexa_webhook(request: Request):
    try:
        body = await request.json()  # 👈 obtiene el JSON que Alexa envía
        consulta = body["request"]["intent"]["slots"]["consulta"]["value"]
        respuesta = obtener_respuesta(consulta, oraciones)

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
        return JSONResponse(status_code=400, content={"error": str(e)})
