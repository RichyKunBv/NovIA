# main.py
# NovIA
# Creador: RichyKunBv
# Licencia: Apache License 2.0

import logging
import json
from collections import deque
from typing import Optional, Any

# Importaciones de Textual
from textual.app import App, ComposeResult
from textual.widgets import Static, RichLog, Input, Header, Footer, Label
from textual.containers import Container
from textual import work
from textual.worker import WorkerState

# Importaciones del Proyecto (Refactorizado)
from config import Config, validate_config, setup_logging
from memory import (
    load_memory, 
    save_new_person, 
    end_session_and_update_memory, 
    promote_ex_to_novio,
    update_user_profile,
    save_interaction
)
from brain import get_ai_response, safe_json_parse
from caras_ascii import CARAS

# Configurar Logging
setup_logging()

class NovIA(App):
    CSS_PATH = "style.tcss"
    current_user_name: Optional[str] = None
    conversation_history = deque(maxlen=Config.CONVERSATION_HISTORY_LIMIT)

    # Botón de pánico
    BINDINGS = [("ctrl+q", "panic_quit", "Salir Inmediatamente")]
    
    def action_panic_quit(self) -> None:
        """Acción para cerrar la aplicación inmediatamente al presionar Ctrl+Q."""
        logging.info("Cierre forzado iniciado por el usuario (Ctrl+Q).")
        self.exit() 

    def compose(self) -> ComposeResult:
        """Crea los widgets con la estructura de contenedores correcta."""
        header_name = "NovIA (Offline)" if Config.USE_OLLAMA else "NovIA (Online)"
        
        yield Header(name=header_name)
        
        with Container(id="main-container"):
            yield Static(id="face_panel")
            with Container(id="chat_panel"):
                yield RichLog(id="chat_log", wrap=True, highlight=True, markup=True)
                yield Input(placeholder="Responde a Miku...", id="input_area")
        
        yield Label(f" v{Config.VERSION}", id="version-label")
        yield Footer()

    def on_unmount(self) -> None:
        """Se ejecuta al cerrar la app para actualizar la memoria."""
        end_session_and_update_memory(self.current_user_name, list(self.conversation_history))

    def on_mount(self) -> None:
        """Se ejecuta una vez cuando la app se inicia."""
        self.update_face("base")
        self.call_later(self.post_welcome_message)

    def post_welcome_message(self) -> None:
        """Muestra el mensaje de bienvenida inicial."""
        chat_log = self.query_one("#chat_log", RichLog)
        chat_log.write("[bold magenta]Miku:[/bold magenta] ¿Y tú quién eres?")
        chat_log.scroll_end(animate=False)

    def update_face(self, emotion: str) -> None:
        """Actualiza el panel de la cara ASCII."""
        face_panel = self.query_one("#face_panel", Static)
        face_ascii = CARAS.get(emotion, CARAS["default"])
        face_panel.update(face_ascii)

    def on_worker_state_changed(self, event) -> None:
        """Se activa cuando un worker termina y procesa el resultado."""
        if event.worker.state == WorkerState.SUCCESS and event.worker.name == "get_ai_response_worker":
            self.process_ai_response(event.worker.result)

    def process_ai_response(self, result: Any) -> None:
        """Procesa la respuesta de la IA."""
        chat_log = self.query_one(RichLog)
        
        if isinstance(result, Exception):
            self.update_face("triste")
            text = f"Ay, hubo un problema con la API. Error: {result}"
            chat_log.write(f"[bold magenta]Miku:[/bold magenta] {text}")
        else:
            self.process_successful_response(result, chat_log)
        
        chat_log.scroll_end(animate=False)

    def process_successful_response(self, raw_response: str, chat_log: RichLog) -> None:
        """Procesa una respuesta exitosa de la IA."""
        data = safe_json_parse(raw_response)
        if not data:
            self.handle_fallback_response(raw_response, chat_log)
            return
        
        # Verificar si la IA quiere salir
        if data.get("tool_to_call") == "panic_quit":
            self.action_panic_quit()
            return

        self.conversation_history.append({"role": "assistant", "content": raw_response})
        
        # Procesar emoción y texto
        emotion = data.get("emocion", "base")
        text = data.get("texto", raw_response)
        self.update_face(emotion)
        chat_log.write(f"[bold magenta]Miku:[/bold magenta] {text}")
        
        # Guardar interacción en memoria persistente (RAG)
        if self.current_user_name:
            # Necesitamos el último mensaje del usuario para guardarlo junto con la respuesta
            last_user_msg = ""
            for msg in reversed(self.conversation_history):
                if msg["role"] == "user":
                    last_user_msg = msg["content"]
                    break
            
            if last_user_msg:
                save_interaction(self.current_user_name, last_user_msg, text)
        
        # Procesar personas mencionadas
        self.process_mentioned_people(data.get("personas_mencionadas", []), chat_log)
        
        # Procesar nueva memoria estructurada
        if "nueva_memoria" in data and self.current_user_name:
            update_user_profile(self.current_user_name, data["nueva_memoria"])

    def handle_fallback_response(self, raw_response: str, chat_log: RichLog) -> None:
        """Maneja respuestas que no son JSON válido."""
        self.update_face("base")
        chat_log.write(f"[bold magenta]Miku:[/bold magenta] {raw_response}")
        logging.warning(f"Respuesta no JSON recibida: {raw_response[:100]}...")

    def process_mentioned_people(self, personas: list, chat_log: RichLog) -> None:
        """Procesa la lista de personas mencionadas."""
        for person in personas:
            if isinstance(person, str) and person.strip():
                if save_new_person(person.strip()):
                    chat_log.write(f"[italic gray]Miku ha guardado a '{person}' en su memoria...[/italic gray]")

    @work(exclusive=True, thread=True, name="get_ai_response_worker")
    def get_ai_response_worker(self, user_prompt: str) -> str | Exception:
        """Worker que llama a la función de IA en brain.py."""
        current_memory = load_memory()
        
        # Obtener el resumen de la última conversación si existe
        last_summary = ""
        if self.current_user_name:
            # Buscar en novio
            if current_memory.get("novio", {}).get("nombre", "").lower() == self.current_user_name.lower():
                last_summary = current_memory["novio"].get("resumen_conversacion", "")
            else:
                # Buscar en exnovios
                for ex in current_memory.get("exnovios", []):
                    if ex.get("nombre", "").lower() == self.current_user_name.lower():
                        last_summary = ex.get("resumen_conversacion", "")
                        break
        
        memory_context = f"El usuario actual se llama {self.current_user_name}. Tu memoria sobre las personas es: {json.dumps(current_memory, ensure_ascii=False)}"
        
        # Llamamos a la función pura del cerebro
        return get_ai_response(user_prompt, list(self.conversation_history), memory_context, last_summary)
            
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Maneja la entrada del usuario."""
        prompt = event.value.strip()
        if not prompt: return

        chat_log = self.query_one(RichLog)
        chat_log.write(f"[bold green]Tú:[/bold green] {prompt}")
        self.query_one(Input).clear()

        if self.current_user_name is None:
            self.handle_first_interaction(prompt, chat_log)
        else:
            self.handle_normal_conversation(prompt)
        
        chat_log.scroll_end(animate=False)

    def handle_first_interaction(self, user_name_input: str, chat_log: RichLog) -> None:
        """Maneja la primera interacción para establecer el nombre del usuario."""
        current_memory = load_memory()
        user_name_lower = user_name_input.lower()
        ex_names = [ex.get("nombre", "").lower() for ex in current_memory.get("exnovios", [])]
        current_novio_name = current_memory.get("novio", {}).get("nombre", "").lower()

        if user_name_lower in ex_names:
            promote_ex_to_novio(user_name_input)
            self.current_user_name = user_name_input
            chat_log.write(f"[bold magenta]Miku:[/bold magenta] Ah... eres tú, {self.current_user_name}. Supongo que has vuelto.")
        elif user_name_lower == current_novio_name:
            self.current_user_name = user_name_input
            chat_log.write(f"[bold magenta]Miku:[/bold magenta] ¡Mi amor! por fin te veo {self.current_user_name}.")
        else:
            self.current_user_name = user_name_input
            chat_log.write(f"[bold magenta]Miku:[/bold magenta] ¿Así que te llamas {self.current_user_name}? Encantada. Supongo.")
        
        self.update_face("base")

    def handle_normal_conversation(self, prompt: str) -> None:
        """Maneja una conversación normal después de la identificación."""
        self.conversation_history.append({"role": "user", "content": prompt})
        self.update_face("pensativa")
        self.get_ai_response_worker(prompt)


if __name__ == "__main__":
    if validate_config():
        app = NovIA()
        app.run()
    else:
        print("Error: Configuración inválida. Revisa debug.log")