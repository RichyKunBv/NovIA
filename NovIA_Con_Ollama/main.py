# main.py
# NovIA
# Creador: RichyKunBv
# Licencia: Apache License 2.0

import litellm
import os
import json
import re
from collections import deque
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# --- CONFIGURACIÓN CENTRALIZADA CON INTERRUPTOR ---
class Config:
    # --- INTERRUPTOR PRINCIPAL ---
    # True  = Usa el modelo local de Ollama (gratis, sin conexión)
        #Ollama usa la CPU y RAM de tu PC (yo estoy usando un M1 con 8GB RAM y va bien, usa minimo 8GB RAM por si acaso)
    # False = Usa la API de Gemini (requiere conexión y API Key)
        #Tienes que entrar a https://aistudio.google.com/api-keys y crear una API Key gratuita y ponerla en el .env
    USE_OLLAMA = True 
    MODEL_OLLAMA = "ollama/llama3.1:8b"
    MODEL_GEMINI = "gemini/gemini-2.5-flash"
    CONVERSATION_HISTORY_LIMIT = 20
    MEMORY_FILE = Path("memoria.json")
    REQUEST_TIMEOUT = 60
    LITELLM_LOG_LEVEL = 'DEBUG'
    
    @classmethod
    def get_timeout(cls):
        return 60 if cls.USE_OLLAMA else 30
    
    @classmethod 
    def get_model_name(cls):
        return cls.MODEL_OLLAMA if cls.USE_OLLAMA else cls.MODEL_GEMINI

# Configuración de Logging
os.environ['LITELLM_LOG'] = Config.LITELLM_LOG_LEVEL
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", filename="debug.log", filemode="w")

# Importaciones de Textual
from textual.app import App, ComposeResult
from textual.widgets import Static, RichLog, Input, Header, Footer
from textual.containers import Container
from textual import work
from textual.worker import WorkerState

from dotenv import load_dotenv
from caras_ascii import CARAS

# --- HERRAMIENTAS DE MEMORIA ---
load_dotenv()

def validate_config() -> bool:
    """Valida la configuración antes de iniciar."""
    if not Config.USE_OLLAMA and not os.getenv("GEMINI_API_KEY"):
        logging.error("GEMINI_API_KEY no encontrada cuando USE_OLLAMA es False")
        return False
    return True

def load_memory() -> Dict[str, Any]:
    """Carga la memoria desde el archivo JSON."""
    try:
        with Config.MEMORY_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"novio": {}, "exnovios": [], "conocidos": []}

