import os
import logging
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup, Bot
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes,
    ConversationHandler, filters, Dispatcher
)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)

# Переменные окружения
TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
ADMIN_CHAT_ID = 7367401537

# Состояния
CHOOSING, TYPING_TO_ADMIN = range(2)

# Создание приложения бота
application = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Start command from user {update.effective_user.id}")
    keyboard = [["Отправить файл с переводом", "Написать админам"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Выберите действие:",
        reply_markup=reply_markup
    )
    return CHOOSING

async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Choice: {update.message.text}")
    keyboard = [["Отправить файл с переводом", "Написать админам"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    text = update.message.text
    if text == "Отправить файл с переводом":
        await update.message.reply_text(
            "Чтобы отправить свой файл, заполните мини-анкету: https://tally.so/r/3qQZg2. Это займет всего пару минут!",
            reply_markup=reply_markup
        )
        return CHOOSING
    elif text == "Написать админам":
        await update.message.reply_text(
            "Здесь можно написать что угодно. Мы ответим вам в ближайшее время.\n"
            "Пожалуйста, добавьте в сообщение свой ник в формате @никнейм."
        )
        return TYPING_TO_ADMIN
    else:
        await update.message.reply_text(
            "Пожалуйста, выберите одну из кнопок.",
            reply_markup=reply_markup
        )
        return CHOOSING

async def forward_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.forward_message(
        chat_id=ADMIN_CHAT_ID,
        from_chat_id=update.message.chat.id,
        message_id=update.message.message_id
    )
    keyboard = [["Отправить файл с переводом", "Написать админам"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Ваше сообщение отправлено администраторам! Спасибо ❤️",
        reply_markup=reply_markup
    )
    return CHOOSING

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Диалог отменён. Напишите /start для начала.")
    return ConversationHandler.END

# Настройка ConversationHandler
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        CHOOSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_choice)],
        TYPING_TO_ADMIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, forward_to_admin)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

application.add_handler(conv_handler)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), application.bot)
        application.update_queue.put_nowait(update)
        return 'OK'
    except Exception as e:
        logger.error(f"Error in webhook: {e}")
        return 'Error', 500

@app.route('/')
def index():
    return 'Bot is running!'

if __name__ == '__main__':
    # Установка webhook
    try:
        import asyncio
        bot = Bot(TOKEN)
        webhook_url = f"{WEBHOOK_URL}/webhook"
        asyncio.run(bot.set_webhook(url=webhook_url))
        logger.info(f"Webhook set to {webhook_url}")
    except Exception as e:
        logger.error(f"Failed to set webhook: {e}")
    
    # Запуск Flask приложения
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
