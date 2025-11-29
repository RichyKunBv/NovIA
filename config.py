# config.py
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno al inicio
load_dotenv()

class Config:
    # --- INTERRUPTOR PRINCIPAL ---
    # True  = Usa el modelo local de Ollama (gratis, sin conexión)
        #Ollama usa la CPU y RAM de tu PC (yo estoy usando un M1 con 8GB RAM y va bien, usa minimo 8GB RAM por si acaso)
    # False = Usa la API de Gemini (requiere conexión y API Key)
        #Tienes que entrar a https://aistudio.google.com/api-keys y crear una API Key gratuita y ponerla en el .env

    USE_OLLAMA = False 
    MODEL_OLLAMA = "ollama/phi3.5:3.8b"   # Puedes cambiar a otro modelo que tengas localmente

#    Modelos alternativos Ollama con los que he probado (por si quieres probar otros):
    # Modelos descargados
#    MODEL_OLLAMA = "ollama/llama3.1:8b"
#    MODEL_OLLAMA = "ollama/deepseek-r1:7b"

    # Modelos en la nube (requieren conexión a internet)
#    MODEL_OLLAMA = "ollama/qwen3-vl:235b-cloud"
#    MODEL_OLLAMA = "ollama/gpt-oss:120b-cloud"    
    
    
    MODEL_GEMINI = "gemini/gemini-2.5-flash"
    
    # Configuración General
    CONVERSATION_HISTORY_LIMIT = 20
    MEMORY_FILE = Path("memoria.json")
    REQUEST_TIMEOUT = 60
    LITELLM_LOG_LEVEL = 'DEBUG'
    
    VERSION = "v1.0.0"
    
    @classmethod
    def get_timeout(cls):
        return 60 if cls.USE_OLLAMA else 30
    
    @classmethod 
    def get_model_name(cls):
        return cls.MODEL_OLLAMA if cls.USE_OLLAMA else cls.MODEL_GEMINI

def setup_logging():
    """Configura el sistema de logging."""
    os.environ['LITELLM_LOG'] = Config.LITELLM_LOG_LEVEL
    logging.basicConfig(
        level=logging.INFO, 
        format="%(asctime)s [%(levelname)s] %(message)s", 
        filename="debug.log", 
        filemode="w"
    )

def validate_config() -> bool:
    """Valida la configuración antes de iniciar."""
    if not Config.USE_OLLAMA and not os.getenv("GEMINI_API_KEY"):
        logging.error("GEMINI_API_KEY no encontrada cuando USE_OLLAMA es False")
        return False
    return True
