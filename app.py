import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = 7367401537

CHOOSING, TYPING_TO_ADMIN = range(2)

# /start — показать меню
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["Отправить файл с переводом", "Написать админам"]
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Выберите действие:", reply_markup=markup
    )
    return CHOOSING

# Выбор кнопки
async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "Отправить файл с переводом":
        await update.message.reply_text(
            "Чтобы отправить свой файл, заполните мини-анкету: https://tally.so/r/3qQZg2. Это займет всего пару минут!"
        )
        return CHOOSING

    elif text == "Написать админам":
        await update.message.reply_text(
            "Здесь можно написать что угодно. Мы ответим вам в ближайшее время.\n"
            "Пожалуйста, добавьте в сообщение свой ник в формате @никнейм."
        )
        return TYPING_TO_ADMIN

    else:
        await update.message.reply_text("Пожалуйста, выберите одну из кнопок.")
        return CHOOSING

# Получение текста для админов
async def forward_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.forward_message(
        chat_id=ADMIN_CHAT_ID,
