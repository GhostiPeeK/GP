import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery, LabeledPrice,
    PreCheckoutQuery
)
from aiogram.client.bot import DefaultBotProperties
from config import BOT_TOKEN, CURRENCY, PAYMENT_AMOUNTS, GAMES, ADMIN_ID
from database import db
from keyboards import (
    get_main_menu, get_games_inline, get_amounts_inline,
    get_profile_inline, get_admin_inline, get_back_to_main
)

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
    
    await message.answer(
        f"👋 <b>Привет, {user.first_name}!</b>\n\n"
        f"🎮 Здесь ты можешь пополнить баланс любимых игр.\n"
        f"💎 Оплата принимается в Telegram Stars.\n\n"
        f"👇 Выбери действие в меню снизу:",
        reply_markup=get_main_menu()
    )

@dp.message(lambda message: message.text == "🎮 Игры")
async def menu_games(message: Message):
    """Кнопка Игры"""
    await message.answer(
        "🎮 <b>Выбери игру:</b>",
        reply_markup=get_games_inline()
    )

@dp.message(lambda message: message.text == "⭐ Пополнить")
async def menu_topup(message: Message):
    """Кнопка Пополнить"""
    await message.answer(
        "🎮 <b>Сначала выбери игру:</b>",
        reply_markup=get_games_inline()
    )

@dp.message(lambda message: message.text == "📊 Профиль")
async def menu_profile(message: Message):
    """Кнопка Профиль"""
    user_stats = db.get_user_stats(message.from_user.id)
    
    if user_stats and user_stats['total_payments'] > 0:
        text = (
            f"📊 <b>Твой профиль</b>\n\n"
            f"🆔 ID: <code>{message.from_user.id}</code>\n"
            f"👤 Имя: {message.from_user.first_name}\n"
            f"💰 Всего потрачено: {user_stats['total_spent_stars']} ⭐\n"
            f"🛒 Всего покупок: {user_stats['total_payments']}\n"
            f"📅 С нами с: {user_stats['registered_at'][:10]}"
        )
    else:
        text = (
            f"📊 <b>Твой профиль</b>\n\n"
            f"🆔 ID: <code>{message.from_user.id}</code>\n"
            f"👤 Имя: {message.from_user.first_name}\n\n"
            f"💡 У тебя пока нет покупок.\n"
            f"🎮 Выбери игру и сделай первый заказ!"
        )
    
    await message.answer(text, reply_markup=get_profile_inline())

@dp.message(lambda message: message.text == "❓ Помощь")
async def menu_help(message: Message):
    """Кнопка Помощь"""
    text = (
        "❓ <b>Помощь</b>\n\n"
        "🎮 <b>Как пополнить игру?</b>\n"
        "1. Нажми «🎮 Игры»\n"
        "2. Выбери нужную игру\n"
        "3. Выбери сумму в Stars\n"
        "4. Оплати счет\n"
        "5. Получи пополнение\n\n"
        "💎 <b>Где взять Stars?</b>\n"
        "• Купить в Telegram Premium\n"
        "• Через @PremiumBot\n"
        "• В App Store / Google Play\n\n"
        "⏱ <b>Сколько ждать?</b>\n"
        "Пополнение приходит в течение 1-2 минут\n\n"
        "📞 <b>Связь с поддержкой:</b>\n"
        "@твой_username"
    )
    
    await message.answer(text, reply_markup=get_back_to_main())

@dp.message(lambda message: message.text == "👥 Рефералы")
async def menu_referrals(message: Message):
    """Кнопка Рефералы"""
    await message.answer(
        "👥 <b>Реферальная программа</b>\n\n"
        "🚀 Скоро тут будет реферальная система!\n"
        "Приводи друзей и получай бонусы.",
        reply_markup=get_back_to_main()
    )

@dp.message(lambda message: message.text == "📞 Контакты")
async def menu_contacts(message: Message):
    """Кнопка Контакты"""
    text = (
        "📞 <b>Контакты</b>\n\n"
        "👨‍💻 Админ: @твой_username\n"
        "📧 Почта: твоя@почта.ru\n"
        "💬 Чат: @твой_чат\n\n"
        "🕐 Работаем 24/7"
    )
    
    await message.answer(text, reply_markup=get_back_to_main())

