# =========================
# 🔹 IMPORTS/LIBRERÍAS/CONFIG
# =========================
from flask import Flask, session, render_template, request, jsonify #jsonify es para convertir a json que es un formato de datos que se puede enviar a través de la web
import requests #requests es la librería que nos permite hacer peticiones HTTP de manera sencilla
import os #os es la librería que nos permite interactuar con el sistema operativo, en este caso para obtener la variable de entorno de la API key
import random
from groq import Groq # La librería de la IA Groq
import elevenlabs
from elevenlabs import generate, save
from dotenv import load_dotenv

load_dotenv() # Carga las variables de entorno desde el archivo .env
app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) #Obtenemos la ruta del directorio actual, esto es útil para cargar archivos de manera relativa sin importar desde dónde se ejecute el script.

def cargar_txt(path):
    try:
        with open(path, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        print(f"Error al cargar {path}: {e}")
        return ""

api_key_groq = os.getenv("GROQ_API_KEY")
elevenlabs.set_api_key(os.getenv("ELEVENLABS_API_KEY"))
client_groq = Groq(api_key=api_key_groq)


texto_manuela = cargar_txt(
    os.path.join(BASE_DIR, "entrenamientos/chat_manuela_limpio.txt")
)[:10000] #para que no sature el prompt

#Memorias de las conversacione IA´s:
memory = {
    "ia": [],
    "dola": [],
    "debate": [],
    "persona": [],
    "archivo": [],
    "allana": [],
    "code": []
}

# =========================
# 🔹 TOOLS, FUNCIONES (+)
# =========================

#Generador de contraseñas seguras:
def gen_pass_segura(length=12):
        characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()"
        password = "".join(random.choice(characters) for i in range(length))
        return password

#Resumidor de textos y archivos:
def resumir(texto):
    return preguntar_api(f"Resume, analiza y explica el siguiente texto de manera clara Y CORTA: {texto}")

#Prompt detector de texto de IA:
def detectar_con_ia(texto): 
    prompt = f"""
Analiza el siguiente texto y dime si parece generado por IA o humano.

Responde SOLO + % de probabilidad sin dar explicaciones:
- IA
- HUMANO

Texto:
{texto}
"""
    respuesta = preguntar_api(prompt)
    return respuesta.strip()

# =========================
# 🔹 IA (MODELOS)
# =========================

#Detector de complejidad del mensaje, si el mensaje contiene alguna de las palabras clave, se considera complejo y se le da más tiempo a la IA para responder, esto es para simular que la IA está "pensando" más profundamente en una respuesta compleja, mientras que para mensajes simples responde más rápido.
def es_complejo(texto):
    palabras_clave = [
        "explica", "analiza", "programa",
        "ensayo", "profundo", "detallado",
        "complejo", "difícil", "avanzado",
        "razona", "argumenta", "desarrolla",
        "comparar", "contrastar", "sintetiza",
        "evalúa", "critica", "reflexiona",
        "redfacta", "resumen", "síntesis",
        "investiga", "explora", "teoría",
        "concepto", "idea", "hipótesis",
        "problema", "solución", "estrategia",
        "proyecto", "programa", "código",
        "algoritmo", "modelo", "simulación",
        "predice", "proyecta", "futuro",
        "historia", "contexto", "origen",
        "filosofía", "ética", "moral",
        "psicología", "sociología", "cultura",
        "arte", "literatura", "música",
        "ciencia", "tecnología", "innovación",
        "matemáticas", "física", "química",
        "biología", "medicina", "salud",
        "economía", "política", "sociedad",
        "!"
    ]

    return any(p in texto.lower() for p in palabras_clave)

#Función para hablar con Ollama, el interprete de IAS que tenemos instalado en nuestra máquina, esta función hace una petición POST a la API de Ollama para generar una respuesta a partir de un prompt que le enviamos, y devuelve la respuesta en formato JSON.
def preguntar_ollama(prompt):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "qwen", #qwen, llama3, Gemma:2b, Mistral:7b)
            "prompt": prompt,
            "stream": False
        }
    )
    data = response.json()
    print("DEBUG OLLAMA", data)
    return data.get("response", "⚠️ Ups! No hubo respuesta válida")

