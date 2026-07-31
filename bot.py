import json
import random
import asyncio
from pathlib import Path

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)


# ===============================
# BOT TOKEN
# ===============================

TOKEN = TOKEN = os.getenv("BOT_TOKEN")


# ===============================
# PATH
# ===============================

BASE_DIR = Path(__file__).parent
LAB_DIR = BASE_DIR / "labs"


# ===============================
# LAB NAMES
# ===============================

LAB_NAMES = {
    "experiment1": "📘 Experiment 1",
    "experiment2": "📗 Experiment 2",
    "experiment3": "📙 Experiment 3",
}


# Store questions
user_questions = {}

# Store already asked questions
user_asked_questions = {}



# ===============================
# START
# ===============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = []

    files = sorted(LAB_DIR.glob("*.json"))


    if not files:
        await update.message.reply_text(
            "No lab sheets found.\nPut JSON files inside labs folder."
        )
        return


    for file in files:

        name = LAB_NAMES.get(
            file.stem,
            file.stem
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    name,
                    callback_data=f"lab|{file.name}",
                )
            ]
        )


    message = """
🤖 Welcome to Micro Lab Practice Bot!

How to use:

1️⃣ Select your Lab Sheet
2️⃣ Press Practice MCQs
3️⃣ Answer the questions
4️⃣ Read explanation
5️⃣ Next question appears automatically

Good luck! 📚
"""


    await update.message.reply_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )



# ===============================
# LAB SELECTED
# ===============================

async def lab_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()


    filename = query.data.split("|")[1]

    path = LAB_DIR / filename


    with open(path, encoding="utf-8") as f:

        questions = json.load(f)


    user_id = query.from_user.id


    user_questions[user_id] = questions

    # Reset previous session
    user_asked_questions[user_id] = []


    keyboard = [
        [
            InlineKeyboardButton(
                "📖 Practice MCQs",
                callback_data="practice",
            )
        ]
    ]


    name = LAB_NAMES.get(
        Path(filename).stem,
        filename
    )


    await query.edit_message_text(
        text=f"✅ {name} selected\n\nStart Practice?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )



# ===============================
# SEND QUESTION
# ===============================

async def send_question(query, context):

    user_id = query.from_user.id


    questions = user_questions.get(user_id)


    if not questions:

        await context.bot.send_message(
            chat_id=query.message.chat.id,
            text="Session expired.\nUse /start"
        )

        return



    asked = user_asked_questions.get(
        user_id,
        []
    )


    # Finished all questions

    if len(asked) == len(questions):

        await context.bot.send_message(
            chat_id=query.message.chat.id,
            text="🎉 You completed all questions!\n\nUse /start for a new session."
        )

        return



    # Select unused question

    available = [
        q for q in questions
        if q not in asked
    ]


    q = random.choice(available)


    asked.append(q)

    user_asked_questions[user_id] = asked


    context.user_data["question"] = q



    keyboard = []


    for i, option in enumerate(q["options"]):

        keyboard.append(
            [
                InlineKeyboardButton(
                    option,
                    callback_data=f"answer|{i}",
                )
            ]
        )


    await context.bot.send_message(
        chat_id=query.message.chat.id,
        text="❓ " + q["question"],
        reply_markup=InlineKeyboardMarkup(keyboard),
    )



# ===============================
# PRACTICE
# ===============================

async def practice(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()


    await send_question(
        query,
        context
    )



# ===============================
# ANSWER
# ===============================

async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()


    if "question" not in context.user_data:

        await context.bot.send_message(
            chat_id=query.message.chat.id,
            text="Session expired.\nUse /start"
        )

        return



    q = context.user_data["question"]


    selected = int(
        query.data.split("|")[1]
    )



    if selected == q["answer"]:

        message = "✅ Correct!\n\n"

    else:

        message = (
            "❌ Wrong!\n\n"
            f"Correct Answer:\n"
            f"{q['options'][q['answer']]}\n\n"
        )


    message += (
        "📖 Explanation:\n"
        + q["explanation"]
    )


    # Keep old messages

    await context.bot.send_message(
        chat_id=query.message.chat.id,
        text=message,
    )


    # 1 second delay

    await asyncio.sleep(1)


    await send_question(
        query,
        context
    )



# ===============================
# HOME
# ===============================

async def home(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()


    keyboard = []


    files = sorted(
        LAB_DIR.glob("*.json")
    )


    for file in files:

        name = LAB_NAMES.get(
            file.stem,
            file.stem
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    name,
                    callback_data=f"lab|{file.name}",
                )
            ]
        )


    await context.bot.send_message(
        chat_id=query.message.chat.id,
        text="📚 Select a Lab Sheet",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )



# ===============================
# MAIN
# ===============================

app = Application.builder().token(TOKEN).build()


app.add_handler(
    CommandHandler(
        "start",
        start
    )
)


app.add_handler(
    CallbackQueryHandler(
        lab_selected,
        pattern="^lab\\|",
    )
)


app.add_handler(
    CallbackQueryHandler(
        practice,
        pattern="^practice$",
    )
)


app.add_handler(
    CallbackQueryHandler(
        answer,
        pattern="^answer\\|",
    )
)


app.add_handler(
    CallbackQueryHandler(
        home,
        pattern="^home$",
    )
)



print("Bot running...")


app.run_polling()
