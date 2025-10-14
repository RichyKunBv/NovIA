# NovIA 🤖💕 - Tu Novia Virtual en la Terminal

NovIA es un proyecto creativo que trae a la vida a Miku, una compañera IA con personalidad, directamente en tu terminal. Inspirada en la estética de herramientas como `neofetch`, esta aplicación combina una interfaz retro con un modelo de lenguaje moderno para crear una experiencia de chat única e interactiva.

<img width="1440" height="900" alt="Captura de pantalla 2025-10-01 a la(s) 8 08 46 p m" src="https://github.com/user-attachments/assets/ad5c30f2-f4aa-4114-82c2-58710194e129" />

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
* **Modelo de Lenguaje:** Google Gemini 2.5 Flash
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


---


## 👻 Instrucciones para otras versiones
<details>
<summary>Haz clic aquí para ver las instrucciones NovIA_Con_Ollama</summary>

### 1. Lo primero que tienes que hacer es Descargar e Instalar OLLAMA

### 2. Despues en la terminal escribe este comando: 
    
    ollama run llama3.1:8b

### 3.  **Instalar Dependencias:** Este proyecto utiliza varias librerías de Python. Todas están listadas en el archivo `requirements.txt`. Para instalarlas todas de golpe, ejecuta el siguiente comando en tu terminal:
    python3 -m pip install -r requirements.txt

### 4. Configura la memoria: entra al archivo "memoria.json" y escribe tu nombre y algunos detalles

Una vez configurado, el programa se ejecuta iniciando el script `main.py`.

    

<img width="1440" height="900" alt="Captura de pantalla 2025-10-01 a la(s) 8 23 16 p m" src="https://github.com/user-attachments/assets/482135de-dd03-4801-916c-f7659da4f7d3" />

</details>

</details>