@dp.callback_query(lambda c: c.data.startswith('game_'))
async def process_game_selection(callback: CallbackQuery):
    """Выбор игры"""
    game_id = callback.data.replace('game_', '')
    game_name = GAMES[game_id]
    
    users[callback.from_user.id] = {'game': game_id, 'game_name': game_name}
    
    await callback.message.edit_text(
        f"🎮 <b>Игра:</b> {game_name}\n"
        f"💰 <b>Выбери сумму пополнения:</b>",
        reply_markup=get_amounts_inline()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith('amount_'))
async def process_amount(callback: CallbackQuery):
    """Выбор суммы и создание счета"""
    amount_stars = int(callback.data.replace('amount_', ''))
    user_id = callback.from_user.id
    
    if user_id not in users:
        await callback.message.answer("Ошибка, начни заново /start")
        await callback.answer()
        return
    
    game_name = users[user_id]['game_name']
    
    prices = [LabeledPrice(label=f"Пополнение {game_name}", amount=amount_stars)]
    
    await callback.message.answer_invoice(
        title=f"Пополнение {game_name}",
        description=f"Покупка на {amount_stars} ⭐ для игры {game_name}",
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
    
    await message.answer(
        f"✅ <b>ОПЛАЧЕНО!</b>\n\n"
        f"⭐ Сумма: {amount_stars} Telegram Stars\n"
        f"🎮 Игра: {game_name}\n"
        f"💰 Статус: <b>Пополнение выполняется</b>\n\n"
        f"🔜 В течение 1-2 минут баланс будет зачислен.\n"
        f"Спасибо за покупку, бро! 💪\n\n"
        f"🎫 ID: <code>{charge_id}</code>",
        reply_markup=get_back_to_main()
    )
    
    logging.info(f"ПЛАТЕЖ: User {message.from_user.id} | Game: {game_id} | Stars: {amount_stars}")

@dp.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    """Возврат в главное меню"""
    await callback.message.answer(
        "🏠 <b>Главное меню</b>\n\n"
        "👇 Выбери действие:",
        reply_markup=get_main_menu()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "back_to_games")
async def back_to_games(callback: CallbackQuery):
    """Возврат к выбору игр"""
    await callback.message.edit_text(
        "🎮 <b>Выбери игру:</b>",
        reply_markup=get_games_inline()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "to_games")
async def to_games(callback: CallbackQuery):
    """Переход к играм"""
    await callback.message.answer(
        "🎮 <b>Выбери игру:</b>",
        reply_markup=get_games_inline()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "profile_history")
async def profile_history(callback: CallbackQuery):
    """История покупок"""
    # Здесь можно показать последние покупки
    await callback.message.answer(
        "📊 <b>История покупок</b>\n\n"
        "🚀 Функция в разработке!",
        reply_markup=get_back_to_main()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    """Статистика для админа"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    
    games_stats = db.get_game_stats()
    recent = db.get_recent_payments(5)
    
    text = "👑 <b>Админ панель - Статистика</b>\n\n"
    
    if games_stats:
        text += "<b>По играм:</b>\n"
        for game in games_stats:
            text += f"• {game['game_name']}: {game['total_payments']} покупок | {game['total_stars']} ⭐\n"
    
    text += "\n<b>Последние 5 платежей:</b>\n"
    if recent:
        for p in recent:
            text += f"• {p['game_name']}: {p['amount_stars']} ⭐ ({p['created_at'][:16]})\n"
    
    await callback.message.answer(text, reply_markup=get_admin_inline())
    await callback.answer()

@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    """Команда для входа в админку"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Доступ запрещен")
        return
    
    await message.answer(
        "👑 <b>Админ панель</b>\n\n"
        "Выбери раздел:",
        reply_markup=get_admin_inline()
    )

@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    """Команда статистики"""
    await menu_profile(message)

async def main():
    """Запуск бота"""
    logging.info("Бот запускается...")
    
    try:
        me = await bot.get_me()
        logging.info(f"Бот @{me.username} успешно запущен!")
    except Exception as e:
        logging.error(f"Ошибка подключения: {e}")
        return
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
