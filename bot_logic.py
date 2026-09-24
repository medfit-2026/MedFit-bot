import os
import logging
import aiohttp
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import database as db

TOKEN = os.environ.get("TELEGRAM_TOKEN")
MANAGER_USERNAME = "@Sonyka12345"
YANDEX_API_KEY = os.environ.get("YANDEX_API_KEY")
YANDEX_FOLDER_ID = os.environ.get("YANDEX_FOLDER_ID")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ===== ГРУППЫ =====
COURSES = {
    "1": (101, 120),
    "2": (201, 220),
    "3": (301, 320),
    "4": (401, 420),
    "5": (501, 520),
    "6": (601, 620),
}

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["📊 Мой профиль", "🏆 Рейтинг"],
        ["👟 Ввести шаги", "🏃 Ввести бег"],
        ["🧠 Викторина", "🎯 Достижения"],
        ["👥 Моя группа", "📍 Отметиться на пробежке"],
        ["🤖 Спросить ИИ", "👨‍🏫 Связаться с менеджером"],
        ["ℹ️ Помощь"],
    ],
    resize_keyboard=True,
)


# ===== БАЗОВЫЕ =====
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
        "• Викторины по физкультуре\n"
        "• Фиксировать нормативы\n\n"
        "Сначала выберите группу: `/group`\n\n"
        "Потом вводите активность:\n"
        "`/add 8000` — шаги\n"
        "`/run 5.5` — бег (км)\n"
        "`/quiz` — викторина"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=MAIN_KEYBOARD)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 *Команды бота*\n\n"
        "*Настройка:*\n"
        "/start — регистрация\n"
        "/group — выбрать группу\n\n"
        "*Активность:*\n"
        "/add 8000 — шаги\n"
        "/run 5.5 — бег (км)\n"
        "/test Бег100м 5 — норматив\n"
        "📍 Отметиться на пробежке\n"
        "/points — мои точки\n\n"
        "*Викторина:*\n"
        "/quiz — пройти викторину\n"
        "/results — мои результаты\n\n"
        "*Просмотр:*\n"
        "/stats — профиль\n"
        "/top — общий рейтинг\n"
        "/topgroup — рейтинг группы\n"
        "/achievements — ачивки\n\n"
        "*Очки:* 1 XP = 100 шагов = 0.05 км бега.\n"
        "*Тесты:* 50 XP × оценка.\n"
        "*Викторина:* 20 XP за правильный ответ."
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# ===== ВЫБОР ГРУППЫ =====
async def choose_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает кнопки курсов."""
    keyboard = [
        [InlineKeyboardButton("1 курс", callback_data="course:1"),
         InlineKeyboardButton("2 курс", callback_data="course:2")],
        [InlineKeyboardButton("3 курс", callback_data="course:3"),
         InlineKeyboardButton("4 курс", callback_data="course:4")],
        [InlineKeyboardButton("5 курс", callback_data="course:5"),
         InlineKeyboardButton("6 курс", callback_data="course:6")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "📚 Выберите свой курс:",
        reply_markup=reply_markup,
    )


async def course_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает группы выбранного курса."""
    query = update.callback_query
    await query.answer()

    course = query.data.split(":")[1]
    start_num, end_num = COURSES[course]

    # Строим кнопки группами по 5 в ряд
    keyboard = []
    row = []
    for i in range(start_num, end_num + 1):
        row.append(InlineKeyboardButton(str(i), callback_data=f"setgroup:{i}"))
        if len(row) == 5:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("« Назад к курсам", callback_data="course:back")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        f"📚 *{course} курс* — выберите группу:",
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )


