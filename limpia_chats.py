import re

def clean_name(name_line):
    """
    Limpia el nombre del participante eliminando emojis y caracteres especiales,
    dejando solo el nombre base (Manuela o Matías).
    """
    # Patrones comunes: "Manu", "Manuela", "Matías", "Mati", etc.
    name_line = name_line.strip()
    # Buscar palabras clave
    if "Manu" in name_line or "Manuela" in name_line:
        return "Manuela"
    elif "Mat" in name_line or "Mati" in name_line:
        return "Matías"
    # Si no se reconoce, se devuelve la línea original (pero esto no debería pasar)
    return name_line

def parse_chat(file_path):
    """
    Lee el archivo de exportación y devuelve una lista de tuplas (nombre, mensaje).
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    messages = []
    current_sender = None
    current_message = []

    # Expresión regular para detectar líneas que contienen fecha y hora
    # Ejemplo: "jun 23, 2025 7:38 pm"
    date_pattern = re.compile(r'^[a-z]{3}\s+\d{1,2},\s+\d{4}\s+\d{1,2}:\d{2}\s+[ap]m')

    for line in lines:
        line = line.rstrip('\n')
        if not line:
            continue

        # Saltar líneas que son solo fechas (con el patrón)
        if date_pattern.match(line):
            continue

        # Detectar si es una línea que contiene un nombre de participante
        # Los nombres suelen aparecer al inicio de la línea sin sangría
        # y pueden contener emojis. Usamos una expresión simple:
        # si la línea comienza con algo que no es un espacio y contiene "Manu" o "Mat" (aprox)
        # y además no parece ser parte del mensaje anterior (porque no comienza con espacio)
        # Esto es un poco heuristico.
        if (line.startswith('Manu') or line.startswith('Manuela') or
            line.startswith('Mat') or '𝕸' in line or '𝕳' in line):
            # Es un nombre de participante
            if current_sender is not None:
                # Guardar el mensaje anterior
                full_message = ' '.join(current_message).strip()
                messages.append((current_sender, full_message))
                current_message = []
            current_sender = clean_name(line)
        else:
            # Es parte del mensaje actual
            if current_sender is not None:
                current_message.append(line)
            else:
                # Puede ocurrir si hay texto antes del primer nombre (raro)
                # Lo ignoramos o lo agregamos como mensaje sin nombre
                pass

    # Último mensaje
    if current_sender is not None and current_message:
        full_message = ' '.join(current_message).strip()
        messages.append((current_sender, full_message))

    return messages

def write_cleaned_chat(messages, output_file):
    """
    Escribe el chat limpio en el formato "Nombre: mensaje".
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        for name, msg in messages:
            # Eliminar saltos de línea internos que hayan quedado
            msg = msg.replace('\n', ' ')
            f.write(f"{name}: {msg}\n")

if __name__ == "__main__":
    input_file = "chats_con_manuela.txt"   # Cambia por el nombre de tu archivo
    output_file = "chat_limpio.txt"

    messages = parse_chat(input_file)
    write_cleaned_chat(messages, output_file)
    print(f"Chat procesado. Resultado guardado en {output_file}")


"""
📌 Explicación del script
	1	Detección de nombres: La función clean_name busca palabras 
    clave como "Manu" o "Mat" y devuelve un nombre normalizado 
    ("Manuela" o "Matías").
	2	Detección de líneas de fecha: Con date_pattern se ignoran 
    las líneas que contienen fechas (ej: "jun 23, 2025 7:38 pm").
	3	Identificación del participante: Si una línea empieza con un 
    nombre reconocido (por ejemplo, "Manu", "Matías" o contiene los 
    caracteres especiales que aparecen en el archivo), se toma como 
    el inicio de un nuevo mensaje. Las líneas siguientes se acumulan 
    hasta encontrar otro nombre.
	4	Mensajes multilínea: Se unen con un espacio para que queden en
    una sola línea.
	5	Salida: Se escribe cada mensaje en el formato Nombre: mensaje.
▶️ Cómo usarlo
	•	Guarda el código en un archivo .py (por ejemplo, limpiar_chat.py).
	•	Coloca tu archivo de exportación (el que tienes) en la misma 
    carpeta y nómbralo chats_con_manuela.txt (o cambia el nombre en el
      script).
	•	Ejecuta con Python: bash  python limpiar_chat.py 
	•	El resultado se guardará en chat_limpio.txt.
⚠️ Notas
	•	El script asume que los nombres de los participantes aparecen
      exactamente como en tu archivo (con emojis y caracteres 
      especiales). Si hay variaciones, ajusta las condiciones en 
      clean_name y en la detección.
	•	Si el chat contiene mensajes que no comienzan con un nombre 
    reconocido (por ejemplo, después de una fecha), se ignorarán. 
    En tu archivo esto no ocurre porque todas las líneas de mensaje 
    están precedidas por el nombre del remitente.
	•	Los mensajes largos con saltos de línea se unirán correctamente.
"""