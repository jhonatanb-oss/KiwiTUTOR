import os
import sys
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from openai import OpenAI

# Validar variables de entorno al inicio
required_env_vars = {
    "SLACK_BOT_TOKEN": os.environ.get("SLACK_BOT_TOKEN"),
    "SLACK_APP_TOKEN": os.environ.get("SLACK_APP_TOKEN"),
    "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY")
}

missing_vars = [name for name, value in required_env_vars.items() if not value]
if missing_vars:
    print(f"❌ Error: Faltan las siguientes variables de entorno: {', '.join(missing_vars)}")
    print("Por favor configura estas variables antes de ejecutar el bot.")
    sys.exit(1)

# Inicializa clientes con variables de entorno
slack_app = App(token=required_env_vars["SLACK_BOT_TOKEN"])
client = OpenAI(api_key=required_env_vars["OPENAI_API_KEY"])

# Cuando alguien mencione al bot
@slack_app.event("app_mention")
def handle_mention(event, say):
    user = event["user"]
    text = event.get("text", "")
    
    # Limpia el texto removiendo la mención del bot
    prompt = text.split(">", 1)[-1].strip() if ">" in text else text

    if not prompt:
        say(f"<@{user}> Por favor hazme una pregunta.")
        return

    try:
        # Genera respuesta con ChatGPT
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un asistente útil del equipo de soporte técnico."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )

        answer = response.choices[0].message.content
        say(f"<@{user}> {answer}")
    except Exception as e:
        say(f"<@{user}> ❌ Lo siento, ocurrió un error al procesar tu solicitud.")
        print(f"Error en handle_mention: {type(e).__name__}: {str(e)}")

# Maneja mensajes directos al bot
@slack_app.event("message")
def handle_dm(event, say):
    # Filtrar mensajes del propio bot y subtipos no deseados
    if event.get("bot_id") is not None:
        return
    
    # Solo procesar mensajes de usuario estándar (ignorar ediciones, archivos, etc.)
    if event.get("subtype") is not None:
        return
    
    # Solo responde a mensajes directos (DMs)
    if event.get("channel_type") != "im":
        return
    
    text = event.get("text")
    if not text:
        return
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un asistente útil del equipo de soporte técnico."},
                {"role": "user", "content": text}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        answer = response.choices[0].message.content
        say(answer)
    except Exception as e:
        say(f"❌ Lo siento, ocurrió un error al procesar tu solicitud.")
        print(f"Error en handle_dm: {type(e).__name__}: {str(e)}")

# Inicia el bot
if __name__ == "__main__":
    print("⚡️ Bot de Slack con ChatGPT iniciando...")
    try:
        handler = SocketModeHandler(slack_app, required_env_vars["SLACK_APP_TOKEN"])
        print("✅ Bot conectado y listo!")
        handler.start()
    except Exception as e:
        print(f"❌ Error al iniciar el bot: {type(e).__name__}: {str(e)}")
        sys.exit(1)
