# NovIA 🤖💕 - Tu Novia Virtual en la Terminal

NovIA es un proyecto creativo que trae a la vida a Miku, una compañera IA con personalidad, directamente en tu terminal. Inspirada en la estética de herramientas como `neofetch`, esta aplicación combina una interfaz retro con un modelo de lenguaje moderno para crear una experiencia de chat única e interactiva.

<img width="1440" height="900" alt="Captura de pantalla 2025-08-24 a la(s) 11 27 52 p m" src="https://github.com/user-attachments/assets/b539e078-325a-47c7-b91a-d2438c17f3f6" />

---

## ✨ Características Principales

* **Interfaz Gráfica en Terminal (TUI):** Construida con **Textual**, la aplicación tiene un layout de dos columnas, paneles con bordes y colores, y una experiencia de usuario fluida.
* **Arte ASCII Dinámico:** Miku expresa sus emociones a través de arte ASCII que cambia dinámicamente según el tono de la conversación.
* **Personalidad Definida:** Miku no es un chatbot genérico. Su personalidad, gustos y forma de hablar están definidos por un `system prompt` detallado, lo que la hace consistente y creíble.
* **IA Inteligente:** Impulsado por la API de **Google Gemini**, el chatbot entiende el contexto y el sentimiento de la conversación para generar respuestas coherentes.
* **Chat Desplazable:** El historial de la conversación se puede navegar completamente con las flechas del teclado o el ratón, gracias a los widgets avanzados de Textual.
* **Asincrónico y sin Congelamiento:** La comunicación con la API de la IA se realiza en un hilo de trabajo separado, asegurando que la interfaz nunca se congele mientras esperas una respuesta.

---

## 🛠️ Tecnologías Utilizadas

* **Lenguaje:** Python 3.10+
* **Interfaz:** [Textual](https://github.com/Textualize/textual) y [Rich](https://github.com/Textualize/rich)
* **Conexión IA:** [LiteLLM](https://github.com/BerriAI/litellm)
* **Modelo de Lenguaje:** Google Gemini 1.5 Flash
* **Gestión de Entorno:** venv
* **Manejo de API Keys:** python-dotenv

---

## 🚀 Configuración

Para ejecutar este proyecto, necesitarás tener Python 3 instalado en tu sistema.

1.  **Entorno Virtual:** Se recomienda encarecidamente usar un entorno virtual de Python para instalar las dependencias de forma aislada y no afectar tu sistema.

2.  **Instalar Dependencias:** Este proyecto utiliza varias librerías de Python. Todas están listadas en el archivo `requirements.txt`. Para instalarlas todas de golpe, ejecuta el siguiente comando en tu terminal:
    ```bash
    python3 -m pip install -r requirements.txt
    ```

3.  **Clave de API:** Debes crear un archivo llamado `.env` en la raíz del proyecto. Dentro de este archivo, añade tu clave de la API de Google Gemini con el siguiente formato:
    ```
    GEMINI_API_KEY="AIzaSy...tu...clave...secreta...aqui"
    ```

Una vez configurado, el programa se ejecuta iniciando el script `main.py`.