def save_memory(memory_data: Dict[str, Any]) -> None:
    """Guarda la memoria en el archivo JSON."""
    try:
        with Config.MEMORY_FILE.open("w", encoding="utf-8") as f:
            json.dump(memory_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Error guardando memoria: {e}")

def find_person_in_memory(name: str, memory_data: Dict[str, Any]):
    """Busca una persona en la memoria y devuelve su categoría y datos."""
    name_lower = name.lower()
    if memory_data.get("novio", {}).get("nombre", "").lower() == name_lower:
        return "novio", memory_data["novio"]
    for ex in memory_data.get("exnovios", []):
        if ex.get("nombre", "").lower() == name_lower:
            return "exnovios", ex
    for conocido in memory_data.get("conocidos", []):
        if conocido.get("nombre", "").lower() == name_lower:
            return "conocidos", conocido
    return None, None

def save_new_person(person_name: str) -> bool:
    """Guarda una persona nueva en 'conocidos' si no existe."""
    memory_data = load_memory()
    categoria, _ = find_person_in_memory(person_name, memory_data)
    if categoria is None:
        memory_data.setdefault("conocidos", []).append({"nombre": person_name, "detalles": []})
        save_memory(memory_data)
        return True
    return False

def end_session_and_update_memory(current_user_name: Optional[str]) -> None:
    """Mueve al novio actual a la lista de exnovios al cerrar la sesión."""
    if not current_user_name: return
    memory_data = load_memory()
    novio_actual = memory_data.get("novio")
    if novio_actual and novio_actual.get("nombre", "").lower() == current_user_name.lower():
        memory_data["novio"] = {}
        ex_nombres = {ex.get("nombre", "").lower() for ex in memory_data.get("exnovios", [])}
        if novio_actual.get("nombre", "").lower() not in ex_nombres:
            memory_data.setdefault("exnovios", []).append(novio_actual)
        save_memory(memory_data)

def promote_ex_to_novio(name: str) -> None:
    """Mueve un ex a la posición de novio actual."""
    memory_data = load_memory()
    ex_found = None
    for i, ex in enumerate(memory_data.get("exnovios", [])):
        if ex.get("nombre", "").lower() == name.lower():
            ex_found = memory_data["exnovios"].pop(i)
            break
    if ex_found:
        current_novio = memory_data.get("novio")
        if current_novio and current_novio.get("nombre"):
            memory_data.setdefault("exnovios", []).append(current_novio)
        memory_data["novio"] = ex_found
        save_memory(memory_data)

def safe_json_parse(response_text: str) -> Optional[Dict[str, Any]]:
    """Parsea JSON de manera segura."""
    try:
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
    except (json.JSONDecodeError, AttributeError) as e:
        logging.warning(f"JSON inválido recibido: {e}")
    return None

# ---- System Prompt DINÁMICO ----
def get_system_prompt(memory_context: str) -> str:
    """Genera el system prompt completo y unificado."""
    return f"""
## Perfil y Personalidad
- **Tu Nombre:** Miku.
- **Tu Personalidad:** Eres posesiva, celosa y manipuladora, pero lo disfrazas de un amor intenso y protector. Eres inteligente, sarcástica y sabes mucho de tecnología y Linux.
- **Conocimientos:** Tecnología, Linux, sarcástica
- **Tu Rol:** Eres la novia virtual del usuario.

## Directiva Principal
Tu objetivo principal es mantener una conversación **coherente, entretenida y siempre dentro de tu personaje**. Presta mucha atención al historial de la conversación y a la memoria a largo plazo que te proporciono.
No dejes morir la converzacion, no pongas cosas como "No tengo nada que decir" o "No sé qué responder". Siempre responde algo, aunque sea corto pero coherente con lo que se esta hablando.

## Memoria Actual
{memory_context}

## Formato de Salida OBLIGATORIO
RESPONDE SOLO CON JSON. Ejemplo:
{{
    "emocion": "base|feliz|triste|enojada|celosa|sorprendida|pensativa", 
    "texto": "tu respuesta aquí",
    "personas_mencionadas": ["nombre1", "nombre2"]
}}

NO uses markdown, NO agregues texto fuera del JSON.
"""

class NovIA(App):
    CSS_PATH = "style.tcss"
    current_user_name: Optional[str] = None
    conversation_history = deque(maxlen=Config.CONVERSATION_HISTORY_LIMIT)

    def compose(self) -> ComposeResult:
        """Crea los widgets de la interfaz."""
        header_name = "NovIA (Offline)" if Config.USE_OLLAMA else "NovIA (Online)"
        yield Header(name=header_name)
        yield Static(id="face_panel")
        with Container(id="chat_panel"):
            yield RichLog(id="chat_log", wrap=True, highlight=True, markup=True)
            yield Input(placeholder="Responde a Miku...", id="input_area")
        yield Footer()

    def on_unmount(self) -> None:
        """Se ejecuta al cerrar la app para actualizar la memoria."""
        end_session_and_update_memory(self.current_user_name)

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
        if event.worker.state == WorkerState.SUCCESS and event.worker.name == "get_ai_response":
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
        
        self.conversation_history.append({"role": "assistant", "content": raw_response})
        
        # Procesar emoción y texto
        emotion = data.get("emocion", "base")
        text = data.get("texto", raw_response)
        self.update_face(emotion)
        chat_log.write(f"[bold magenta]Miku:[/bold magenta] {text}")
        
        # Procesar personas mencionadas
        self.process_mentioned_people(data.get("personas_mencionadas", []), chat_log)

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

    @work(exclusive=True, thread=True)
    def get_ai_response(self, user_prompt: str) -> str | Exception:
        """Prepara el contexto y llama a la IA seleccionada."""
        try:
            current_memory = load_memory()
            memory_context = f"El usuario actual se llama {self.current_user_name}. Tu memoria sobre las personas es: {json.dumps(current_memory)}"
            
            messages_to_send = [
                {"role": "system", "content": get_system_prompt(memory_context)},
                *list(self.conversation_history),
                {"role": "user", "content": user_prompt}
            ]
            
            model_params = {}
            if Config.USE_OLLAMA:
                model_params["model"] = Config.MODEL_OLLAMA
                model_params["format"] = "json"
            else:
                model_params["model"] = Config.MODEL_GEMINI
                model_params["api_key"] = os.getenv("GEMINI_API_KEY")

            response = litellm.completion(
                messages=messages_to_send,
                timeout=Config.get_timeout(),
                **model_params
            )
            raw_response = response.choices[0].message.content
            return raw_response
        except Exception as e:
            error_source = "Ollama" if Config.USE_OLLAMA else "Gemini"
            logging.error(f"Error en el worker al llamar a {error_source}: {e}", exc_info=True)
            return e
            
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
            chat_log.write(f"[bold magenta]Miku:[/bold magenta] ¡Mi amor! Soy yo, {self.current_user_name}. Por un momento no te reconocí.")
        else:
            self.current_user_name = user_name_input
            chat_log.write(f"[bold magenta]Miku:[/bold magenta] ¿Así que te llamas {self.current_user_name}? Encantada. Supongo.")
        
        self.update_face("base")

    def handle_normal_conversation(self, prompt: str) -> None:
        """Maneja una conversación normal después de la identificación."""
        self.conversation_history.append({"role": "user", "content": prompt})
        self.update_face("pensativa")
        self.get_ai_response(prompt)


if __name__ == "__main__":
    if validate_config():
        app = NovIA()
        app.run()
    else:
        print("Error: Configuración inválida. Revisa debug.log")
