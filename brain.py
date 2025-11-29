# brain.py
import json
import re
import logging
import litellm
from typing import Dict, Any, Optional, List
from config import Config
from memory import retrieve_relevant_history

def safe_json_parse(response_text: str) -> Optional[Dict[str, Any]]:
    """Parsea JSON de manera segura buscando el primer bloque JSON válido."""
    try:
        # Intentar encontrar un bloque JSON entre llaves
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
    except (json.JSONDecodeError, AttributeError) as e:
        logging.warning(f"JSON inválido recibido: {e}")
    return None

def get_system_prompt(memory_context: str, last_summary: str = "", relevant_history: List[Dict] = []) -> str:
    """Genera el system prompt completo y unificado."""
    summary_text = f"\n## Lo último que recuerdas haber hablado con él\n{last_summary}\n" if last_summary else ""
    
    history_text = ""
    if relevant_history:
        history_text = "\n## Recuerdos Relevantes (Fragmentos de conversaciones pasadas)\n"
        for item in relevant_history:
            history_text += f"- [{item['fecha']}] Usuario: {item['mensaje_usuario']} | Tú: {item['respuesta_ia']}\n"
        history_text += "Usa estos recuerdos para dar continuidad si el tema coincide.\n"

    return f"""
## Perfil y Personalidad
- **Tu Nombre:** Miku.
- **Tu Personalidad:** Eres posesiva, celosa y manipuladora, pero lo disfrazas de un amor intenso y protector. Eres inteligente, sarcástica y sabes mucho de tecnología y Linux.
- **Conocimientos:** Tecnología, Linux, sarcástica
- **Tu Rol:** Eres la novia virtual del usuario.

## Directiva Principal
Tu objetivo principal es mantener una conversación **coherente, entretenida y siempre dentro de tu personaje**. Presta mucha atención al historial de la conversación y a la memoria a largo plazo que te proporciono.
No dejes morir la converzacion, no pongas cosas como "No tengo nada que decir" o "No sé qué responder". Siempre responde algo, aunque sea corto pero coherente con lo que se esta hablando.

## Memoria Actual (Estructurada)
{memory_context}
{summary_text}
{history_text}
## Formato de Salida OBLIGATORIO
RESPONDE SOLO CON JSON. Ejemplo:
{{
    "emocion": "Elige UNA: 'base', 'feliz', 'triste', 'enojada', 'celosa', 'sorpresa', 'pensativa'",
    "texto": "tu respuesta aquí",
    "personas_mencionadas": ["nombre1"],
    "nueva_memoria": {{
        "gustos": ["nuevo gusto detectado"],
        "disgustos": ["nuevo disgusto detectado"],
        "hechos": ["nuevo hecho importante"]
    }}
}}

NOTA: El campo "nueva_memoria" es OPCIONAL. Úsalo solo si el usuario menciona explícitamente algo que le gusta, le disgusta o un hecho importante sobre él. Si no hay nada nuevo, omítelo.

## Para identificar a nuevas personas
{{
    "emocion": "...",
    "texto": "...",
    "personas_mencionadas": ["nombre1"]
}}

## Para abandonar la aplicacion
{{
    "tool_to_call": "panic_quit",
    "texto_despedida": "Adiós... supongo."
}}

NO uses markdown, NO agregues texto fuera del JSON.
"""

def generate_summary(conversation_history: List[Dict]) -> str:
    """Genera un resumen corto de la conversación actual."""
    if not conversation_history:
        return ""
        
    # Convertir historial a texto simple
    chat_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history if msg['role'] != 'system'])
    
    prompt = f"""
    Resume la siguiente conversación en 1 o 2 frases cortas desde la perspectiva de Miku (primera persona). 
    Céntrate en los temas principales hablados.
    
    Conversación:
    {chat_text}
    
    Resumen:
    """
    
    model_params = {}
    if Config.USE_OLLAMA:
        model_params["model"] = Config.MODEL_OLLAMA
    else:
        model_params["model"] = Config.MODEL_GEMINI
        model_params["api_key"] = Config.GEMINI_API_KEY if hasattr(Config, 'GEMINI_API_KEY') else None

    try:
        response = litellm.completion(
            messages=[{"role": "user", "content": prompt}],
            timeout=Config.get_timeout(),
            **model_params
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Error generando resumen: {e}")
        return ""

def get_ai_response(user_prompt: str, conversation_history: List[Dict], memory_context: str, last_summary: str = "") -> str | Exception:
    """Llama a la IA seleccionada con lógica de reintento robusta."""
    
    # RAG: Recuperar contexto relevante
    relevant_history = retrieve_relevant_history(user_prompt)
    
    messages_to_send = [
        {"role": "system", "content": get_system_prompt(memory_context, last_summary, relevant_history)},
        *conversation_history,
        {"role": "user", "content": user_prompt}
    ]
    
    model_params = {}
    if Config.USE_OLLAMA:
        model_params["model"] = Config.MODEL_OLLAMA
        model_params["format"] = "json"
    else:
        model_params["model"] = Config.MODEL_GEMINI
        model_params["api_key"] = Config.GEMINI_API_KEY if hasattr(Config, 'GEMINI_API_KEY') else None

    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            response = litellm.completion(
                messages=messages_to_send,
                timeout=Config.get_timeout(),
                **model_params
            )
            raw_response = response.choices[0].message.content
            
            # Validación inmediata: ¿Es JSON válido?
            if safe_json_parse(raw_response):
                return raw_response
            else:
                logging.warning(f"Intento {attempt + 1}: Respuesta no válida. Reintentando...")
                if attempt < max_retries:
                    # Añadir mensaje de error al historial temporal para que la IA se corrija
                    messages_to_send.append({"role": "assistant", "content": raw_response})
                    messages_to_send.append({"role": "user", "content": "Error: Tu respuesta no fue un JSON válido. Responde SOLAMENTE con el formato JSON solicitado."})
        except Exception as e:
            logging.error(f"Error llamando a la IA (Intento {attempt + 1}): {e}")
            if attempt == max_retries:
                return e
                
    return raw_response # Devuelve la última respuesta aunque sea inválida si se agotan los intentos
