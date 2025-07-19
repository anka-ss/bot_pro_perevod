import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from aiohttp.web_app import Application

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Получаем переменные окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_GROUP_ID = os.getenv('ADMIN_GROUP_ID', '-7367401537')
WEBHOOK_HOST = os.getenv('RENDER_EXTERNAL_URL', 'https://your-app.onrender.com')
WEBHOOK_PATH = f'/webhook/{BOT_TOKEN}'
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def get_main_keyboard():
    """Создает основную клавиатуру с кнопками"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📤 Отправить файлик")],
            [KeyboardButton(text="✍️ Написать админам")]
        ],
        resize_keyboard=True,  # Подгоняет размер кнопок
        one_time_keyboard=False,  # Клавиатура остается после нажатия
        persistent=True  # Клавиатура всегда видна
    )
    return keyboard

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    """Обработчик команды /start"""
    await message.answer(
        "Привет! 👋\n\nВыберите действие:",
        reply_markup=get_main_keyboard()
    )

@dp.message(lambda message: message.text == "📤 Отправить файлик")
async def send_file_handler(message: types.Message):
    """Обработчик кнопки 'Отправить файлик'"""
    await message.answer(
        "Чтобы отправить файлик, надо заполнить мини-анкету: ссылка. Это займет всего пару минут ✨",
        reply_markup=get_main_keyboard()
    )

@dp.message(lambda message: message.text == "✍️ Написать админам")
async def contact_admin_handler(message: types.Message):
    """Обработчик кнопки 'Написать админам'"""
    await message.answer(
        "Ответьте на это сообщение — и админы ответят так быстро, как смогут ✍️. "
        "Обязательно напишите в конце свой @никнейм",
        reply_markup=get_main_keyboard()
    )

@dp.message()
async def message_handler(message: types.Message):
    """Обработчик всех остальных сообщений"""
    
    # Проверяем, является ли сообщение ответом на сообщение бота
    if message.reply_to_message and message.reply_to_message.from_user.id == bot.id:
        # Это ответ на сообщение бота - пересылаем в админскую группу
        try:
            # Формируем сообщение для админов
            user_info = f"👤 Пользователь: {message.from_user.full_name}"
            if message.from_user.username:
                user_info += f" (@{message.from_user.username})"
            user_info += f"\n🆔 ID: {message.from_user.id}"
            
            admin_message = f"{user_info}\n\n📝 Сообщение:\n{message.text}"
            
            # Отправляем в админскую группу
            await bot.send_message(
                chat_id=ADMIN_GROUP_ID,
                text=admin_message
            )
            
            # Подтверждаем отправку пользователю
            await message.answer(
                "✅ Ваше сообщение отправлено админам!",
                reply_markup=get_main_keyboard()
            )
            
        except Exception as e:
            logging.error(f"Ошибка при отправке сообщения админам: {e}")
            await message.answer(
                "❌ Произошла ошибка при отправке сообщения. Попробуйте позже.",
                reply_markup=get_main_keyboard()
            )
    else:
        # Обычное сообщение - показываем меню
        await message.answer(
            "Выберите действие:",
            reply_markup=get_main_keyboard()
        )

async def on_startup():
    """Настройка webhook при запуске"""
    logging.info(f"Настройка webhook: {WEBHOOK_URL}")
    await bot.set_webhook(url=WEBHOOK_URL, drop_pending_updates=True)

async def on_shutdown():
    """Очистка при завершении"""
    logging.info("Удаление webhook...")
    await bot.delete_webhook()
    await bot.session.close()

def main():
    """Основная функция запуска приложения"""
    
    # Создаем веб-приложение
    app = Application()
    
    # Настраиваем webhook handler
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    
    # Настраиваем приложение
    setup_application(app, dp, bot=bot)
    
    # Добавляем обработчики запуска и завершения
    app.on_startup.append(lambda app: asyncio.create_task(on_startup()))
    app.on_shutdown.append(lambda app: asyncio.create_task(on_shutdown()))
    
    # Запускаем веб-сервер
    port = int(os.getenv('PORT', 10000))
    logging.info(f"Запуск сервера на порту {port}")
    web.run_app(app, host='0.0.0.0', port=port)

if __name__ == '__main__':
    main()