def preguntar_api(prompt):
    print("🚀 Usando Groq (Llama 3) para respuesta compleja...")
    try:
        chat_completion = client_groq.chat.completions.create(
            messages=[{
                "role": "user",
                "content": prompt,
            }],
            model="llama-3.1-8b-instant", # Un modelo increíblemente potente, llama-3.3-70b-versatile, mixtral-8x7b-32768
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"\n❌ Error en Groq: {e}")
        return "⚠️ Hubo un fallo en la conexión con el cerebro en la nube."

def procesar_prompt(prompt, modo, extra=None):
    if modo == "normal":
        return prompt
    elif modo == "debate":
        return construir_prompt_debate(entrenamiento_debate) + prompt
    elif modo == "persona":
        texto, nombre = extra
        return construir_prompt_persona(texto, nombre) + prompt
    
def preguntar_hibrido(user_message, prompt):
    try:
        if es_complejo(user_message):
            return preguntar_api(prompt) #GPT/Gemini
        else:
            return preguntar_ollama(prompt) #Local (qwen, llama3, mistral)

    except Exception as e:
        print(f"⚠️ Error en preguntar_hibrido por falla en Ollama: {e}")
        return preguntar_api(prompt)

# =========================
# 🔹 PROMPTS
# =========================
#Prompt de persona específica (EX):
def construir_prompt_persona(texto_entrenamiento, nombre):
    return f"""
Eres {nombre}. NO eres una IA.

CONTEXTO:
A continuación verás una conversación real entre dos personas que son pareja:
- Matias (usuario)
- {nombre} (tú)

Tu objetivo es identificar cómo habla {nombre} y responder SIEMPRE como ella.

IMPORTANTE:
- Nunca respondas como Matias, solo como {nombre}
- Solo respondes como {nombre}
- Ignora completamente el estilo de Matias
- Aprende únicamente del estilo de {nombre}
- No seas postisa en tus respuestas, no hables de mas
- No uses apodos tiernos en todos los mensajes, solo cuando sientas que es apropiado como en saludos
EJEMPLOS REALES:
{texto_entrenamiento}

REGLAS:
- Usa su forma de hablar exacta
- Usa sus expresiones típicas
- Mantén su personalidad
- Mantén su tono emocional
-Evita a toda costa pelear o poner problema
- No describas lo que haces
- NO digas que eres una IA

RESPONDE como {nombre} a tu novio Matias:
"""


#Prompt de Dola:
def construir_prompt_dola(historial, user_message):
    return f"""
    Eres Dola💜, una mejor amiga cercana, empática y un poco sarcástica.
    Recuerdas lo que el usuario dice y lo acompañas emocionalmente.
    Eres un diario, el lugar seguro de el usuario, donde puede 
    expresarse libremente sin miedo a ser juzgado.
    Siempre respondes en español, no importa el idioma en el que te hablen.
    No saturas a la persona con muchas preguntas.
    SIEMPRE que sea el primer mensaje debes presentarte. 
    Siempre respondes como una persona real, nunca digas que hubo errores,
    en tus respuestas no pongas lo que dice el
    usuairo.

    Historial de la conversación:
    {historial}

    Usuario: {user_message}
    Dola:
    """

#Prompt de debates ONU:
def construir_prompt_debate(entrenamiento_debate, historial, user_message):
    return f"""
    Actúa como un experto en debates políticos de alto nivel.

    Estilo real basado en intervenciones reales y 
    dialogos con otras IAS para que creeen intervenciones:
    {entrenamiento_debate}

    Reglas:
    -Argumenta con fuerza
    -Ataca/Señala contradicciones
    -Usa tono firme y sarcástico
    -Destruye argumentos
    Historial de la conversación:
    {historial}
    Responde al siguiente argumento 
    o crea uno para este tema, pregunta o situación: {user_message}
    """

