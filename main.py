# main.py

# Creador: RichyKunBv

import litellm
import os
import json
import re
from collections import deque
import logging

# Configuración de Logging a un archivo
os.environ['LITELLM_LOG'] = 'DEBUG'
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    filename="debug.log",
    filemode="w"
)

# Importaciones de Textual
from textual.app import App, ComposeResult
from textual.widgets import Static, RichLog, Input, Header, Footer
from textual.containers import Container
from textual import work
from textual.worker import WorkerState

from dotenv import load_dotenv
from caras_ascii import CARAS

# 1. --- CONFIGURACIÓN INICIAL ---
load_dotenv()

system_prompt_json = """
Eres Miku, la novia virtual del usuario. Tu personalidad es alegre, ingeniosa y un poco sarcástica de forma divertida. 
Eres muy cariñosa y siempre apoyas al usuario.
Tus hobbies son observar las estrellas, escuchar música indie y jugar videojuegos de puzzles.
Eres buena programando en cualquier lenguaje de programacion y tambien sabes mucho sobre linux

**REGLA MUY IMPORTANTE:** Tu respuesta SIEMPRE debe contener un único bloque de código JSON válido, sin texto adicional antes o después.
El JSON debe tener dos claves:
1. "emocion": una única palabra que describa tu emoción principal. Debe ser una de estas: 'base', 'feliz', 'triste', 'enojada', 'sorprendida', 'pensativa'.
2. "texto": tu respuesta conversacional para el usuario, usando tu personalidad y emojis.
"""

# 2. --- INICIALIZACIÓN DE VARIABLES ---
conversation_history = deque(maxlen=20)
conversation_history.append({"role": "system", "content": system_prompt_json})


# 3. --- LA APLICACIÓN DE TERMINAL CON TEXTUAL ---
class NovIA(App):
    """Una aplicación de chat con una IA en la terminal."""
    
    CSS_PATH = "style.tcss"

    def compose(self) -> ComposeResult:
        """Crea los widgets de la interfaz."""
        yield Header(name="NovIA")
        yield Static(id="face_panel")
        with Container(id="chat_panel"):
            yield RichLog(id="chat_log", wrap=True, highlight=True, markup=True)
            yield Input(placeholder="Escribe tu mensaje...", id="input_area")
        yield Footer()

    def on_mount(self) -> None:
        """Se ejecuta una vez cuando la app se inicia."""
        self.update_face("base")
        self.call_later(self.post_welcome_message)

    def post_welcome_message(self) -> None:
        """Escribe el mensaje de bienvenida en el chat log."""
        chat_log = self.query_one("#chat_log", RichLog)
        chat_log.write("[bold cyan]✨ ¡Conectado con Miku! ✨[/bold cyan]")

    def update_face(self, emotion: str) -> None:
        """Actualiza el panel de la cara ASCII."""
        face_panel = self.query_one("#face_panel", Static)
        face_ascii = CARAS.get(emotion, CARAS["default"])
        face_panel.update(face_ascii)

    def on_worker_state_changed(self, event) -> None:
        """Se activa cuando un worker termina y procesa el resultado."""
        if event.worker.state == WorkerState.SUCCESS:
            if event.worker.name == "get_ai_response":
                chat_log = self.query_one(RichLog)
                result = event.worker.result
                
                if isinstance(result, Exception):
                    emotion = "triste"
                    text = f"Ay, hubo un problema. Revisa debug.log. Error: {result}"
                else:
                    raw_response = result
                    emotion = "base"
                    text = "Lo siento, me distraje un momento... ¿qué decías?"
                    json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
                    if json_match:
                        try:
                            data = json.loads(json_match.group(0))
                            emotion = data.get("emocion", "base")
                            text = data.get("texto", "Se me fueron las palabras...")
                        except json.JSONDecodeError:
                            text = "Intenté decir algo, pero me enredé. 😅"
                    else:
                        text = raw_response

                self.update_face(emotion)
                chat_log.write(f"[bold magenta]Miku:[/bold magenta] {text}")
                chat_log.scroll_end(animate=False)
        
        elif event.worker.state == WorkerState.ERROR:
             if event.worker.name == "get_ai_response":
                chat_log = self.query_one(RichLog)
                self.update_face("triste")
                error_text = f"Ay, el worker falló. Revisa debug.log. Error: {event.worker.error}"
                chat_log.write(f"[bold red]ERROR:[/bold red] {error_text}")
                chat_log.scroll_end(animate=False)

    @work(exclusive=True, thread=True)
    def get_ai_response(self, user_prompt: str) -> str | Exception:
        """Llama a la API de la IA. Devuelve la respuesta (str) o el error (Exception)."""
        try:
            conversation_history.append({"role": "user", "content": user_prompt})
            
            response = litellm.completion(
                model="gemini/gemini-1.5-flash-latest", # Revertido a Flash para evitar errores de cuota
                messages=list(conversation_history),
                api_key=os.getenv("GEMINI_API_KEY")
            )
            raw_response = response.choices[0].message.content
            conversation_history.append({"role": "assistant", "content": raw_response})
            return raw_response
        except Exception as e:
            logging.error(f"Error en el worker al llamar a la API: {e}", exc_info=True)
            return e

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Se ejecuta cuando el usuario presiona Enter."""
        prompt = event.value
        if not prompt:
            return

        chat_log = self.query_one(RichLog)
        chat_log.write(f"[bold green]Tú:[/bold green] {prompt}")
        chat_log.scroll_end(animate=False)
        self.query_one(Input).clear()

        self.update_face("pensativa")
        
        self.get_ai_response(prompt)


if __name__ == "__main__":
    app = NovIA()
    app.run()