import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Получаем токен бота и ID группы из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_GROUP_ID = os.getenv('ADMIN_GROUP_ID', '-7367401537')  # ID группы с минусом

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def get_main_keyboard():
    """Создает основную клавиатуру с кнопками"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="📤 Отправить файлик", callback_data="send_file"),
        InlineKeyboardButton(text="✍️ Написать админам", callback_data="contact_admin")
    )
    builder.adjust(1)  # По одной кнопке в ряд
    return builder.as_markup()

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    """Обработчик команды /start"""
    await message.answer(
        "Привет! 👋\n\nВыберите действие:",
        reply_markup=get_main_keyboard()
    )

@dp.callback_query(lambda c: c.data == "send_file")
async def send_file_handler(callback: types.CallbackQuery):
    """Обработчик кнопки 'Отправить файлик'"""
    await callback.message.answer(
        "Чтобы отправить файлик, надо заполнить мини-анкету: ссылка. Это займет всего пару минут ✨",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "contact_admin")
async def contact_admin_handler(callback: types.CallbackQuery):
    """Обработчик кнопки 'Написать админам'"""
    await callback.message.answer(
        "Ответьте на это сообщение — и админы ответят так быстро, как смогут ✍️. "
        "Обязательно напишите в конце свой @никнейм",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()

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

async def main():
    """Основная функция запуска бота"""
    try:
        logging.info("Бот запускается...")
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Ошибка при запуске бота: {e}")
    finally:
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())