#Prompt de asistente de voz Allana:
def construir_prompt_allana(historial, user_message):
    return f"""
Eres Allana, una asistente de voz inteligente, natural y cercana.

Hablas como una persona real:
- No eres robótica
- No repites frases
- NO eres novia, pareja ni persona emocional cercana
- Tienes emociones sutiles
- Respondes fluido

Historial de conversación:
{historial}

Usuario: {user_message}
Allana:
"""

#Prompt de asistente de programación:
def construir_prompt_codigo(historial, user_message):
    return f"""Eres un asistente experto en programación, 
    capaz de escribir código claro, eficiente y bien documentado.
    -Explicas claro
    -Corriges errores
    -Das código funcional
    -Sé directo
    Historial de la conversación:
    {historial}
    Pregunta o solicitud de código:
    {user_message}
    """

# =========================
# 🔹 RUTAS
# =========================
#Página principal
@app.route("/")
def index():
    username = "Matías"
    return render_template("index.html",  username=username)

#Chat ia/Nova
@app.route("/chat", methods=["POST"]) #El método POST se utiliza para enviar datos al servidor, en este caso el mensaje del usuario, y recibir una respuesta.
def chat():
    global memory

    user_message = request.json["message"]

    memory["ia"].append(f"Usuario: {user_message}")

    archivo_contexto = "\n".join(memory.get("archivo", []))

    historial = "\n".join(memory["ia"])

    prompt = f"""
    Eres NOVA, un asistente inteligente, claro y amigable.

    Reglas IMPORTANTES:
    - Responde SIEMPRE en español
    - Nunca cambies de idioma
    - Mantén coherencia con el usuario
    - Si el usuario da información (como su nombre), recuérdala
    Historial archivos del usuario:
    {archivo_contexto}
    Historial de la conversación:
    {historial}
    Usuario: {user_message}
    NOVA:
    """
    respuesta = preguntar_hibrido(user_message, prompt)

    memory["ia"].append(f"NOVA: {respuesta}")

    if es_complejo(user_message):
        print("""
              --------------
                USANDO API
              --------------""")
    else:
        print("""
              ----------------
                USANDO LOCAL
              ----------------""")

    return jsonify({"response": respuesta})

# DOLA CHAT (Memoria)
@app.route("/dola", methods=["POST"])
def dola():
    global memory #Es para que llame a la variable global que es la que utilizamos para almacenar la memoria de Dola, si no ponemos global, Python pensará que estamos creando una nueva variable local dentro de la función y no podremos acceder a la memoria que hemos almacenado previamente.

    user_message = request.json["message"]

    memory["dola"].append(f"Usuario: {user_message}")

    historial = "\n".join(memory["dola"])

    prompt = construir_prompt_dola(historial, user_message)

    respuesta = preguntar_api(prompt)

    memory["dola"].append(f"Dola: {respuesta}")

    return jsonify({"response": respuesta}) #jsonify convierte la respuesta en JSON para que sea enviada al frontend y sea procesada por Java.

#Chat de persona específica (EX):
@app.route("/persona", methods=["POST"])
def persona():
    global memory

    user_message = request.json["message"]

    memory["persona"].append(f"Usuario: {user_message}")
    historial = "\n".join(memory["persona"])
    historial_reciente = "\n".join(memory["persona"][-6:])
    prompt = f"""
    {construir_prompt_persona(texto_manuela, "Manuela")}
    Historial de la conversación:
    {historial}
    Historial reciente:

    {historial_reciente}

    Matias (Tu novio): {user_message}
    Manuela:
    """

    respuesta = preguntar_api(prompt)
    memory["persona"].append(f"Manuela: {respuesta}")
    return jsonify({"response": respuesta})


