import asyncio
from bot_logic import run_telegram_bot

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    run_telegram_bot()
