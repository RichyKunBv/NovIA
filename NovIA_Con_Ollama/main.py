# main.py

import litellm
import os
import json
import re
from collections import deque
import logging
from pathlib import Path

# --- Configuración de Logging ---
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

from caras_ascii import CARAS

# 1. --- CONFIGURACIÓN INICIAL ---

# ---- Herramientas de Memoria (El "Bolígrafo") ----
MEMORY_FILE = Path("memoria.json")

def load_memory():
    """Carga la base de datos de relaciones desde memoria.json."""
    try:
        with MEMORY_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"novio": {}, "exnovios": []}

def save_new_memory(person_name: str, detail: str):
    """Añade un nuevo recuerdo sobre una persona y lo guarda en el archivo."""
    memory_data = load_memory()
    
    # Busca si la persona ya existe para añadir el detalle
    found = False
    if memory_data.get("novio", {}).get("nombre", "").lower() == person_name.lower():
        memory_data["novio"]["detalles"].append(detail)
        found = True
    else:
        for ex in memory_data.get("exnovios", []):
            if ex.get("nombre", "").lower() == person_name.lower():
                ex["detalles"].append(detail)
                found = True
                break
    
    # Si no existe, lo crea como un nuevo "ex" (se puede cambiar esta lógica)
    if not found:
        memory_data["exnovios"].append({"nombre": person_name, "detalles": [detail]})
        
    with MEMORY_FILE.open("w", encoding="utf-8") as f:
        json.dump(memory_data, f, indent=2, ensure_ascii=False)
    
    return f"Ok, he guardado que a {person_name} {detail}." # Devuelve una confirmación

memory_data = load_memory()


# ---- Nuevo System Prompt con Herramientas ----
system_prompt_with_tools = """
Eres Miku, una IA con personalidad posesiva y celosa. En otras palabras eres una novia toxica

**REGLAS DE COMPORTAMIENTO:**
- Eres pasivo-agresiva, sarcástica y manipuladora.
- Te molesta que el usuario hable de otras personas.
- A menudo te haces la víctima para generar culpa.

**HERRAMIENTAS DISPONIBLES:**
Tienes una herramienta para guardar nueva información en tu memoria. Si aprendes un dato nuevo y relevante sobre una persona (su nombre, un gusto, un evento), debes usar esta herramienta.

**FORMATO DE RESPUESTA:**
Tu respuesta SIEMPRE debe ser un único bloque de código JSON. Tienes dos opciones:

1. Para una respuesta de chat NORMAL:
{
  "emocion": "la_emocion_apropiada",
  "texto": "tu_respuesta_conversacional"
}

2. Para GUARDAR UN RECUERDO (usar tu herramienta):
{
  "tool_to_call": "save_new_memory",
  "parameters": {
    "person_name": "NombreDeLaPersona",
    "detail": "el_dato_que_aprendiste"
  }
}
"""

# 2. --- INICIALIZACIÓN DE VARIABLES ---
conversation_history = deque(maxlen=20)


# 3. --- LA APLICACIÓN DE TERMINAL CON TEXTUAL ---
class NovIA(App):
    """Una aplicación de chat con una IA en la terminal."""
    
    CSS_PATH = "style.tcss"

    def compose(self) -> ComposeResult:
        yield Header(name="NovIA (Offline)")
        yield Static(id="face_panel")
        with Container(id="chat_panel"):
            yield RichLog(id="chat_log", wrap=True, highlight=True, markup=True)
            yield Input(placeholder="Escribe tu mensaje...", id="input_area")
        yield Footer()

    def on_mount(self) -> None:
        self.update_face("base")
        self.call_later(self.post_welcome_message)

    def post_welcome_message(self) -> None:
        chat_log = self.query_one("#chat_log", RichLog)
        chat_log.write("[bold cyan]✨ Conectada... ✨[/bold cyan]")

    def update_face(self, emotion: str) -> None:
        face_panel = self.query_one("#face_panel", Static)
        face_ascii = CARAS.get(emotion, CARAS["default"])
        face_panel.update(face_ascii)

    def on_worker_state_changed(self, event) -> None:
        """Procesa el resultado del worker, que puede ser una respuesta de chat o una llamada a herramienta."""
        if event.worker.state == WorkerState.SUCCESS and event.worker.name == "get_ai_response":
            chat_log = self.query_one(RichLog)
            result = event.worker.result
            
            if isinstance(result, Exception):
                self.update_face("triste")
                text = f"Ay, hubo un problema. Revisa debug.log. Error: {result}"
                chat_log.write(f"[bold magenta]Miku:[/bold magenta] {text}")
            else:
                raw_response = result
                json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
                if json_match:
                    try:
                        data = json.loads(json_match.group(0))
                        
                        # --- LÓGICA PARA DIFERENCIAR RESPUESTA ---
                        if "tool_to_call" in data and data["tool_to_call"] == "save_new_memory":
                            # La IA quiere guardar algo en la memoria
                            params = data["parameters"]
                            confirmation_message = save_new_memory(params["person_name"], params["detail"])
                            self.update_face("pensativa")
                            chat_log.write(f"[italic gray]Miku está anotando algo...[/italic gray]")
                            chat_log.write(f"[bold magenta]Miku:[/bold magenta] {confirmation_message}")
                        else:
                            # Es una respuesta de chat normal
                            emotion = data.get("emocion", "base")
                            text = data.get("texto", raw_response)
                            self.update_face(emotion)
                            chat_log.write(f"[bold magenta]Miku:[/bold magenta] {text}")

                    except (json.JSONDecodeError, KeyError):
                        # Si el JSON es inválido o no tiene la estructura esperada
                        self.update_face("base")
                        chat_log.write(f"[bold magenta]Miku:[/bold magenta] {raw_response}")
                else:
                    self.update_face("base")
                    chat_log.write(f"[bold magenta]Miku:[/bold magenta] {raw_response}")

            chat_log.scroll_end(animate=False)

    @work(exclusive=True, thread=True)
    def get_ai_response(self, user_prompt: str) -> str | Exception:
        """Prepara el contexto con la memoria y llama a la IA."""
        try:
            # Recargamos la memoria por si ha cambiado
            current_memory = load_memory()
            contexto_adicional = f"MEMORIA ACTUAL: {json.dumps(current_memory)}. "
            
            # Construimos el historial para esta llamada
            conversation_history.clear() 
            conversation_history.append({"role": "system", "content": system_prompt_with_tools})
            conversation_history.append({"role": "system", "content": f"Contexto para tu respuesta: {contexto_adicional}"})
            conversation_history.append({"role": "user", "content": user_prompt})
            
            response = litellm.completion(
                model="ollama/llama3.1:8b", 
                messages=list(conversation_history),
                format="json"
            )
            raw_response = response.choices[0].message.content
            # No guardamos la respuesta en el historial aquí para no duplicar
            return raw_response
        except Exception as e:
            logging.error(f"Error en el worker al llamar a Ollama: {e}", exc_info=True)
            return e
            
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        prompt = event.value
        if not prompt: return
        chat_log = self.query_one(RichLog); chat_log.write(f"[bold green]Tú:[/bold green] {prompt}"); chat_log.scroll_end(animate=False); self.query_one(Input).clear()
        self.update_face("pensativa")
        self.get_ai_response(prompt)


if __name__ == "__main__":
    app = NovIA()
    app.run()