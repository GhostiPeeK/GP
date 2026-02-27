import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery, LabeledPrice,
    PreCheckoutQuery, InlineKeyboardMarkup, 
    InlineKeyboardButton
)
from aiogram.client.bot import DefaultBotProperties
from config import BOT_TOKEN, CURRENCY, PAYMENT_AMOUNTS, GAMES, ADMIN_ID
from database import db

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# Хранилище пользователей (только для временных данных)
users = {}

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user = message.from_user
    
    # Сохраняем пользователя в БД
    db.add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    # Создаем клавиатуру с играми
    buttons = []
    row = []
    for i, (game_id, game_name) in enumerate(GAMES.items(), 1):
        row.append(InlineKeyboardButton(text=game_name, callback_data=f"game_{game_id}"))
        if i % 2 == 0:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await message.answer(
        "👋 Привет, бро! Выбери игру для пополнения:\n\n"
        "💎 Оплата принимается в Telegram Stars",
        reply_markup=keyboard
    )

@dp.callback_query(lambda c: c.data.startswith('game_'))
async def process_game_selection(callback: CallbackQuery):
    """Выбор игры"""
    game_id = callback.data.replace('game_', '')
    game_name = GAMES[game_id]
    
    # Сохраняем выбор пользователя
    users[callback.from_user.id] = {'game': game_id, 'game_name': game_name}
    
    # Клавиатура с суммами в звездах
    buttons = []
    row = []
    for i, amount in enumerate(PAYMENT_AMOUNTS, 1):
        row.append(InlineKeyboardButton(text=f"{amount} ⭐", callback_data=f"amount_{amount}"))
        if i % 3 == 0:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    
    # Кнопка "Назад"
    buttons.append([InlineKeyboardButton(text="◀ Назад к играм", callback_data="back_to_games")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.answer(
        f"🎮 Игра: {game_name}\n"
        f"💰 Выбери сумму пополнения (в Telegram Stars):",
        reply_markup=keyboard
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "back_to_games")
async def back_to_games(callback: CallbackQuery):
    """Возврат к выбору игр"""
    buttons = []
    row = []
    for i, (game_id, game_name) in enumerate(GAMES.items(), 1):
        row.append(InlineKeyboardButton(text=game_name, callback_data=f"game_{game_id}"))
        if i % 2 == 0:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.answer(
        "👋 Выбери игру для пополнения:",
        reply_markup=keyboard
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith('amount_'))
async def process_amount(callback: CallbackQuery):
    """Выбор суммы и создание счета в Stars"""
    amount_stars = int(callback.data.replace('amount_', ''))
    user_id = callback.from_user.id
    
    if user_id not in users:
        await callback.message.answer("Ошибка, начни заново /start")
        await callback.answer()
        return
    
    game_name = users[user_id]['game_name']
    
    # Создаем счет в Telegram Stars
    prices = [LabeledPrice(label=f"Пополнение {game_name}", amount=amount_stars)]
    
    await callback.message.answer_invoice(
        title=f"Пополнение {game_name}",
        description=f"Покупка на {amount_stars} ⭐ для игры {game_name}\n\n"
                    f"✅ После оплаты звезды будут списаны, а баланс игры пополнен автоматически",
        payload=f"game_{users[user_id]['game']}_{amount_stars}_{user_id}",
        provider_token="",
        currency="XTR",
        prices=prices,
        start_parameter="game_payment"
    )
    await callback.answer()

@dp.pre_checkout_query()
async def on_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    """Обязательный обработчик предпроверки"""
    await pre_checkout_query.answer(ok=True)

@dp.message(lambda message: message.successful_payment is not None)
async def on_successful_payment(message: Message):
    """Обработчик успешного платежа"""
    payment = message.successful_payment
    amount_stars = payment.total_amount
    payload = payment.invoice_payload
    charge_id = payment.telegram_payment_charge_id
    
    # Парсим payload
    parts = payload.split('_')
    game_id = parts[1] if len(parts) > 1 else "unknown"
    game_name = GAMES.get(game_id, 'Неизвестная игра')
    
    # Сохраняем платеж в БД
    db.add_payment(
        user_id=message.from_user.id,
        game_id=game_id,
        game_name=game_name,
        amount_stars=amount_stars,
        charge_id=charge_id
    )
    
    # Отвечаем пользователю
    await message.answer(
        f"✅ <b>ОПЛАЧЕНО!</b>\n\n"
        f"⭐ Сумма: {amount_stars} Telegram Stars\n"
        f"🎮 Игра: {game_name}\n"
        f"💰 Статус: <b>Пополнение выполняется</b>\n\n"
        f"🔜 В течение 1-2 минут баланс будет зачислен.\n"
        f"Спасибо за покупку, бро! 💪\n\n"
        f"🎫 ID транзакции: <code>{charge_id}</code>",
        parse_mode="HTML"
    )
    
    logging.info(f"ПЛАТЕЖ: User {message.from_user.id} | Game: {game_id} | Stars: {amount_stars}")

@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    """Показывает статистику пользователя"""
    user_stats = db.get_user_stats(message.from_user.id)
    
    if user_stats and user_stats['total_payments'] > 0:
        await message.answer(
            f"📊 <b>Твоя статистика</b>\n\n"
            f"💰 Всего потрачено: {user_stats['total_spent_stars']} ⭐\n"
            f"🛒 Всего покупок: {user_stats['total_payments']}\n"
            f"📅 Зарегистрирован: {user_stats['registered_at'][:10]}",
            parse_mode="HTML"
        )
    else:
        await message.answer("📊 Статистики пока нет. Соверши первую покупку!")

@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    """Админ-панель (только для админа)"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Доступ запрещен")
        return
    
    # Получаем статистику
    games_stats = db.get_game_stats()
    recent_payments = db.get_recent_payments(5)
    
    text = "👑 <b>Админ панель</b>\n\n"
    
    if games_stats:
        text += "<b>Статистика по играм:</b>\n"
        for game in games_stats:
            text += f"• {game['game_name']}: {game['total_payments']} покупок | {game['total_stars']} ⭐\n"
    else:
        text += "Пока нет статистики по играм\n"
    
    text += "\n<b>Последние 5 платежей:</b>\n"
    if recent_payments:
        for p in recent_payments:
            text += f"• {p['game_name']}: {p['amount_stars']} ⭐ ({p['created_at'][:16]})\n"
    else:
        text += "Пока нет платежей\n"
    
    await message.answer(text, parse_mode="HTML")

@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Помощь"""
    await message.answer(
        "🔍 <b>Доступные команды:</b>\n\n"
        "/start - Начать работу (выбор игры)\n"
        "/stats - Твоя статистика\n"
        "/help - Это сообщение\n\n"
        "💡 <b>Как это работает:</b>\n"
        "1. Выбираешь игру\n"
        "2. Выбираешь сумму в Stars\n"
        "3. Оплачивашь Telegram Stars\n"
        "4. Получаешь пополнение в игре\n\n"
        "❓ Вопросы? Пиши @твой_username"
    )

async def main():
    """Запуск бота"""
    logging.info("Бот запускается...")
    
    # Проверяем подключение к Telegram
    try:
        me = await bot.get_me()
        logging.info(f"Бот @{me.username} успешно запущен!")
    except Exception as e:
        logging.error(f"Ошибка подключения: {e}")
        return
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())