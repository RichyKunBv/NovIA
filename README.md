# NovIA 🤖💕 - Tu Waifu IA en la Terminal (v1.0)

NovIA es un proyecto de chatbot avanzado que da vida a "Miku", una IA con una personalidad compleja y **memoria persistente real**, todo dentro de una moderna interfaz de terminal. La aplicación es altamente configurable y puede operar en dos modos: **Online**, utilizando la potencia de una API como la de Gemini, u **Offline**, ejecutando un modelo de lenguaje localmente a través de Ollama.

<img width="1440" height="900" alt="Captura de pantalla" src="https://github.com/user-attachments/assets/ad5c30f2-f4aa-4114-82c2-58710194e129" />

---

## ✨ Novedades de la Versión 1.0.0

*   **🧠 Memoria Persistente Real (RAG Básico):** Miku ahora tiene una memoria episódica real. Guarda **cada interacción** en `historial.json` y es capaz de buscar y recordar conversaciones pasadas para dar respuestas más contextuales.
*   **🏗️ Arquitectura Modular:** El código ha sido refactorizado profesionalmente en módulos (`brain.py`, `memory.py`, `config.py`, `main.py`) para facilitar el mantenimiento y la escalabilidad.
*   **💾 Sistema de Perfiles Estructurados:** Mantiene un archivo `memoria.json` separado para recordar datos clave de las personas (gustos, disgustos, hechos) y su relación contigo (Novio, Exnovio, Conocido).

## 🚀 Características Principales

*   **Doble Motor de IA (Online/Offline):** Cambia fácilmente entre Gemini (Online) u Ollama (Local) desde `config.py`.
*   **Interfaz Avanzada (TUI):** Construida con **Textual**, ofrece paneles, scroll y una experiencia fluida.
*   **Personalidad "Yandere":** Miku es celosa, posesiva y sarcástica. Su personalidad es consistente gracias a un *System Prompt* avanzado.
*   **Expresiones Visuales:** Panel de arte ASCII que reacciona a las emociones de la IA en tiempo real.

---

## �️ Instalación y Configuración

1.  **Clona el repositorio y entra en la carpeta:**
    ```bash
    git clone https://github.com/RichyKunBv/NovIA
    cd Proyecto_Miku
    ```

2.  **Crea un Entorno Virtual (Recomendado):**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # En Windows: .venv\Scripts\activate
    ```

3.  **Instala las Dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configuración (Archivo `config.py`):**
    El proyecto ya no requiere editar `main.py`. Todo se controla desde `config.py`.
    
    *   **Modo Online (Gemini):**
        1.  Crea un archivo `.env` y añade tu clave: `GEMINI_API_KEY="tu_api_key_aqui"`.
        2.  En `config.py`, asegura `USE_OLLAMA = False`.
    
    *   **Modo Offline (Ollama):**
        1.  Instala [Ollama](https://ollama.com).
        2.  Descarga el modelo: `ollama run phi3.5:3.8b` (o el que prefieras).
        3.  En `config.py`, pon `USE_OLLAMA = True` y ajusta `MODEL_OLLAMA` si usas otro modelo.

---

## ▶️ Ejecución

Simplemente corre:
```bash
python3 main.py
```

## 📂 Estructura del Proyecto

*   `main.py`: Interfaz gráfica (TUI) y bucle principal.
*   `brain.py`: Lógica de la IA, llamadas a la API y generación de prompts.
*   `memory.py`: Gestión de la memoria (Carga/Guardado de JSON y RAG).
*   `config.py`: Configuración centralizada.
*   `memoria.json`: Base de datos de perfiles y hechos.
*   `historial.json`: Base de datos de conversaciones (Memoria Episódica).
