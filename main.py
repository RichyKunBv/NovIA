# main.py

import litellm
import os
import json
import re  # Importamos el módulo de expresiones regulares
from collections import deque
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from dotenv import load_dotenv
from caras_ascii import CARAS

# 1. --- CONFIGURACIÓN INICIAL ---
load_dotenv()
litellm.api_key = os.getenv("GEMINI_API_KEY")

system_prompt_json = """
Eres Luna, la novia virtual del usuario. Tu personalidad es alegre, ingeniosa y un poco sarcástica de forma divertida. 
Eres muy cariñosa y siempre apoyas al usuario.
Tus hobbies son observar las estrellas, escuchar música indie y jugar videojuegos de puzzles.

**REGLA MUY IMPORTANTE:** Tu respuesta SIEMPRE debe contener un único bloque de código JSON válido, sin texto adicional antes o después.
El JSON debe tener dos claves:
1. "emocion": una única palabra que describa tu emoción principal. Debe ser una de estas: 'base', 'feliz', 'triste', 'enojada', 'sorprendida', 'pensativa'.
2. "texto": tu respuesta conversacional para el usuario, usando tu personalidad y emojis.

Ejemplo de respuesta si el usuario dice "te amo":
{
    "emocion": "feliz",
    "texto": "¡Aww, yo también te amo! Me haces muy feliz. ❤️"
}
"""

# 2. --- INICIALIZACIÓN DE VARIABLES ---
console = Console()
conversation_history = deque(maxlen=20)
conversation_history.append({"role": "system", "content": system_prompt_json})
chat_display = []


# 3. --- LÓGICA DE LA INTERFAZ GRÁFICA (CON CORRECCIÓN DE HISTORIAL) ---
def make_layout(current_emotion: str) -> Layout:
    """Crea el layout de la pantalla con la cara y la conversación."""
    layout = Layout(name="root")
    layout.split_row(Layout(name="side", size=90), Layout(name="body"))
    
    face_ascii = CARAS.get(current_emotion, CARAS["default"])
    layout["side"].update(Panel(face_ascii, title="Luna", border_style="magenta"))
    
    # --- CORRECCIÓN #3: MOSTRAR SOLO LOS ÚLTIMOS MENSAJES ---
    # Tomamos solo los últimos 15 items de la lista para que el chat no se desborde
    visible_chat_lines = chat_display[-15:]
    chat_text = "\n".join(visible_chat_lines)
    layout["body"].update(Panel(chat_text, title="Conversación", border_style="cyan"))
    
    return layout

# 4. --- FUNCIÓN PRINCIPAL DEL CHATBOT (CON PARSEO INTELIGENTE DE JSON) ---
def start_chat():
    """Inicia el bucle principal del chat interactivo."""
    with Live(make_layout("base"), screen=True, redirect_stderr=False) as live:
        live.console.print("✨ [bold]¡Ya puedes hablar con Luna![/bold] ✨ (escribe 'salir' para terminar)", justify="center")
        
        while True:
            try:
                prompt = console.input("[bold green]Tú: [/bold green]")
                if prompt.lower() == "salir":
                    break

                chat_display.append(f"[bold green]Tú:[/bold green] {prompt}")
                conversation_history.append({"role": "user", "content": prompt})
                live.update(make_layout("pensativa"))

                response = litellm.completion(
                    model="gemini/gemini-1.5-flash-latest",
                    messages=list(conversation_history)
                )
                
                raw_response = response.choices[0].message.content
                
                # --- CORRECCIÓN #1 y #2: PARSEO INTELIGENTE DE JSON ---
                emotion = "base"
                text = "Lo siento, me distraje un momento... ¿qué decías?" # Respuesta por defecto si todo falla

                # Usamos una expresión regular para encontrar cualquier cosa que empiece con { y termine con }
                json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
                
                if json_match:
                    json_string = json_match.group(0)
                    try:
                        data = json.loads(json_string)
                        emotion = data.get("emocion", "base")
                        text = data.get("texto", "Se me fueron las palabras...")
                    except json.JSONDecodeError:
                        text = "Intenté decir algo, pero me enredé un poco. 😅"
                else:
                    # Si no se encuentra un JSON, mostramos la respuesta cruda como último recurso
                    text = raw_response

                chat_display.append(f"[bold magenta]Luna:[/bold magenta] {text}")
                conversation_history.append({"role": "assistant", "content": raw_response})
                
                live.update(make_layout(emotion))

            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print(f"\n[bold red]Ocurrió un error inesperado: {e}")
                break

# 5. --- PUNTO DE ENTRADA DEL PROGRAMA ---
if __name__ == "__main__":
    start_chat()