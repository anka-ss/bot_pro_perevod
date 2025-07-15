import os
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes,
    ConversationHandler, filters
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = 7367401537

# Здесь укажи полный публичный адрес Render-сервиса (когда деплоишь - его дают)
YOUR_WEBHOOK_URL = os.getenv("WEBHOOK_URL")

CHOOSING, TYPING_TO_ADMIN = range(2)

app_flask = Flask(__name__)

# Создаём Telegram Application
application = Application.builder().token(TOKEN).build()

# === Хэндлеры ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Отправить файл с переводом", "Написать админам"]]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Выберите действие:", reply_markup=markup)
    return CHOOSING

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

async def forward_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.forward_message(
        chat_id=ADMIN_CHAT_ID,
        from_chat_id=update.message.chat.id,
        message_id=update.message.message_id
    )
    await update.message.reply_text(
        "Ваше сообщение отправлено администраторам! Спасибо ❤️"
    )
    return CHOOSING

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Диалог отменён. Напишите /start для начала.")
    return ConversationHandler.END

# ConversationHandler
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        CHOOSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_choice)],
        TYPING_TO_ADMIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, forward_to_admin)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

application.add_handler(conv_handler)

# === Flask route для Telegram webhook ===
@app_flask.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put(update)
    return 'ok'

# === Запуск Flask приложения и установка вебхука ===
if __name__ == '__main__':
    import asyncio

    async def set_webhook():
        webhook_url = f"{YOUR_WEBHOOK_URL}/webhook"
        await application.bot.set_webhook(url=webhook_url)
        print(f"Webhook установлен на: {webhook_url}")

    asyncio.run(set_webhook())
    app_flask.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
