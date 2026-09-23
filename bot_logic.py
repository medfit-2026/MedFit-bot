import os
import logging
import aiohttp
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import database as db

TOKEN = os.environ.get("TELEGRAM_TOKEN")
MANAGER_USERNAME = "@Sonyka12345"  # ← ваш ник
YANDEX_API_KEY = os.environ.get("YANDEX_API_KEY")
YANDEX_FOLDER_ID = os.environ.get("YANDEX_FOLDER_ID")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["📊 Мой профиль", "🏆 Рейтинг"],
        ["👟 Ввести шаги", "🏃 Ввести бег"],
        ["📋 Тест", "🎯 Достижения"],
        ["👥 Моя группа", "📍 Отметиться на пробежке"],
        ["🤖 Спросить ИИ", "👨‍🏫 Связаться с менеджером"],
        ["ℹ️ Помощь"],
    ],
    resize_keyboard=True,
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.create_user(user.id, user.username or "", user.full_name)
    text = (
        f"Привет, {user.first_name}! 👋\n\n"
        "Я — *MedFit Assistant*, бот для геймификации физкультуры "
        "в медицинском вузе.\n\n"
        "Что я умею:\n"
        "• Считать очки (XP) за шаги и бег\n"
        "• Вести стрик — дни без пропусков\n"
        "• Рейтинг группы\n"
        "• Фиксировать нормативы\n"
        "• Отмечать пробежки по геолокации\n"
        "• Отвечать на вопросы через ИИ\n\n"
        "Сначала укажите группу:\n"
        "`/group Леч-101`\n\n"
        "Потом вводите активность:\n"
        "`/add 8000` — шаги\n"
        "`/run 5.5` — бег (км)\n"
        "`/test Бег100м 5` — норматив\n\n"
        "Спросите ИИ: `/ai Как правильно бегать?`"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=MAIN_KEYBOARD)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 *Команды бота*\n\n"
        "*Настройка:*\n"
        "/start — регистрация\n"
        "/group Леч-101 — указать группу\n\n"
        "*Активность:*\n"
        "/add 8000 — шаги\n"
        "/run 5.5 — бег (км)\n"
        "/test Бег100м 5 — норматив\n"
        "📍 Отметиться на пробежке — кнопка\n"
        "/points — мои точки пробежек\n\n"
        "*ИИ:*\n"
        "/ai вопрос — спросить ассистента\n\n"
        "*Просмотр:*\n"
        "/stats — мой профиль\n"
        "/top — общий рейтинг\n"
        "/topgroup — рейтинг группы\n"
        "/achievements — достижения\n\n"
        "*Очки:* 1 XP = 100 шагов = 0.05 км бега.\n"
        "*Тесты:* 50 XP × оценка."
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def set_group_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /group Леч-101")
        return
    group_name = " ".join(context.args)
    user = update.effective_user
    db.create_user(user.id, user.username or "", user.full_name)
    db.set_group(user.id, group_name)
    await update.message.reply_text(f"✅ Вы в группе: *{group_name}*", parse_mode="Markdown")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    row = db.get_user(user.id)
    if not row:
        await update.message.reply_text("Сначала нажмите /start")
        return
    _, username, full_name, group_name, points, streak, last_date, total_steps, total_run, test_score = row

    if points < 100:
        level = "🩺 Студент"
    elif points < 500:
        level = "💊 Ординатор"
    elif points < 1500:
        level = "🩻 Врач"
    elif points < 5000:
        level = "🧬 Профессор ЗОЖ"
    else:
        level = "🏆 Легенда физкультуры"

    text = (
        f"📊 *Ваш профиль*\n\n"
        f"👤 {full_name}\n"
        f"👥 Группа: {group_name or '— (введите /group)'}\n"
        f"🎖 {level}\n"
        f"⭐ XP: {points}\n"
        f"🔥 Стрик: {streak} дн.\n"
        f"👟 Шагов: {total_steps:,}\n"
        f"🏃 Бег: {total_run:.1f} км\n"
        f"📋 Баллов за тесты: {test_score}\n"
        f"📅 Активность: {last_date or '—'}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = db.get_top(10)
    if not rows:
        await update.message.reply_text("Пока никто не набрал очки.")
        return
    medals = ["🥇", "🥈", "🥉"]
    lines = ["🏆 *Общий рейтинг*\n"]
    for i, (name, points, streak) in enumerate(rows):
        prefix = medals[i] if i < 3 else f"{i + 1}."
        lines.append(f"{prefix} {name} — {points} XP (🔥{streak})")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def top_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    row = db.get_user(user.id)
    if not row or not row[3]:
        await update.message.reply_text("Сначала укажите группу: /group Леч-101")
        return
    group_name = row[3]
    rows = db.get_top_by_group(group_name)
    medals = ["🥇", "🥈", "🥉"]
    lines = [f"🏆 *Рейтинг группы {group_name}*\n"]
    for i, (name, points, streak) in enumerate(rows):
        prefix = medals[i] if i < 3 else f"{i + 1}."
        lines.append(f"{prefix} {name} — {points} XP (🔥{streak})")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /add 8000")
        return
    try:
        steps = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Введите целое число.")
        return
    if steps <= 0 or steps > 100000:
        await update.message.reply_text("Число от 1 до 100 000.")
        return
    await process_steps(update, steps)


async def process_steps(update: Update, steps: int):
    user = update.effective_user
    db.create_user(user.id, user.username or "", user.full_name)
    result = db.add_steps(user.id, steps)
    if not result:
        await update.message.reply_text("Сначала /start")
        return
    earned, total_points, streak = result
    await update.message.reply_text(
        f"✅ Записано: {steps:,} шагов\n"
        f"⭐ +{earned} XP (всего: {total_points})\n"
        f"🔥 Стрик: {streak} дн.\n\n"
        f"Так держать, будущий врач! 💪"
    )
    await check_achievements(update, total_points, streak)


async def add_run_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /run 5.5 (километры)")
        return
    try:
        km = float(context.args[0].replace(",", "."))
    except ValueError:
        await update.message.reply_text("Введите число, например: /run 5.5")
        return
    if km <= 0 or km > 100:
        await update.message.reply_text("Число от 0.1 до 100 км.")
        return
    user = update.effective_user
    db.create_user(user.id, user.username or "", user.full_name)
    result = db.add_run(user.id, km)
    if not result:
        await update.message.reply_text("Сначала /start")
        return
    earned, points, total_run = result
    await update.message.reply_text(
        f"🏃 Записано: *{km} км*\n"
        f"⭐ +{earned} XP (всего: {points})\n"
        f"🏅 Всего пробежали: {total_run:.1f} км",
        parse_mode="Markdown",
    )
    await check_achievements(update, points, 0)


async def add_test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Использование: /test Бег100м 5")
        return
    test_name = context.args[0]
    try:
        score = int(context.args[1])
    except ValueError:
        await update.message.reply_text("Оценка должна быть числом 1–5.")
        return
    if score < 1 or score > 5:
        await update.message.reply_text("Оценка от 1 до 5.")
        return
    user = update.effective_user
    db.create_user(user.id, user.username or "", user.full_name)
    result = db.add_test(user.id, test_name, score)
    if not result:
        await update.message.reply_text("Сначала /start")
        return
    bonus, points = result
    await update.message.reply_text(
        f"📋 Норматив *{test_name}*: оценка *{score}*\n"
        f"⭐ +{bonus} XP (всего: {points})",
        parse_mode="Markdown",
    )


async def check_achievements(update, points, streak):
    user = update.effective_user
    existing = db.get_achievements(user.id)
    to_grant = []
    if "first_steps" not in existing:
        to_grant.append(("first_steps", "🥉 *Первые шаги*!"))
    if points >= 1000 and "1000xp" not in existing:
        to_grant.append(("1000xp", "🥈 *1000 XP* — постоянный участник!"))
    if streak >= 7 and "streak7" not in existing:
        to_grant.append(("streak7", "🥇 *Стрик 7 дней*!"))
    if points >= 10000 and "legend" not in existing:
        to_grant.append(("legend", "🏆 *Легенда физкультуры*!"))

    for code, msg in to_grant:
        db.add_achievement(user.id, code)
        await update.message.reply_text(f"🎉 Новая ачивка!\n{msg}", parse_mode="Markdown")


async def achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    codes = db.get_achievements(user.id)
    catalog = {
        "first_steps": "🥉 Первые шаги",
        "1000xp": "🥈 1000 XP",
        "streak7": "🥇 Стрик 7 дней",
        "legend": "🏆 Легенда физкультуры",
    }
    if not codes:
        await update.message.reply_text("Ачивок пока нет.")
        return
    lines = ["🎯 *Ваши достижения:*\n"]
    for code in codes:
        lines.append(catalog.get(code, code))
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def contact_manager(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"👨‍🏫 *Связаться с преподавателем:*\n\n{MANAGER_USERNAME}\n\n"
        f"Напишите ему напрямую в Telegram.",
        parse_mode="Markdown",
    )


async def request_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("📍 Отправить локацию", request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await update.message.reply_text(
        "Нажмите кнопку ниже, чтобы отметить точку пробежки.\n\n"
        "⚠️ Работает только в личном чате.",
        reply_markup=keyboard,
    )


async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    location = update.message.location

    if not location:
        await update.message.reply_text("Не удалось получить координаты.")
        return

    db.create_user(user.id, user.username or "", user.full_name)
    db.add_run_point(user.id, location.latitude, location.longitude)

    maps_url = f"https://www.google.com/maps?q={location.latitude},{location.longitude}"

    await update.message.reply_text(
        f"📍 *Точка сохранена!*\n\n"
        f"Широта: `{location.latitude:.5f}`\n"
        f"Долгота: `{location.longitude:.5f}`\n\n"
        f"[Открыть на карте]({maps_url})",
        parse_mode="Markdown",
        reply_markup=MAIN_KEYBOARD,
        disable_web_page_preview=True,
    )


async def my_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    points = db.get_run_points(user.id)
    if not points:
        await update.message.reply_text(
            "У вас пока нет сохранённых точек. Нажмите «📍 Отметиться на пробежке»."
        )
        return

    lines = ["📍 *Ваши последние точки:*\n"]
    for i, (lat, lon, d) in enumerate(points[:5]):
        lines.append(f"{i + 1}. {d} — [{lat:.4f}, {lon:.4f}](https://www.google.com/maps?q={lat},{lon})")
    await update.message.reply_text(
        "\n".join(lines), parse_mode="Markdown", disable_web_page_preview=True
    )


async def ask_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Задайте вопрос: /ai Как правильно бегать?"
        )
        return

    if not YANDEX_API_KEY or not YANDEX_FOLDER_ID:
        await update.message.reply_text(
            "⚠️ ИИ пока не настроен. Добавьте YANDEX_API_KEY и YANDEX_FOLDER_ID в Environment."
        )
        return

    user_question = " ".join(context.args)
    prompt = (
        f"Ты — спортивный ассистент в медицинском вузе. "
        f"Ответь студенту кратко (до 100 слов), дружелюбно и с медицинской точки зрения: "
        f"{user_question}"
    )

    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Authorization": f"Api-Key {YANDEX_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "modelUri": f"gpt://{YANDEX_FOLDER_ID}/yandexgpt-lite/latest",
        "completionOptions": {"stream": False, "temperature": 0.6, "maxTokens": 200},
        "messages": [
            {"role": "system", "text": "Ты помощник по физкультуре для студентов-медиков."},
            {"role": "user", "text": prompt},
        ],
    }

    await update.message.reply_text("⏳ Думаю...")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    answer = data["result"]["alternatives"][0]["message"]["text"]
                    await update.message.reply_text(f"🤖 {answer}")
                else:
                    error_text = await resp.text()
                    logger.error(f"YandexGPT error: {error_text}")
                    await update.message.reply_text(f"⚠️ Ошибка ИИ: {resp.status}")
    except Exception as e:
        logger.error(f"AI error: {e}")
        await update.message.reply_text(f"❌ Ошибка соединения: {e}")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "📊 Мой профиль":
        await stats(update, context)
    elif text == "🏆 Рейтинг":
        await top(update, context)
    elif text == "👥 Моя группа":
        await top_group(update, context)
    elif text == "🎯 Достижения":
        await achievements(update, context)
    elif text == "👨‍🏫 Связаться с менеджером":
        await contact_manager(update, context)
    elif text == "ℹ️ Помощь":
        await help_command(update, context)
    elif text == "👟 Ввести шаги":
        await update.message.reply_text("Введите число шагов за сегодня, например: 8000")
    elif text == "🏃 Ввести бег":
        await update.message.reply_text("Введите километры: /run 5.5")
    elif text == "📋 Тест":
        await update.message.reply_text("Формат: /test Бег100м 5 (оценка 1–5)")
    elif text == "📍 Отметиться на пробежке":
        await request_location(update, context)
    elif text == "🤖 Спросить ИИ":
        await update.message.reply_text("Формат: /ai Ваш вопрос")
    else:
        try:
            steps = int(text.replace(" ", ""))
            if 0 < steps <= 100000:
                await process_steps(update, steps)
            else:
                await update.message.reply_text("Введите число от 1 до 100 000.")
        except ValueError:
            await update.message.reply_text("Не понял. Используйте кнопки или /help")


def run_telegram_bot():
    db.init_db()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("group", set_group_command))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CommandHandler("topgroup", top_group))
    app.add_handler(CommandHandler("add", add_command))
    app.add_handler(CommandHandler("run", add_run_command))
    app.add_handler(CommandHandler("test", add_test_command))
    app.add_handler(CommandHandler("achievements", achievements))
    app.add_handler(CommandHandler("manager", contact_manager))
    app.add_handler(CommandHandler("points", my_points))
    app.add_handler(CommandHandler("ai", ask_ai))
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    logger.info("Bot started (polling)...")
    app.run_polling()
