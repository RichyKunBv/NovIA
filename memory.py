# memory.py
import json
import logging
import time
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
from config import Config

# --- CONSTANTES ---
HISTORY_FILE = Path("historial.json")

# --- FUNCIONES DE CARGA/GUARDADO ---

def load_memory() -> Dict[str, Any]:
    """Carga la memoria estructurada (perfiles) desde el archivo JSON."""
    try:
        with Config.MEMORY_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"novio": {}, "exnovios": [], "conocidos": []}

def save_memory(memory_data: Dict[str, Any]) -> None:
    """Guarda la memoria estructurada en el archivo JSON."""
    try:
        with Config.MEMORY_FILE.open("w", encoding="utf-8") as f:
            json.dump(memory_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Error guardando memoria: {e}")

def load_history() -> List[Dict[str, Any]]:
    """Carga el historial completo de conversaciones."""
    try:
        if not HISTORY_FILE.exists():
            return []
        with HISTORY_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_history(history_data: List[Dict[str, Any]]) -> None:
    """Guarda el historial completo en el archivo JSON."""
    try:
        with HISTORY_FILE.open("w", encoding="utf-8") as f:
            json.dump(history_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Error guardando historial: {e}")

# --- FUNCIONES PRINCIPALES DE MEMORIA ---

def save_interaction(user_name: str, user_text: str, ai_response: str) -> None:
    """
    Guarda una interacción individual en el historial persistente.
    Esta es la base de la 'Memoria Episódica'.
    """
    history = load_history()
    
    interaction = {
        "timestamp": time.time(),
        "fecha": time.strftime("%Y-%m-%d %H:%M:%S"),
        "usuario": user_name,
        "mensaje_usuario": user_text,
        "respuesta_ia": ai_response
    }
    
    history.append(interaction)
    save_history(history)

def retrieve_relevant_history(query: str, limit: int = 3) -> List[Dict[str, Any]]:
    """
    RAG BÁSICO: Busca interacciones pasadas relevantes basadas en palabras clave.
    Devuelve una lista de las interacciones más relevantes.
    """
    history = load_history()
    if not history:
        return []

    query_words = set(query.lower().split())
    # Filtramos palabras comunes muy cortas para evitar ruido
    query_words = {w for w in query_words if len(w) > 3}
    
    if not query_words:
        return []

    scored_interactions = []
    
    for interaction in history:
        # Combinamos texto de usuario y respuesta para la búsqueda
        content = (interaction.get("mensaje_usuario", "") + " " + interaction.get("respuesta_ia", "")).lower()
        
        # Puntuación simple: cuántas palabras clave coinciden
        score = sum(1 for word in query_words if word in content)
        
        if score > 0:
            scored_interactions.append((score, interaction))
    
    # Ordenar por puntuación (mayor primero) y tomar los últimos 'limit'
    # Preferimos coincidencias recientes si tienen el mismo score, por eso el sort es estable
    scored_interactions.sort(key=lambda x: x[0], reverse=True)
    
    return [item[1] for item in scored_interactions[:limit]]

def find_person_in_memory(name: str, memory_data: Dict[str, Any]) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """Busca una persona en la memoria y devuelve su categoría y datos."""
    name_lower = name.lower()
    
    # Buscar en novio actual
    if memory_data.get("novio", {}).get("nombre", "").lower() == name_lower:
        return "novio", memory_data["novio"]
        
    # Buscar en exnovios
    for ex in memory_data.get("exnovios", []):
        if ex.get("nombre", "").lower() == name_lower:
            return "exnovios", ex
            
    # Buscar en conocidos
    for conocido in memory_data.get("conocidos", []):
        if conocido.get("nombre", "").lower() == name_lower:
            return "conocidos", conocido
            
    return None, None

def save_new_person(person_name: str) -> bool:
    """Guarda una persona nueva en 'conocidos' si no existe."""
    memory_data = load_memory()
    categoria, _ = find_person_in_memory(person_name, memory_data)
    
    if categoria is None:
        # Estructura básica para nueva persona
        new_person = {
            "nombre": person_name,
            "detalles": [],
            "perfil": {
                "gustos": [],
                "disgustos": [],
                "hechos": []
            },
            "resumen_conversacion": ""
        }
        memory_data.setdefault("conocidos", []).append(new_person)
        save_memory(memory_data)
        return True
    return False

def update_user_profile(user_name: str, new_data: Dict[str, list]) -> None:
    """Actualiza el perfil (gustos, disgustos, hechos) de una persona."""
    if not user_name or not new_data: return
    
    memory_data = load_memory()
    categoria, person_data = find_person_in_memory(user_name, memory_data)
    
    if person_data:
        # Asegurar que existe la estructura de perfil
        if "perfil" not in person_data:
            person_data["perfil"] = {"gustos": [], "disgustos": [], "hechos": []}
            
        # Actualizar campos
        for field in ["gustos", "disgustos", "hechos"]:
            if field in new_data and new_data[field]:
                current_list = person_data["perfil"].setdefault(field, [])
                # Añadir solo si no existe ya (evitar duplicados exactos)
                for item in new_data[field]:
                    if item not in current_list:
                        current_list.append(item)
                        logging.info(f"Memoria actualizada para {user_name}: +{field} '{item}'")
        
        save_memory(memory_data)

def end_session_and_update_memory(current_user_name: Optional[str], conversation_history: List[Dict] = []) -> None:
    """
    Mueve al novio actual a la lista de exnovios al cerrar la sesión 
    y genera un resumen de la conversación.
    """
    if not current_user_name: return
    
    # Importación local para evitar ciclo circular
    from brain import generate_summary
    
    memory_data = load_memory()
    novio_actual = memory_data.get("novio")
    
    # Generar resumen si hay historial
    if conversation_history:
        summary = generate_summary(conversation_history)
        if summary:
            # Guardar resumen en el objeto del novio actual
            if novio_actual and novio_actual.get("nombre", "").lower() == current_user_name.lower():
                novio_actual["resumen_conversacion"] = summary
                logging.info(f"Resumen generado para {current_user_name}: {summary}")

    if novio_actual and novio_actual.get("nombre", "").lower() == current_user_name.lower():
        # Limpiar slot de novio
        memory_data["novio"] = {}
        
        # Verificar si ya existe en exnovios para no duplicar
        ex_nombres = {ex.get("nombre", "").lower() for ex in memory_data.get("exnovios", [])}
        
        # Si ya existe, actualizamos sus datos (incluyendo el nuevo resumen)
        found_in_ex = False
        for i, ex in enumerate(memory_data.get("exnovios", [])):
            if ex.get("nombre", "").lower() == current_user_name.lower():
                memory_data["exnovios"][i] = novio_actual # Actualizamos con los datos más recientes
                found_in_ex = True
                break
        
        if not found_in_ex:
            memory_data.setdefault("exnovios", []).append(novio_actual)
            
        save_memory(memory_data)

def promote_ex_to_novio(name: str) -> None:
    """Mueve un ex a la posición de novio actual."""
    memory_data = load_memory()
    ex_found = None
    
    # Buscar y remover de exnovios
    for i, ex in enumerate(memory_data.get("exnovios", [])):
        if ex.get("nombre", "").lower() == name.lower():
            ex_found = memory_data["exnovios"].pop(i)
            break
            
    if ex_found:
        # Si hay un novio actual, moverlo a exnovios
        current_novio = memory_data.get("novio")
        if current_novio and current_novio.get("nombre"):
            memory_data.setdefault("exnovios", []).append(current_novio)
            
        # Promover al ex encontrado
        memory_data["novio"] = ex_found
        save_memory(memory_data)
