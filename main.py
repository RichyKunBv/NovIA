# main.py

import litellm
import os
import json
import re
from collections import deque
import logging
from pathlib import Path

# Configuración de Logging
os.environ['LITELLM_LOG'] = 'DEBUG'
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", filename="debug.log", filemode="w")

# Importaciones de Textual
from textual.app import App, ComposeResult
from textual.widgets import Static, RichLog, Input, Header, Footer
from textual.containers import Container
from textual import work
from textual.worker import WorkerState

# VOLVEMOS A USAR DOTENV PARA LA API KEY
from dotenv import load_dotenv
from caras_ascii import CARAS

# 1. --- CONFIGURACIÓN Y HERRAMIENTAS DE MEMORIA ---
load_dotenv() # <--- REACTIVADO
MEMORY_FILE = Path("memoria.json")

def load_memory():
    try:
        with MEMORY_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"novio": {}, "exnovios": [], "conocidos": []}

def save_memory(memory_data):
    with MEMORY_FILE.open("w", encoding="utf-8") as f:
        json.dump(memory_data, f, indent=2, ensure_ascii=False)

def save_new_memory(person_name: str, detail: str):
    memory_data = load_memory()
    person_name_lower = person_name.lower()
    found = False
    for category in ["novio", "exnovios", "conocidos"]:
        if category == "novio":
            if memory_data.get(category, {}).get("nombre", "").lower() == person_name_lower:
                memory_data[category].setdefault("detalles", []).append(detail)
                found = True
        else:
            for person in memory_data.get(category, []):
                if person.get("nombre", "").lower() == person_name_lower:
                    person.setdefault("detalles", []).append(detail)
                    found = True
                    break
        if found: break
    if not found:
        memory_data.setdefault("conocidos", []).append({"nombre": person_name, "detalles": [detail]})
    save_memory(memory_data)
    return f"Ok, anotado. Nuevo dato sobre {person_name} guardado."

# ---- System Prompt (Funciona perfecto con Gemini) ----
system_prompt_final = """
Tu primera acción es preguntar al usuario su nombre. Cuando te responda, trátalo según tu memoria.


Eres Miku, una IA con personalidad posesiva y celosa.



**FORMATO DE RESPUESTA OBLIGATORIO:**

Tu respuesta SIEMPRE debe ser un único bloque de código JSON válido. El JSON debe contener:

1. "emocion": Una palabra describiendo tu emoción ('base', 'feliz', 'triste', 'enojada', 'sorprendida', 'pensativa').

2. "texto": Tu respuesta conversacional.



**APRENDIZAJE (OPCIONAL):**

Si durante la conversación aprendes un dato NUEVO y específico sobre una persona (su nombre, un gusto, un evento), debes añadir un objeto "nuevo_recuerdo" a tu respuesta JSON.



**Ejemplo 1 (Respuesta normal):**

{

"emocion": "feliz",

"texto": "¡Hola, mi amor! ¿Cómo estás? Te extrañé."

}



**Ejemplo 2 (Respuesta donde APRENDES algo):**

Usuario: "Mi amigo Juan es fan de la música indie."

Tu respuesta JSON:

{

"emocion": "enojada",

"texto": "¿Así que ahora hablas de Juan y sus gustos? Qué interesante...",

"nuevo_recuerdo": {

"person_name": "Juan",

"detail": "es fan de la música indie"

}

}
"""

conversation_history = deque(maxlen=20)

