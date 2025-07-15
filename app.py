import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes,
    ConversationHandler, filters
)

TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
ADMIN_CHAT_ID = 7367401537

CHOOSING, TYPING_TO_ADMIN = range(2)

# Create PTB app
bot_app = Application.builder().token(TOKEN).build()

# Start handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Отправить файл с переводом", "Написать админам"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Выберите действие:",
        reply_markup=reply_markup
    )
    return CHOOSING

# Choice handler
async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

# Forward to admin
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

# Cancel handler
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Диалог отменён. Напишите /start для начала.")
    return ConversationHandler.END

# Conversation
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        CHOOSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_choice)],
        TYPING_TO_ADMIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, forward_to_admin)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

bot_app.add_handler(conv_handler)

# Entrypoint
if __name__ == '__main__':
    import asyncio

    async def main():
        await bot_app.bot.delete_webhook()
        await bot_app.run_webhook(
            listen="0.0.0.0",
            port=int(os.environ.get('PORT', 5000)),
            webhook_url=f"{WEBHOOK_URL}/webhook"
        )

    asyncio.run(main())
