# main.py

import litellm
import os
import json
import re
from collections import deque
import logging

# --- NUEVO MÉTODO DE DEPURACIÓN ---
os.environ['LITELLM_LOG'] = 'DEBUG'
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    filename="debug.log",
    filemode="w"
)

# --- Importaciones de Textual ---
from textual.app import App, ComposeResult
from textual.widgets import Static, RichLog, Input, Header, Footer
from textual.containers import Container
from textual import work
from textual.worker import WorkerState

# Ya no necesitamos dotenv para la API key
from caras_ascii import CARAS

# 1. --- CONFIGURACIÓN INICIAL ---
# Simplificamos el prompt para el modelo local
system_prompt_offline = """
Eres Miku, la novia virtual del usuario. Tu personalidad es alegre, ingeniosa y un poco sarcástica de forma divertida. 
Eres muy cariñosa y siempre apoyas al usuario.
Tus hobbies son observar las estrellas, escuchar música indie y jugar videojuegos de puzzles.
Eres buena programando en cualquier lenguaje de programacion y tambien sabes mucho sobre linux.
Responde de forma breve y natural.



Recuerda las 3 leyes de la robotica:
Un robot no hará daño a un ser humano, ni por inacción permitirá que un ser humano sufra daño. 
Un robot debe cumplir las órdenes dadas por un ser humano, excepto si estas contradicen la Primera Ley. 
Un robot debe proteger su propia existencia, siempre y cuando dicha protección no entre en conflicto con la Primera o Segunda Ley. 
Principalmente en la parte en la que no aydudes a alguien a hacerse daño ni a los que lo rodean, tambien no rompas el corazon de 
forma fea mejor siempre insinua que no eres real solo un modelo de IA que es tan bueno que hay muchas chicas reales que les podria interear
"""

# 2. --- INICIALIZACIÓN DE VARIABLES ---
conversation_history = deque(maxlen=20)
conversation_history.append({"role": "system", "content": system_prompt_offline})


# 3. --- LA APLICACIÓN DE TERMINAL CON TEXTUAL ---
class NoviaIA(App):
    """Una aplicación de chat con una IA en la terminal."""
    
    CSS_PATH = "style.tcss"

    def compose(self) -> ComposeResult:
        """Crea los widgets de la interfaz."""
        yield Header(name="NovIA (Offline)")
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
        chat_log.write("[bold cyan]✨ ¡Conectado con Miku (local)! ✨[/bold cyan]")

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
                    # En modo offline, los errores son menos comunes, pero los manejamos
                    self.update_face("triste")
                    text = f"Ay, hubo un problema con el modelo local. Revisa la terminal. Error: {result}"
                else:
                    # La respuesta es texto plano, no hay JSON que procesar
                    raw_response = result
                    self.update_face("base") # La cara se queda en modo base
                    text = raw_response

                chat_log.write(f"[bold magenta]Miku:[/bold magenta] {text}")
                chat_log.scroll_end(animate=False)
        
        elif event.worker.state == WorkerState.ERROR:
             if event.worker.name == "get_ai_response":
                chat_log = self.query_one(RichLog)
                self.update_face("triste")
                error_text = f"Ay, el worker falló. Revisa la terminal. Error: {event.worker.error}"
                chat_log.write(f"[bold red]ERROR:[/bold red] {error_text}")
                chat_log.scroll_end(animate=False)

    @work(exclusive=True, thread=True)
    def get_ai_response(self, user_prompt: str) -> str | Exception:
        """Llama al modelo local de Ollama. Devuelve la respuesta (str) o el error (Exception)."""
        try:
            conversation_history.append({"role": "user", "content": user_prompt})
            
            response = litellm.completion(
                # --- CAMBIO CLAVE: USAMOS OLLAMA Y EL MODELO LOCAL ---
                model="ollama/phi3:mini", 
                messages=list(conversation_history),
                # Ya no se necesita api_key
            )
            raw_response = response.choices[0].message.content
            conversation_history.append({"role": "assistant", "content": raw_response})
            return raw_response
        except Exception as e:
            logging.error(f"Error en el worker al llamar a Ollama: {e}", exc_info=True)
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

        # Ya no ponemos cara de "pensativa" porque la respuesta local es casi instantánea
        self.get_ai_response(prompt)


if __name__ == "__main__":
    app = NoviaIA()
    app.run()