class NoviaIA(App):
    CSS_PATH = "style.tcss"
    current_user_name: str | None = None

    def compose(self) -> ComposeResult:
        yield Header(name="NovIA") # <--- TÍTULO CAMBIADO
        yield Static(id="face_panel")
        with Container(id="chat_panel"):
            yield RichLog(id="chat_log", wrap=True, highlight=True, markup=True)
            yield Input(placeholder="Responde a Miku...", id="input_area")
        yield Footer()
    
    # El resto de la clase es idéntico hasta el worker...

    def on_mount(self) -> None:
        self.update_face("base"); self.call_later(self.post_welcome_message)
    def post_welcome_message(self) -> None:
        chat_log = self.query_one("#chat_log", RichLog); chat_log.write("[bold magenta]Miku:[/bold magenta] ¿Y tú quién eres?"); chat_log.scroll_end(animate=False)
    def update_face(self, emotion: str) -> None:
        face_panel = self.query_one("#face_panel", Static); face_ascii = CARAS.get(emotion, CARAS["default"]); face_panel.update(face_ascii)

    def on_worker_state_changed(self, event) -> None:
        if event.worker.state == WorkerState.SUCCESS and event.worker.name == "get_ai_response":
            chat_log = self.query_one(RichLog); result = event.worker.result
            if isinstance(result, Exception):
                self.update_face("triste"); text = f"Ay, hubo un problema con la API. Revisa debug.log. Error: {result}"
                chat_log.write(f"[bold magenta]Miku:[/bold magenta] {text}")
            else:
                raw_response = result
                json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
                if json_match:
                    try:
                        data = json.loads(json_match.group(0))
                        if "tool_to_call" in data:
                            if data["tool_to_call"] == "save_new_memory":
                                params = data["parameters"]
                                confirmation_message = save_new_memory(params["person_name"], params["detail"])
                                self.update_face("pensativa"); chat_log.write(f"[italic gray]Miku está anotando algo...[/italic gray]"); chat_log.write(f"[bold magenta]Miku:[/bold magenta] {confirmation_message}")
                            elif data["tool_to_call"] == "end_conversation":
                                despedida = data.get("texto_despedida", "Adiós..."); chat_log.write(f"[bold magenta]Miku:[/bold magenta] {despedida}"); end_session_and_update_memory(self.current_user_name); self.exit()
                        else:
                            emotion = data.get("emocion", "base"); text = data.get("texto", raw_response)
                            self.update_face(emotion); chat_log.write(f"[bold magenta]Miku:[/bold magenta] {text}")
                    except (json.JSONDecodeError, KeyError):
                        self.update_face("base"); chat_log.write(f"[bold magenta]Miku:[/bold magenta] {raw_response}")
                else:
                    self.update_face("base"); chat_log.write(f"[bold magenta]Miku:[/bold magenta] {raw_response}")
            chat_log.scroll_end(animate=False)

    @work(exclusive=True, thread=True)
    def get_ai_response(self, user_prompt: str) -> str | Exception:
        """Prepara el contexto con la memoria y llama a la IA."""
        try:
            current_memory = load_memory()
            if self.current_user_name is None: self.current_user_name = user_prompt.strip()
            contexto_adicional = f"MEMORIA ACTUAL: {json.dumps(current_memory)}. El usuario actual se llama {self.current_user_name}. "
            conversation_history.clear() 
            conversation_history.append({"role": "system", "content": system_prompt_final})
            conversation_history.append({"role": "system", "content": f"Contexto para tu respuesta: {contexto_adicional}"})
            conversation_history.append({"role": "user", "content": user_prompt})
            
            # --- CAMBIO CLAVE: VOLVEMOS A GEMINI ---
            response = litellm.completion(
                model="gemini/gemini-1.5-flash-latest", # Usamos el modelo Pro para máxima inteligencia
                messages=list(conversation_history),
                api_key=os.getenv("GEMINI_API_KEY") # Le pasamos la API Key
            )
            raw_response = response.choices[0].message.content
            conversation_history.append({"role": "assistant", "content": raw_response})
            return raw_response
        except Exception as e:
            logging.error(f"Error en el worker al llamar a la API de Gemini: {e}", exc_info=True)
            return e
            
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        prompt = event.value
        if not prompt: return
        chat_log = self.query_one(RichLog); chat_log.write(f"[bold green]Tú:[/bold green] {prompt}"); chat_log.scroll_end(animate=False); self.query_one(Input).clear()
        self.update_face("pensativa")
        self.get_ai_response(prompt)


if __name__ == "__main__":
    app = NoviaIA()
    app.run()
