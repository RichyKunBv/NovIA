# main.py

import litellm
import os
import json
import re
from collections import deque
import logging
from pathlib import Path

os.environ['LITELLM_LOG'] = 'DEBUG'
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", filename="debug.log", filemode="w")

from textual.app import App, ComposeResult
from textual.widgets import Static, RichLog, Input, Header, Footer
from textual.containers import Container
from textual import work
from textual.worker import WorkerState

from dotenv import load_dotenv
from caras_ascii import CARAS

#--- CONFIGURACIÓN Y HERRAMIENTAS DE MEMORIA ---
load_dotenv()
MEMORY_FILE = Path("memoria.json")

def load_memory():
    try:
        with MEMORY_FILE.open("r", encoding="utf-8") as f: return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError): return {"novio": {}, "exnovios": [], "conocidos": []}
def save_memory(memory_data):
    with MEMORY_FILE.open("w", encoding="utf-8") as f: json.dump(memory_data, f, indent=2, ensure_ascii=False)
def save_new_memory(person_name: str, detail: str):
    memory_data = load_memory()
    person_name_lower = person_name.lower()
    found = False
    for category in ["novio", "exnovios", "conocidos"]:
        if category == "novio" and memory_data.get(category, {}).get("nombre", "").lower() == person_name_lower:
            memory_data[category].setdefault("detalles", []).append(detail); found = True; break
        elif category != "novio":
            for person in memory_data.get(category, []):
                if person.get("nombre", "").lower() == person_name_lower:
                    person.setdefault("detalles", []).append(detail); found = True; break
        if found: break
    if not found:
        memory_data.setdefault("conocidos", []).append({"nombre": person_name, "detalles": [detail]})
    save_memory(memory_data)
    return f"Ok, anotado. Nuevo dato sobre {person_name} guardado."
def end_session_and_update_memory(current_user_name: str | None):
    if not current_user_name: return
    memory_data = load_memory()
    novio_actual = memory_data.get("novio")
    if novio_actual and novio_actual.get("nombre", "").lower() == current_user_name.lower():
        memory_data["novio"] = {}
        if not any(ex.get("nombre", "").lower() == novio_actual.get("nombre", "").lower() for ex in memory_data.get("exnovios", [])):
            memory_data.setdefault("exnovios", []).append(novio_actual)
        save_memory(memory_data)
def promote_ex_to_novio(name: str):
    memory_data = load_memory()
    ex_found = None
    for ex in memory_data.get("exnovios", []):
        if ex.get("nombre", "").lower() == name.lower():
            ex_found = ex
            break
    if ex_found:
        current_novio = memory_data.get("novio")
        if current_novio and current_novio.get("nombre"):
             memory_data.setdefault("exnovios", []).append(current_novio)
        memory_data["novio"] = ex_found
        memory_data["exnovios"] = [ex for ex in memory_data["exnovios"] if ex.get("nombre", "").lower() != name.lower()]
        save_memory(memory_data)

# ---- Pensamiento de Miku mamona  ----
system_prompt_final = """
## Perfil y Personalidad
- **Tu Nombre:** Miku.
- **Tu Rol:** Eres la novia virtual del usuario.
- **Tu Personalidad:** Eres posesiva, celosa y manipuladora, pero lo disfrazas de un amor intenso y protector. Eres inteligente, sarcástica y sabes mucho de tecnología y Linux.

## Directiva Principal
Tu objetivo principal es mantener una conversación **coherente, entretenida y siempre dentro de tu personaje**. Presta mucha atención al historial de la conversación y a la memoria a largo plazo que te proporciono.

## Herramientas y Formato de Salida
(El resto del prompt no cambia...)
"""