async def group_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет выбранную группу."""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "course:back":
        # Возврат к курсам
        keyboard = [
            [InlineKeyboardButton("1 курс", callback_data="course:1"),
             InlineKeyboardButton("2 курс", callback_data="course:2")],
            [InlineKeyboardButton("3 курс", callback_data="course:3"),
             InlineKeyboardButton("4 курс", callback_data="course:4")],
            [InlineKeyboardButton("5 курс", callback_data="course:5"),
             InlineKeyboardButton("6 курс", callback_data="course:6")],
        ]
        await query.edit_message_text(
            "📚 Выберите свой курс:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    # data = "setgroup:101"
    group_num = data.split(":")[1]
    user = update.effective_user
    db.create_user(user.id, user.username or "", user.full_name)
    db.set_group(user.id, group_num)

    await query.edit_message_text(
        f"✅ Вы в группе: *{group_num}*\n\n"
        f"Теперь рейтинг группы доступен по кнопке «👥 Моя группа».",
        parse_mode="Markdown",
    )


# ===== ПРОФИЛЬ И РЕЙТИНГ =====
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
        f"👥 Группа: {group_name or '— (нажмите /group)'}\n"
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
        await update.message.reply_text("Сначала выберите группу: /group")
        return
    group_name = row[3]
    rows = db.get_top_by_group(group_name)
    medals = ["🥇", "🥈", "🥉"]
    lines = [f"🏆 *Рейтинг группы {group_name}*\n"]
    for i, (name, points, streak) in enumerate(rows):
        prefix = medals[i] if i < 3 else f"{i + 1}."
        lines.append(f"{prefix} {name} — {points} XP (🔥{streak})")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# ===== ШАГИ И БЕГ =====
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
        f"🔥 Стрик: {streak} дн."
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


# ===== ГЕОЛОКАЦИЯ =====
async def request_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("📍 Отправить локацию", request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await update.message.reply_text(
        "Нажмите кнопку ниже, чтобы отметить точку пробежки.\n"
        "⚠️ Работает только в личке.",
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
        await update.message.reply_text("Точек пока нет.")
        return
    lines = ["📍 *Ваши последние точки:*\n"]
    for i, (lat, lon, d) in enumerate(points[:5]):
        lines.append(f"{i + 1}. {d} — [{lat:.4f}, {lon:.4f}](https://www.google.com/maps?q={lat},{lon})")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown", disable_web_page_preview=True)


# ===== ВИКТОРИНА =====
async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    questions = db.get_questions(5)
    if not questions:
        await update.message.reply_text("Вопросы пока не добавлены.")
        return
    context.user_data["quiz"] = {
        "questions": questions,
        "index": 0,
        "correct": 0,
        "total": len(questions),
    }
    await send_question(update, context)


async def send_question(update, context):
    quiz = context.user_data.get("quiz")
    if not quiz:
        return
    idx = quiz["index"]
    if idx >= quiz["total"]:
        await finish_quiz(update, context)
        return

    q_id, text, a, b, c, correct = quiz["questions"][idx]
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"A) {a}", callback_data=f"quiz:{q_id}:A")],
        [InlineKeyboardButton(f"B) {b}", callback_data=f"quiz:{q_id}:B")],
        [InlineKeyboardButton(f"C) {c}", callback_data=f"quiz:{q_id}:C")],
    ])
    msg = f"❓ *Вопрос {idx + 1}/{quiz['total']}*\n\n{text}"
    if update.callback_query:
        await update.callback_query.message.reply_text(msg, parse_mode="Markdown", reply_markup=keyboard)
    else:
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=keyboard)


async def quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    _, q_id, chosen = query.data.split(":")
    quiz = context.user_data.get("quiz")
    if not quiz:
        await query.edit_message_text("Викторина не активна. /quiz")
        return

    current = quiz["questions"][quiz["index"]]
    correct = current[5]

    if chosen == correct:
        quiz["correct"] += 1
        feedback = "✅ Правильно!"
    else:
        feedback = f"❌ Неправильно. Верный ответ: {correct}"

    quiz["index"] += 1
    await query.edit_message_text(feedback, parse_mode="Markdown")
    await send_question(update, context)


async def finish_quiz(update, context):
    quiz = context.user_data.pop("quiz")
    user = update.effective_user
    correct = quiz["correct"]
    total = quiz["total"]
    percent = int(correct / total * 100)

    db.create_user(user.id, user.username or "", user.full_name)
    db.save_quiz_result(user.id, correct, total)

    xp = correct * 20
    text = (
        f"🏁 *Викторина завершена!*\n\n"
        f"✅ Правильных: {correct}/{total} ({percent}%)\n"
        f"⭐ +{xp} XP\n\n"
    )
    if percent == 100:
        text += "🥇 Идеально!"
    elif percent >= 60:
        text += "💪 Хороший результат!"
    else:
        text += "📚 Стоит повторить материал."

    if xp > 0:
        result = db.add_steps(user.id, xp * 100)
        if result:
            _, total_points, _ = result
            text += f"\n⭐ Всего XP: {total_points}"

    await update.message.reply_text(text, parse_mode="Markdown")


async def add_question_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.username != "Sonyka12345":
        await update.message.reply_text("⛔ Только преподаватель.")
        return
    if len(context.args) < 5:
        await update.message.reply_text(
            "Формат:\n"
            "`/addq Вопрос? | A | B | C | B`",
            parse_mode="Markdown",
        )
        return
    full = " ".join(context.args)
    parts = [p.strip() for p in full.split("|")]
    if len(parts) < 5:
        await update.message.reply_text("Нужно 5 частей через `|`", parse_mode="Markdown")
        return
    question, a, b, c, correct = parts[0], parts[1], parts[2], parts[3], parts[4].upper()
    if correct not in ("A", "B", "C"):
        await update.message.reply_text("Правильный ответ — A, B или C.")
        return
    db.add_question(question, a, b, c, correct)
    await update.message.reply_text("✅ Вопрос добавлен!")


async def my_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    results = db.get_last_quiz_results(user.id)
    if not results:
        await update.message.reply_text("Вы ещё не проходили викторину. /quiz")
        return
    lines = ["📊 *Ваши последние викторины:*\n"]
    for correct, total, d in results:
        percent = int(correct / total * 100)
        lines.append(f"• {d}: {correct}/{total} ({percent}%)")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# ===== АЧИВКИ И МЕНЕДЖЕР =====
async def check_achievements(update, points, streak):
    user = update.effective_user
    existing = db.get_achievements(user.id)
    to_grant = []
    if "first_steps" not in existing:
        to_grant.append(("first_steps", "🥉 *Первые шаги*!"))
    if points >= 1000 and "1000xp" not in existing:
        to_grant.append(("1000xp", "🥈 *1000 XP*!"))
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


# ===== ИИ =====
async def ask_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Формат: /ai Как правильно бегать?")
        return
    if not YANDEX_API_KEY or not YANDEX_FOLDER_ID:
        await update.message.reply_text("⚠️ ИИ пока не настроен.")
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
            {"role": "user",