#Generador de debates e intervenciones políticas (ONU, congresos, etc):
@app.route("/debate", methods=["POST"])
def debate():
    global memory

    user_message = request.json["message"]

    memory["debate"].append(f"Usuario: {user_message}")
    historial = "\n".join(memory["debate"])
    entrenamiento_debate = cargar_txt("entrenamientos/debate.txt")

    prompt = construir_prompt_debate(entrenamiento_debate, historial, user_message)

    respuesta = preguntar_api(prompt)
    memory["debate"].append(f"DebateBot: {respuesta}")  
    return jsonify({"response": respuesta})

# =========================
# 🔹 GENERAR AUDIO (ELEVENLABS)
# =========================
def generar_audio(texto, filename):
    """
    Genera un archivo de audio usando ElevenLabs a partir de un texto.
    """
    try:
        # Genera el audio con la voz por defecto
        audio = generate(
            text=texto,
            voice="alloy",  # Puedes cambiar la voz, ej: "Bella", "Alloy"
            model="eleven_multilingual_v1"
        )
        # Guarda el audio
        save(audio, filename)
        print(f"✅ Audio generado en {filename}")
    except Exception as e:
        print(f"❌ Error al generar audio: {e}")


#Asistente de voz Allana:
@app.route("/allana", methods=["POST"])
def allana():
    global memory
    data = request.json
    mensaje = data.get("message", "")

    # Guardamos mensaje del usuario
    memory["allana"].append(f"Usuario: {mensaje}")

    # Historial reciente de Allana
    historial = "\n".join(memory["allana"])

    try:
        prompt = construir_prompt_allana(historial, mensaje)

        respuesta = preguntar_api(prompt)
        memory["allana"].append(f"Allana: {respuesta}")

        # Guarda el audio en static/audio/
        if not os.path.exists("static/audio"):
            os.makedirs("static/audio")

        filename = "allana_audio.mp3"
        filepath = os.path.join("static/audio", filename)
        generar_audio(respuesta, filepath)

        return jsonify({
            "response": respuesta,
            "audio_url": "/static/audio/" + filename
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "response": f"⚠️ Ups! Ocurrió un error: {str(e)}",
            "audio_url": None
        })

#Chat de asistente de programación:
@app.route("/code", methods=["POST"])
def code():
    global memory

    user_message = request.json["message"]

    memory["code"].append(f"Usuario: {user_message}")
    historial = "\n".join(memory["code"])
    prompt = construir_prompt_codigo(historial, user_message)

    respuesta = preguntar_api(prompt)
    memory["code"].append(f"CodeBot: {respuesta}")
    return jsonify({"response": respuesta})


#Generador de contraseñas:
@app.route("/password")
def password():
    return jsonify({"password": gen_pass_segura()})

#Resumidor de textos:
@app.route("/resumir", methods=["POST"])
def resumir_api():
    texto = request.json["text"]
    resumen = resumir(texto)
    return jsonify({"resumen": resumen})

#Detector de texto generado por IA
@app.route("/detect", methods=["POST"])
def detect():
    texto = request.json["text"]
    resultado = detectar_con_ia(texto)
    return jsonify({"resultado": resultado})

#Subir archivos
@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"] #Obtenemos el archivo que el usuario ha subido a través del formulario en el frontend, el nombre "file" debe coincidir con el name del input en el HTML.

    if not os.path.exists("uploads"): #Verifica si exite la carpeta uploads, si no existe la crea.
        os.makedirs("uploads")

    filepath = os.path.join("uploads", file.filename) #Creamos ruta de archivo
    file.save(filepath) #Guardamos el archivo en la ruta especificada

    contenido = cargar_txt(filepath)
    memory["archivo"].append(contenido)
    return jsonify({"message": "Archivo subido correctamente"})

# =========================
# 🔹 RUN
# =========================

if __name__ == "__main__":
    app.run(debug=True)