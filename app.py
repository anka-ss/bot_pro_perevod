import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = 7367401537

ASKING_ADMINS, = range(1)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["Отправить файл с переводом", "Написать админам"]
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Выберите действие:", reply_markup=markup
    )

# Обработка кнопок
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "Отправить файл с переводом":
        await update.message.reply_text(
            "Чтобы отправить свой файл, заполните мини-анкету: https://tally.so/r/3qQZg2. Это займет всего пару минут!"
        )
    elif text == "Написать админам":
        await update.message.reply_text(
            "Здесь можно написать, что угодно. Мы ответим вам в ближайшее время. "
            "Пожалуйста, добавьте в сообщение свой ник в формате @никнейм, чтобы мы могли связаться с вами."
        )
        # Сохраняем, что этот пользователь будет писать админу
        context.user_data["awaiting_message"] = True

# Ловим все последующие сообщения
async def forward_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_message"):
        await context.bot.forward_message(
            chat_id=ADMIN_CHAT_ID,
            from_chat_id=update.message.chat.id,
            message_id=update.message.message_id
        )
        await update.message.reply_text(
            "Ваше сообщение отправлено администраторам!"
        )
        context.user_data["awaiting_message"] = False

# Основной запуск
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(
        filters.TEXT & (~filters.COMMAND),
        handle_buttons
    ))
    app.add_handler(MessageHandler(
        filters.ALL,
        forward_to_admin
    ))

    app.run_polling()

if __name__ == "__main__":
    main()
