import os
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import database as db

TOKEN = os.environ.get("TELEGRAM_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["📊 Мой профиль", "🏆 Рейтинг"],
        ["👟 Ввести шаги", "🎯 Достижения"],
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
        "• Считать ваши очки активности (XP)\n"
        "• Вести стрик — дни подряд без пропусков\n"
        "• Показывать рейтинг группы\n"
        "• Выдавать ачивки за достижения\n\n"
        "Начните с кнопки *👟 Ввести шаги*."
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=MAIN_KEYBOARD)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 *Команды бота*\n\n"
        "/start — регистрация\n"
        "/stats — мой профиль\n"
        "/top — рейтинг группы\n"
        "/achievements — мои ачивки\n"
        "/add 8000 — добавить шаги\n\n"
        "*Очки:* 1 XP за 100 шагов, минимум 5 XP.\n"
        "*Уровни:* Студент → Ординатор → Врач → Профессор → Легенда."
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    row = db.get_user(user.id)
    if not row:
        await update.message.reply_text("Сначала нажмите /start")
        return
    _, username, full_name, points, streak, last_date, total_steps = row

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
        f"🎖 {level}\n"
        f"⭐ XP: {points}\n"
        f"🔥 Стрик: {streak} дн.\n"
        f"👟 Шагов: {total_steps:,}\n"
        f"📅 Активность: {last_date or '—'}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = db.get_top(10)
    if not rows:
        await update.message.reply_text("Пока никто не набрал очки.")
        return
    medals = ["🥇", "🥈", "🥉"]
    lines = ["🏆 *Рейтинг группы*\n"]
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


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "📊 Мой профиль":
        await stats(update, context)
    elif text == "🏆 Рейтинг":
        await top(update, context)
    elif text == "🎯 Достижения":
        await achievements(update, context)
    elif text == "ℹ️ Помощь":
        await help_command(update, context)
    elif text == "👟 Ввести шаги":
        await update.message.reply_text("Введите число шагов за сегодня, например: 8000")
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
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CommandHandler("add", add_command))
    app.add_handler(CommandHandler("achievements", achievements))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    logger.info("Bot started (polling)...")
    app.run_polling()