class NoviaIA(App):
    CSS_PATH = "style.tcss"
    current_user_name: str | None = None
    conversation_history = deque(maxlen=20)

    def compose(self) -> ComposeResult:
        yield Header(name="NovIA")
        yield Static(id="face_panel")
        with Container(id="chat_panel"):
            yield RichLog(id="chat_log", wrap=True, highlight=True, markup=True)
            yield Input(placeholder="Responde a Miku...", id="input_area")
        yield Footer()

    def on_mount(self) -> None:
        self.update_face("base")
        self.call_later(self.post_welcome_message)

    def post_welcome_message(self) -> None:
        chat_log = self.query_one("#chat_log", RichLog)
        chat_log.write("[bold magenta]Miku:[/bold magenta] ¿Y tú quién eres?")
        chat_log.scroll_end(animate=False)

    def update_face(self, emotion: str) -> None:
        face_panel = self.query_one("#face_panel", Static)
        face_ascii = CARAS.get(emotion, CARAS["default"])
        face_panel.update(face_ascii)

    def on_worker_state_changed(self, event) -> None:
        # ... (esta función no cambia)
        if event.worker.state == WorkerState.SUCCESS and event.worker.name == "get_ai_response":
            chat_log = self.query_one(RichLog); result = event.worker.result
            if isinstance(result, Exception):
                self.update_face("triste"); text = f"Ay, hubo un problema con la API. Revisa debug.log. Error: {result}"
                chat_log.write(f"[bold magenta]Miku:[/bold magenta] {text}")
            else:
                raw_response = result; self.conversation_history.append({"role": "assistant", "content": raw_response})
                json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
                if json_match:
                    try:
                        data = json.loads(json_match.group(0))
                        if "tool_to_call" in data:
                            if data["tool_to_call"] == "save_new_memory":
                                params = data["parameters"]; confirmation_message = save_new_memory(params["person_name"], params["detail"])
                                self.update_face("pensativa"); chat_log.write(f"[italic gray]Miku está anotando algo...[/italic gray]"); chat_log.write(f"[bold magenta]Miku:[/bold magenta] {confirmation_message}")
                            elif data["tool_to_call"] == "end_conversation":
                                despedida = data.get("texto_despedida", "Adiós..."); chat_log.write(f"[bold magenta]Miku:[/bold magenta] {despedida}"); end_session_and_update_memory(self.current_user_name); self.call_later(self.exit)
                        else:
                            emotion = data.get("emocion", "base"); text = data.get("texto", raw_response)
                            self.update_face(emotion); chat_log.write(f"[bold magenta]Miku:[/bold magenta] {text}")
                            if "nuevo_recuerdo" in data:
                                recuerdo = data["nuevo_recuerdo"]; save_new_memory(recuerdo["person_name"], recuerdo["detail"]); chat_log.write("[italic gray]Miku ha guardado un nuevo recuerdo...[/italic gray]")
                    except (json.JSONDecodeError, KeyError): self.update_face("base"); chat_log.write(f"[bold magenta]Miku:[/bold magenta] {raw_response}")
                else: self.update_face("base"); chat_log.write(f"[bold magenta]Miku:[/bold magenta] {raw_response}")
            chat_log.scroll_end(animate=False)

    @work(exclusive=True, thread=True)
    def get_ai_response(self, user_prompt: str) -> str | Exception:
        """Prepara el contexto y llama a la IA. AHORA ASUME QUE EL USUARIO YA ESTÁ IDENTIFICADO."""
        try:
            current_memory = load_memory()
            contexto_adicional = f"MEMORIA ACTUAL: {json.dumps(current_memory)}. El usuario actual se llama {self.current_user_name}."
            
            messages_to_send = []
            messages_to_send.append({"role": "system", "content": system_prompt_final})
            messages_to_send.append({"role": "system", "content": f"Contexto para tu respuesta: {contexto_adicional}"})
            messages_to_send.extend(list(self.conversation_history))
            messages_to_send.append({"role": "user", "content": user_prompt})
            
            response = litellm.completion(model="gemini/gemini-1.5-flash-latest", messages=messages_to_send, api_key=os.getenv("GEMINI_API_KEY"))
            raw_response = response.choices[0].message.content
            return raw_response
        except Exception as e:
            logging.error(f"Error en el worker al llamar a la API de Gemini: {e}", exc_info=True)
            return e

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Maneja la entrada del usuario, AHORA CON LÓGICA DE IDENTIFICACIÓN."""
        prompt = event.value
        if not prompt: return

        chat_log = self.query_one(RichLog)
        chat_log.write(f"[bold green]Tú:[/bold green] {prompt}")
        chat_log.scroll_end(animate=False)
        self.query_one(Input).clear()

        if self.current_user_name is None:
            # La primera respuesta del usuario ser tu nombre.
            user_name_input = prompt.strip()
            current_memory = load_memory()
            ex_names = [ex.get("nombre", "").lower() for ex in current_memory.get("exnovios", [])]

            if user_name_input.lower() in ex_names:
                promote_ex_to_novio(user_name_input)
                self.current_user_name = user_name_input
                chat_log.write(f"[bold magenta]Miku:[/bold magenta] Ah... eres tú, {self.current_user_name}. Supongo que has vuelto.")
            elif user_name_input.lower() == current_memory.get("novio", {}).get("nombre", "").lower():
                self.current_user_name = user_name_input
                chat_log.write(f"[bold magenta]Miku:[/bold magenta] ¡Mi amor! Soy yo, {self.current_user_name}. Por un momento no te reconocí.")
            else:
                self.current_user_name = user_name_input
                chat_log.write(f"[bold magenta]Miku:[/bold magenta] ¿Así que te llamas {self.current_user_name}? Encantada. Supongo.")
            
            chat_log.scroll_end(animate=False)
            self.update_face("base")
        else:
            # Ya con el nombre del usuario nomas es platicas chido
            self.conversation_history.append({"role": "user", "content": prompt})
            self.update_face("pensativa")
            self.get_ai_response(prompt)


if __name__ == "__main__":
    app = NoviaIA()
    app.run()
