import os
import logging
from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
import asyncio

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация
API_ID = 23921954
API_HASH = 'e8b91c0c46c3edc7b063e8ef0096616f'
PHONE = '+79053089455'
BOT_TOKEN = '7554368701:AAEiNqwwnSKXvj5OEkHGZl_f1c8j3mszp48'
CHAT_TO_MONITOR = -1001484212179  # ⬅️ ИСПРАВЛЕННЫЙ ID ГРУППЫ "М. ДПС УЧАЛЫ🚔🚔🚔"
YOUR_USER_ID = 463717122  # Ваш user_id

# Флаг для управления мониторингом
is_monitoring = True

# Инициализация клиентов
user_client = TelegramClient('user_session', API_ID, API_HASH)
bot_client = TelegramClient('bot_session', API_ID, API_HASH)

async def send_welcome_message():
    """Отправляет приветственное сообщение"""
    try:
        welcome_text = """🤖 **Добро пожаловать!**

Я буду присылать вам свежую информацию из группы "М. ДПС УЧАЛЫ".

📋 **Команды:**
/start - начать мониторинг
/stop - остановить мониторинг
/status - статус работы

💡 **Мониторинг запущен автоматически!**"""
        
        await bot_client.send_message(YOUR_USER_ID, welcome_text)
        logger.info("Приветственное сообщение отправлено")
    except Exception as e:
        logger.error(f"Ошибка отправки приветствия: {e}")

async def send_to_user(text, media=None):
    """Функция для отправки сообщений пользователю"""
    try:
        if not is_monitoring:
            return
            
        if media and os.path.exists(media):
            await bot_client.send_file(
                YOUR_USER_ID, 
                media, 
                caption=text[:2000] if text else None
            )
            logger.info("Медиа сообщение отправлено")
        else:
            await bot_client.send_message(YOUR_USER_ID, text[:4000])
            logger.info("Текстовое сообщение отправлено")
                
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {e}")

@bot_client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    """Обработчик команды /start"""
    global is_monitoring
    if event.sender_id == YOUR_USER_ID:
        is_monitoring = True
        await event.reply("✅ **Мониторинг запущен!**\nТеперь вы будете получать сообщения из группы.")
        logger.info("Мониторинг запущен по команде /start")

@bot_client.on(events.NewMessage(pattern='/stop'))
async def stop_handler(event):
    """Обработчик команды /stop"""
    global is_monitoring
    if event.sender_id == YOUR_USER_ID:
        is_monitoring = False
        await event.reply("⏹️ **Мониторинг остановлен!**\nСообщения из группы приходить не будут.")
        logger.info("Мониторинг остановлен по команде /stop")

@bot_client.on(events.NewMessage(pattern='/status'))
async def status_handler(event):
    """Обработчик команды /status"""
    if event.sender_id == YOUR_USER_ID:
        status = "✅ **запущен**" if is_monitoring else "⏹️ **остановлен**"
        await event.reply(f"📊 **Статус мониторинга:** {status}")

@user_client.on(events.NewMessage(chats=CHAT_TO_MONITOR))
async def group_message_handler(event):
    """Обработчик новых сообщений из группы"""
    global is_monitoring
    
    if not is_monitoring:
        return  # Мониторинг остановлен
    
    try:
        message = event.message
        sender = await message.get_sender()
        
        # Получаем имя отправителя
        if hasattr(sender, 'title'):
            sender_name = sender.title
        elif hasattr(sender, 'username') and sender.username:
            sender_name = f"@{sender.username}"
        elif hasattr(sender, 'first_name'):
            sender_name = f"{sender.first_name or ''} {sender.last_name or ''}".strip()
        else:
            sender_name = "Неизвестный отправитель"
        
        # Формируем текст сообщения
        text = f"📩 **Новое сообщение из группы**\n"
        text += f"👤 **Отправитель:** {sender_name}\n"
        text += f"💬 **Текст:** {message.text or 'Нет текста'}\n"
        text += f"⏰ **Время:** {message.date.strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Обработка медиа
        media_path = None
        if message.media:
            try:
                if isinstance(message.media, (MessageMediaPhoto, MessageMediaDocument)):
                    media_path = await message.download_media(file='downloads/')
                    media_type = 'Фото' if isinstance(message.media, MessageMediaPhoto) else 'Документ'
                    text += f"\n📎 **Тип медиа:** {media_type}"
                    logger.info(f"Медиа файл загружен: {media_path}")
            except Exception as e:
                logger.error(f"Ошибка загрузки медиа: {e}")
        
        # Отправляем сообщение пользователю
        await send_to_user(text, media_path)
        
        # Удаляем временный файл
        if media_path and os.path.exists(media_path):
            try:
                os.remove(media_path)
            except Exception as e:
                logger.error(f"Ошибка удаления файла: {e}")
            
    except Exception as e:
        logger.error(f"Ошибка обработки сообщения: {e}")

async def main():
    """Основная функция"""
    try:
        # Запускаем бота первым
        logger.info("🔄 Запускаем бота...")
        await bot_client.start(bot_token=BOT_TOKEN)
        logger.info("✅ Бот запущен")
        
        # Отправляем приветственное сообщение
        await send_welcome_message()
        
        # Запускаем клиент пользователя
        logger.info("🔄 Запускаем аккаунт пользователя...")
        await user_client.start(phone=PHONE)
        logger.info("✅ Аккаунт пользователя успешно запущен")
        
        # Получаем информацию о себе
        me = await user_client.get_me()
        logger.info(f"✅ Авторизован как {me.first_name} (id: {me.id})")
        
        # Проверяем доступ к группе
        try:
            chat = await user_client.get_entity(CHAT_TO_MONITOR)
            logger.info(f"✅ Мониторинг группы: {chat.title} (id: {chat.id})")
        except Exception as e:
            logger.error(f"❌ Ошибка доступа к группе: {e}")
            return
        
        logger.info("🚀 Бот начал мониторинг сообщений...")
        logger.info("💡 Используйте команды /start, /stop, /status в личке с ботом")
        logger.info("⏹️ Для остановки нажмите Ctrl+C")
        
        # Ожидаем завершения обоих клиентов
        await asyncio.gather(
            user_client.run_until_disconnected(),
            bot_client.run_until_disconnected()
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка в основной функции: {e}")

if __name__ == '__main__':
    # Создаем папку для загрузок
    os.makedirs('downloads', exist_ok=True)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")