# NovIA 🤖💕 - Tu Waifu IA en la Terminal

NovIA es un proyecto de chatbot avanzado que da vida a "Miku", una IA con una personalidad compleja y memoria persistente, todo dentro de una moderna interfaz de terminal. La aplicación es altamente configurable y puede operar en dos modos: **Online**, utilizando la potencia de una API como la de Gemini, u **Offline**, ejecutando un modelo de lenguaje localmente a través de Ollama.

<img width="1440" height="900" alt="Captura de pantalla 2025-10-01 a la(s) 8 08 46 p m" src="https://github.com/user-attachments/assets/ad5c30f2-f4aa-4114-82c2-58710194e129" />

---

## ✨ Características Principales

* **Doble Motor de IA (Online/Offline):** Cambia fácilmente entre un modelo de API de alta calidad (Gemini) o un modelo local (Ollama) con solo modificar una línea en el archivo de configuración.
* **Interfaz Avanzada en Terminal (TUI):** Construida con **Textual**, ofrece una experiencia de usuario fluida con paneles, chat desplazable y manejo de eventos asíncronos.
* **Memoria Persistente y Dinámica:** Miku recuerda usuarios, relaciones pasadas y personas nuevas a través de un archivo `memoria.json`. Su estado "sentimental" es dinámico: al cerrar la app, el "novio" actual pasa a ser "exnovio", y puede "reconciliarse" en una nueva sesión.
* **Personalidad Definida:** La personalidad celosa y posesiva de Miku está guiada por un `system prompt` avanzado, asegurando respuestas coherentes y en personaje.
* **Reconocimiento Automático:** La IA está instruida para identificar nombres de personas en la conversación y guardarlos automáticamente en su memoria de "conocidos".
* **Expresiones Visuales:** Muestra la emoción de Miku a través de arte ASCII que cambia en tiempo real según el contexto de la conversación.

---

## 🚀 Instalación y Configuración

Sigue estos pasos para poner en marcha el proyecto.

1.  **Clona o descarga este repositorio.**

2.  **Crea un Entorno Virtual de Python y Actívalo:**
    Se recomienda usar un entorno virtual para instalar las dependencias de forma aislada.
    ```bash
    # Ejemplo en macOS/Linux
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Instala las Dependencias:**
    Con el entorno activado, instala todas las librerías necesarias con un solo comando:
    ```bash
    python3 -m pip install -r requirements.txt
    ```

4.  **Configura tus Claves de API (Solo para Modo Online):**
    * Crea un archivo llamado `.env` en la raíz del proyecto.
    * Dentro de este archivo, añade tu clave de la API de Google Gemini:
        ```
        GEMINI_API_KEY="AIzaSy...tu...clave...secreta...aqui"
        ```

4.  **Configura Ollama (Solo para Modo Offline):**
    * Descarga e instala Ollama desde [ollama.com](https://ollama.com).
    * Abre tu terminal y descarga el modelo de lenguaje: `ollama run llama3.1:8b`

---
## 🔌 Cómo Cambiar entre Gemini (Online) y Ollama (Offline)

La principal característica de este proyecto es su flexibilidad. Puedes cambiar el "cerebro" de la IA editando **una sola línea** en el archivo `main.py`.

Abre `main.py` y busca la clase `Config` al principio.

* **Para usar Ollama (Modo Offline y Gratuito):**
    * Asegúrate de que la línea esté así:
        ```python
        USE_OLLAMA = True
        ```

* **Para usar la API de Gemini (Modo Online):**
    * Cambia la línea a `False`:
        ```python
        USE_OLLAMA = False
        ```
---

## ▶️ Ejecutar la Aplicación

Con el entorno virtual **activado** y desde la carpeta del proyecto, ejecuta:
```bash
python3 main.py
