import os
import sys
import threading
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from openai import OpenAI
from flask import Flask

# === Servidor "dummy" para mantener Render activo ===
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "⚡️ Slack Bot está corriendo."

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    flask_app.run(host="0.0.0.0", port=port)

# === Validar variables de entorno ===
required_env_vars = {
    "SLACK_BOT_TOKEN": os.environ.get("SLACK_BOT_TOKEN"),
    "SLACK_APP_TOKEN": os.environ.get("SLACK_APP_TOKEN"),
    "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY")
}

missing_vars = [name for name, value in required_env_vars.items() if not value]
if missing_vars:
    print(f"❌ Faltan variables: {', '.join(missing_vars)}")
    sys.exit(1)

# === Inicializa Slack y OpenAI ===
slack_app = App(token=required_env_vars["SLACK_BOT_TOKEN"])
client = OpenAI(api_key=required_env_vars["OPENAI_API_KEY"])

# === Eventos de Slack ===
@slack_app.event("app_mention")
def handle_mention(event, say):
    user = event["user"]
    text = event.get("text", "")
    prompt = text.split(">", 1)[-1].strip() if ">" in text else text

    if not prompt:
        say(f"<@{user}> Por favor hazme una pregunta.")
        return

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un asistente útil del equipo de soporte técnico."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        say(f"<@{user}> {response.choices[0].message.content}")
    except Exception as e:
        say(f"<@{user}> ❌ Error al procesar tu solicitud.")
        print(f"Error en handle_mention: {type(e).__name__}: {e}")

@slack_app.event("message")
def handle_dm(event, say):
    if event.get("bot_id") or event.get("subtype") or event.get("channel_type") != "im":
        return
    text = event.get("text", "")
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
        say(response.choices[0].message.content)
    except Exception as e:
        say("❌ Error al procesar tu solicitud.")
        print(f"Error en handle_dm: {type(e).__name__}: {e}")

# === Inicio del bot y servidor ===
if __name__ == "__main__":
    print("⚡️ Iniciando Slack Bot...")
    threading.Thread(target=run_flask, daemon=True).start()  # Flask corre en segundo plano
    try:
        handler = SocketModeHandler(slack_app, required_env_vars["SLACK_APP_TOKEN"])
        print("✅ Bot conectado y listo.")
        handler.start()
    except Exception as e:
        print(f"❌ Error al iniciar el bot: {type(e).__name__}: {e}")
        sys.exit(1)

