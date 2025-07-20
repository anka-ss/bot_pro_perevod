import asyncio
import logging
import os
from datetime import datetime, timedelta
from collections import defaultdict
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
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

# Словарь для хранения состояний пользователей (ожидают ли ответа админам)
waiting_for_admin_message = {}

# Словарь для связывания сообщений админа с пользователями
# Формат: {message_id_от_бота_в_админ_чате: user_id}
admin_message_to_user = {}

# Статистика
stats = {
    'total_users': set(),  # Уникальные пользователи
    'messages_today': 0,   # Сообщения за сегодня
    'messages_this_week': 0,  # Сообщения за неделю
    'daily_messages': defaultdict(int),  # По дням
    'start_time': datetime.now()  # Время запуска бота
}

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def update_stats(user_id):
    """Обновляет статистику при новом сообщении"""
    now = datetime.now()
    today = now.date()
    
    # Добавляем пользователя в уникальные
    stats['total_users'].add(user_id)
    
    # Увеличиваем счетчики
    stats['daily_messages'][today] += 1
    
    # Пересчитываем сегодняшние сообщения
    stats['messages_today'] = stats['daily_messages'][today]
    
    # Пересчитываем сообщения за неделю
    week_ago = today - timedelta(days=7)
    stats['messages_this_week'] = sum(
        count for date, count in stats['daily_messages'].items() 
        if date >= week_ago
    )
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
    # Работаем только в личных чатах
    if message.chat.type != 'private':
        return
    
    # Обновляем статистику
    update_stats(message.from_user.id)
        
    await message.answer(
        "Привет! 👋\n\nВыберите действие:",
        reply_markup=get_main_keyboard()
    )

@dp.message(Command('stats'))
async def stats_handler(message: types.Message):
    """Обработчик команды /stats - только для админов"""
    # Проверяем, что это админ (сообщение из админского чата или от админа)
    is_admin = (
        str(message.chat.id) == ADMIN_GROUP_ID or  # Сообщение из админской группы
        str(message.from_user.id) == ADMIN_GROUP_ID.replace('-', '')  # Личное сообщение от админа
    )
    
    if not is_admin:
        return  # Игнорируем команду от обычных пользователей
    
    # Формируем статистику
    uptime = datetime.now() - stats['start_time']
    uptime_str = f"{uptime.days} дн. {uptime.seconds // 3600} ч. {(uptime.seconds % 3600) // 60} мин."
    
    # Последние 7 дней
    recent_days = []
    for i in range(6, -1, -1):  # От 6 дней назад до сегодня
        day = datetime.now().date() - timedelta(days=i)
        count = stats['daily_messages'].get(day, 0)
        day_name = "Сегодня" if i == 0 else f"{day.strftime('%d.%m')}"
        recent_days.append(f"  {day_name}: {count}")
    
    stats_text = f"""📊 **Статистика бота**

👥 **Уникальные пользователи:** {len(stats['total_users'])}
📨 **Сообщений сегодня:** {stats['messages_today']}
📈 **Сообщений за неделю:** {stats['messages_this_week']}

📅 **По дням:**
{chr(10).join(recent_days)}

⏱️ **Время работы:** {uptime_str}
🚀 **Запущен:** {stats['start_time'].strftime('%d.%m.%Y %H:%M')}"""
    
    await message.answer(stats_text, parse_mode='Markdown')

@dp.message(lambda message: message.text == "📤 Отправить файлик")
async def send_file_handler(message: types.Message):
    """Обработчик кнопки 'Отправить файлик'"""
    # Работаем только в личных чатах
    if message.chat.type != 'private':
        return
        
    await message.answer(
        "Чтобы отправить файлик, надо заполнить мини-анкету: ссылка. Это займет всего пару минут ✨",
        reply_markup=get_main_keyboard()
    )

@dp.message(lambda message: message.text == "✍️ Написать админам")
async def contact_admin_handler(message: types.Message):
    """Обработчик кнопки 'Написать админам'"""
    # Работаем только в личных чатах
    if message.chat.type != 'private':
        return
    
    # Помечаем пользователя как ожидающего ввода сообщения для админов
    waiting_for_admin_message[message.from_user.id] = True
    
    # Обновляем статистику
    update_stats(message.from_user.id)
        
    await message.answer(
        "Напишите ваше сообщение — и админы ответят так быстро, как смогут ✍️. "
        "Обязательно напишите в конце свой @никнейм",
        reply_markup=get_main_keyboard()
    )

@dp.message()
async def message_handler(message: types.Message):
    """Обработчик всех остальных сообщений"""
    
    # Если сообщение из админского чата и это ответ на сообщение бота
    if str(message.chat.id) == ADMIN_GROUP_ID and message.reply_to_message and message.reply_to_message.from_user.id == bot.id:
        # Ищем пользователя для ответа
        original_message_id = message.reply_to_message.message_id
        target_user_id = admin_message_to_user.get(original_message_id)
        
        if target_user_id:
            try:
                # Отправляем ответ пользователю
                await bot.send_message(
                    chat_id=target_user_id,
                    text=f"💬 Ответ от админов:\n\n{message.text}",
                    reply_markup=get_main_keyboard()
                )
                
                # Подтверждаем админу
                await message.reply("✅ Ответ отправлен пользователю!")
                
                # Удаляем связь (необязательно, но экономит память)
                del admin_message_to_user[original_message_id]
                
            except Exception as e:
                logging.error(f"Ошибка при отправке ответа пользователю: {e}")
                await message.reply("❌ Ошибка при отправке ответа пользователю")
        else:
            await message.reply("❌ Не удалось найти пользователя для ответа")
        return
    
    # Работаем только в личных чатах для обычных пользователей
    if message.chat.type != 'private':
        return
    
    user_id = message.from_user.id
    
    # Проверяем, ожидает ли пользователь ввода сообщения для админов
    if waiting_for_admin_message.get(user_id, False):
        # Убираем пометку
        waiting_for_admin_message[user_id] = False
        
        # Пересылаем сообщение админам
        try:
            # Формируем сообщение для админов
            user_info = f"👤 Пользователь: {message.from_user.full_name}"
            if message.from_user.username:
                user_info += f" (@{message.from_user.username})"
            user_info += f"\n🆔 ID: {message.from_user.id}"
            
            admin_message = f"{user_info}\n\n📝 Сообщение:\n{message.text}"
            
            # Отправляем в админскую группу
            logging.info(f"Отправляем сообщение в группу: {ADMIN_GROUP_ID}")
            result = await bot.send_message(
                chat_id=ADMIN_GROUP_ID,
                text=admin_message
            )
            
            # Сохраняем связь между сообщением админа и пользователем
            admin_message_to_user[result.message_id] = user_id
            
            logging.info(f"Сообщение отправлено успешно: {result.message_id}")
            
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

async def health_check(request):
    """Health check endpoint для мониторинга"""
    return web.Response(text="Bot is running!")

def main():
    """Основная функция запуска приложения"""
    
    # Создаем веб-приложение
    app = Application()
    
    # Добавляем health check
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    
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
