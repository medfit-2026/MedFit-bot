import os
import threading
from flask import Flask
from bot_logic import run_telegram_bot

app = Flask(__name__)


@app.route('/')
def home():
    return "Bot is running"


@app.route('/health')
def health():
    return "OK"


def start_bot():
    run_telegram_bot()


if __name__ == "__main__":
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
