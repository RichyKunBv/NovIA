# NovIA 🤖💕 - Tu Novia Virtual en la Terminal

NovIA es un proyecto creativo que trae a la vida a Miku, una compañera IA con personalidad, directamente en tu terminal. Inspirada en la estética de herramientas como `neofetch`, esta aplicación combina una interfaz retro con un modelo de lenguaje moderno para crear una experiencia de chat única e interactiva.

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
