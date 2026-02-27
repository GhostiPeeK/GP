import logging
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.client.bot import DefaultBotProperties
from config import (
    BOT_TOKEN, ADMIN_ID, GAMES, PAYMENT_AMOUNTS,
    STARS_ENABLED, STARS_TO_RUB,
    CRYPTO_ENABLED, CRYPTO_API_KEY, CRYPTO_CURRENCIES,
    REFERRAL_BONUS, REFERRAL_BONUS_STARS
)
from database import db
from keyboards import *
from crypto_bot import CryptoBot

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# Инициализация CryptoBot
if CRYPTO_ENABLED:
    crypto_bot = CryptoBot(CRYPTO_API_KEY)
else:
    crypto_bot = None

# Хранилище пользователей
users = {}

# ============================================
# ОСНОВНЫЕ КОМАНДЫ
# ============================================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start с поддержкой рефералов"""
    user = message.from_user
    args = message.text.split()
    
    # Проверяем реферальный код
    referrer_code = None
    if len(args) > 1:
        referrer_code = args[1]
    
    # Сохраняем пользователя
    referral_code = db.add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        referrer_code=referrer_code
    )
    
    # Если есть реферер, начисляем бонус
    if referrer_code and REFERRAL_BONUS_STARS > 0:
        await message.answer(
            f"🎉 Ты пришел по реферальной ссылке!\n"
            f"⭐ Бонус {REFERRAL_BONUS_STARS} звезд будет начислен после первой покупки!"
        )
    
    await message.answer(
        f"👋 <b>Привет, {user.first_name}!</b>\n\n"
        f"🎮 Здесь ты можешь пополнить баланс любимых игр.\n"
        f"💎 Доступные способы оплаты:\n"
        f"⭐ Telegram Stars\n"
        f"₿ Криптовалюта (USDT, TON, BTC)\n\n"
        f"👇 Выбери действие в меню снизу:",
        reply_markup=get_main_menu()
    )

# ============================================
# ОБРАБОТЧИКИ МЕНЮ
# ============================================

@dp.message(lambda message: message.text == "🎮 Игры")
async def menu_games(message: Message):
    await message.answer(
        "🎮 <b>Выбери игру:</b>",
        reply_markup=get_games_inline()
    )

@dp.message(lambda message: message.text == "⭐ Пополнить")
async def menu_topup(message: Message):
    await message.answer(
        "🎮 <b>Сначала выбери игру:</b>",
        reply_markup=get_games_inline()
    )

@dp.message(lambda message: message.text == "📊 Профиль")
async def menu_profile(message: Message):
    user_stats = db.get_user_stats(message.from_user.id)
    
    if user_stats and user_stats['total_payments'] > 0:
        text = (
            f"📊 <b>Твой профиль</b>\n\n"
            f"🆔 ID: <code>{message.from_user.id}</code>\n"
            f"👤 Имя: {message.from_user.first_name}\n"
            f"💰 Всего потрачено: {user_stats['total_spent_stars']} ⭐\n"
            f"🛒 Всего покупок: {user_stats['total_payments']}\n"
            f"👥 Рефералов: {user_stats.get('referrals_count', 0)}\n"
            f"🎁 Бонусов: {user_stats.get('total_bonus', 0)} ⭐\n"
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

@dp.message(lambda message: message.text == "👥 Рефералы")
async def menu_referrals(message: Message):
    user_stats = db.get_user_stats(message.from_user.id)
    
    if user_stats and user_stats.get('referral_code'):
        referral_link = f"https://t.me/{(await bot.get_me()).username}?start={user_stats['referral_code']}"
        
        text = (
            f"👥 <b>Реферальная программа</b>\n\n"
            f"🔗 Твоя ссылка:\n"
            f"<code>{referral_link}</code>\n\n"
            f"🎁 За каждого друга ты получаешь {REFERRAL_BONUS}% от его покупок\n"
            f"⭐ Бонус за регистрацию: {REFERRAL_BONUS_STARS} ⭐\n\n"
            f"📊 Статистика:\n"
            f"• Приглашено: {user_stats.get('referrals_count', 0)} чел\n"
            f"• Заработано: {user_stats.get('total_bonus', 0)} ⭐"
        )
        
        await message.answer(text, reply_markup=get_referral_inline(user_stats['referral_code']))
    else:
        await message.answer("❌ Ошибка загрузки реферального кода")

@dp.message(lambda message: message.text == "❓ Помощь")
async def menu_help(message: Message):
    text = (
        "❓ <b>Помощь</b>\n\n"
        "🎮 <b>Как пополнить игру?</b>\n"
        "1. Нажми «🎮 Игры»\n"
        "2. Выбери нужную игру\n"
        "3. Выбери сумму в ⭐ Stars\n"
        "4. Выбери способ оплаты\n"
        "5. Оплати и получи пополнение\n\n"
        "💎 <b>Способы оплаты:</b>\n"
        "⭐ Telegram Stars - быстро и удобно\n"
        "₿ Криптовалюта - USDT, TON, BTC\n\n"
        "👥 <b>Рефералы:</b>\n"
        "Приводи друзей и получай {REFERRAL_BONUS}% от их покупок\n\n"
        "⏱ <b>Сколько ждать?</b>\n"
        "Пополнение приходит в течение 1-2 минут\n\n"
        "📞 <b>Связь с поддержкой:</b>\n"
        "@твой_username"
    )
    
    await message.answer(text, reply_markup=get_back_to_main())

@dp.message(lambda message: message.text == "📞 Контакты")
async def menu_contacts(message: Message):
    text = (
        "📞 <b>Контакты</b>\n\n"
        "👨‍💻 Админ: @твой_username\n"
        "📧 Почта: твоя@почта.ru\n"
        "💬 Чат: @твой_чат\n\n"
        "🕐 Работаем 24/7"
    )
    
    await message.answer(text, reply_markup=get_back_to_main())

# ============================================
# ОБРАБОТЧИКИ ВЫБОРА
# ============================================

@dp.callback_query(lambda c: c.data.startswith('game_'))
async def process_game_selection(callback: CallbackQuery):
    game_id = callback.data.replace('game_', '')
    game_data = GAMES.get(game_id, {})
    game_name = game_data.get('name', "Неизвестная игра")
    
    if not game_data.get('enabled', True):
        await callback.message.edit_text(
            f"❌ Игра временно недоступна",
            reply_markup=get_back_to_main()
        )
        await callback.answer()
        return
    
    users[callback.from_user.id] = {'game': game_id, 'game_name': game_name}
    
    await callback.message.edit_text(
        f"🎮 <b>Игра:</b> {game_name}\n"
        f"💰 <b>Выбери сумму в ⭐ Stars:</b>",
        reply_markup=get_amounts_inline(game_id)
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith('amount_'))
async def process_amount(callback: CallbackQuery):
    parts = callback.data.split('_')
    game_id = parts[1]
    amount_stars = int(parts[2])
    
    user_id = callback.from_user.id
    game_data = GAMES.get(game_id, {})
    game_name = game_data.get('name', "Неизвестная игра")
    
    if user_id not in users:
        users[user_id] = {}
    users[user_id]['game'] = game_id
    users[user_id]['game_name'] = game_name
    users[user_id]['amount'] = amount_stars
    
    rub_amount = amount_stars * STARS_TO_RUB
    
    # Запрашиваем аккаунт в игре
    await callback.message.edit_text(
        f"🎮 <b>Игра:</b> {game_name}\n"
        f"💰 <b>Сумма:</b> {amount_stars} ⭐ (~{rub_amount:.0f} руб)\n\n"
        f"📝 <b>Введи свой ID или ник в игре:</b>\n"
        f"(Например: 123456789 или NickName)",
        reply_markup=None
    )
    users[user_id]['awaiting_account'] = True
    await callback.answer()

@dp.message(lambda message: message.from_user.id in users and users[message.from_user.id].get('awaiting_account'))
async def process_account(message: Message):
    user_id = message.from_user.id
    account = message.text.strip()
    
    if not account:
        await message.answer("❌ Введи корректный ID или ник")
        return
    
    users[user_id]['account'] = account
    users[user_id]['awaiting_account'] = False
    
    game_id = users[user_id]['game']
    amount_stars = users[user_id]['amount']
    game_name = users[user_id]['game_name']
    rub_amount = amount_stars * STARS_TO_RUB
    
    await message.answer(
        f"🎮 <b>Игра:</b> {game_name}\n"
        f"💰 <b>Сумма:</b> {amount_stars} ⭐ (~{rub_amount:.0f} руб)\n"
        f"👤 <b>Аккаунт:</b> {account}\n\n"
        f"👇 <b>Выбери способ оплаты:</b>",
        reply_markup=get_payment_methods_inline(game_id, amount_stars)
    )

# ============================================
# ОБРАБОТЧИКИ ОПЛАТЫ
# ============================================

@dp.callback_query(lambda c: c.data.startswith('pay_stars_'))
async def pay_with_stars(callback: CallbackQuery):
    parts = callback.data.split('_')
    game_id = parts[2]
    amount_stars = int(parts[3])
    user_id = callback.from_user.id
    game_name = GAMES.get(game_id, {}).get('name', "Неизвестная игра")
    
    prices = [LabeledPrice(label=f"Пополнение {game_name}", amount=amount_stars)]
    
    await callback.message.answer_invoice(
        title=f"Пополнение {game_name}",
        description=f"Оплата {amount_stars} ⭐ Telegram Stars",
        payload=f"stars_{game_id}_{amount_stars}_{user_id}",
        provider_token="",
        currency="XTR",
        prices=prices,
        start_parameter="game_payment"
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith('pay_crypto_'))
async def pay_with_crypto(callback: CallbackQuery):
    parts = callback.data.split('_')
    game_id = parts[2]
    amount_stars = int(parts[3])
    game_name = GAMES.get(game_id, {}).get('name', "Неизвестная игра")
    
    rub_amount = amount_stars * STARS_TO_RUB
    
    await callback.message.edit_text(
        f"₿ <b>Оплата криптовалютой</b>\n\n"
        f"🎮 Игра: {game_name}\n"
        f"💰 Сумма: {amount_stars} ⭐ (~{rub_amount:.0f} руб)\n\n"
        f"👇 <b>Выбери валюту:</b>",
        reply_markup=get_crypto_currencies_inline(game_id, amount_stars)
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith('crypto_'))
async def process_crypto_currency(callback: CallbackQuery):
    parts = callback.data.split('_')
    currency = parts[1]
    game_id = parts[2]
    amount_stars = int(parts[3])
    user_id = callback.from_user.id
    game_data = GAMES.get(game_id, {})
    game_name = game_data.get('name', "Неизвестная игра")
    
    if not crypto_bot:
        await callback.message.edit_text(
            "❌ Криптоплатежи временно недоступны",
            reply_markup=get_back_to_main()
        )
        await callback.answer()
        return
    
    rub_amount = amount_stars * STARS_TO_RUB
    
    # Конвертация в крипту
    rates = {
        'USDT': rub_amount / 90,
        'TON': rub_amount / 450,
        'BTC': rub_amount / 5400000
    }
    
    crypto_amount = round(rates.get(currency, rub_amount), 6)
    
    description = f"{game_name} - {amount_stars}⭐"
    invoice = await crypto_bot.create_invoice(
        amount=crypto_amount,
        currency=currency,
        description=description,
        user_id=user_id,
        game_id=game_id
    )
    
    if invoice and invoice.get("pay_url"):
        users[user_id]['crypto_invoice'] = invoice["invoice_id"]
        users[user_id]['crypto_currency'] = currency
        users[user_id]['crypto_amount'] = crypto_amount
        users[user_id]['stars_amount'] = amount_stars
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить", url=invoice["pay_url"])],
            [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"check_crypto_{invoice['invoice_id']}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data=f"back_to_payment_{game_id}_{amount_stars}")]
        ])
        
        await callback.message.edit_text(
            f"₿ <b>Счет на оплату</b>\n\n"
            f"🎮 Игра: {game_name}\n"
            f"💰 Сумма: {amount_stars} ⭐\n"
            f"💎 Валюта: {currency}\n"
            f"💵 К оплате: {crypto_amount} {currency}\n\n"
            f"⬇️ Нажми кнопку ниже для оплаты:",
            reply_markup=keyboard
        )
    else:
        await callback.message.edit_text(
            "❌ Ошибка создания счета. Попробуй позже.",
            reply_markup=get_back_to_main()
        )
    
    await callback.answer()

# ============================================
# ОБРАБОТЧИКИ ПЛАТЕЖЕЙ
# ============================================

@dp.pre_checkout_query()
async def on_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

@dp.message(lambda message: message.successful_payment is not None)
async def on_successful_payment(message: Message):
    payment = message.successful_payment
    amount_stars = payment.total_amount
    payload = payment.invoice_payload
    charge_id = payment.telegram_payment_charge_id
    
    parts = payload.split('_')
    game_id = parts[1] if len(parts) > 1 else "unknown"
    game_name = GAMES.get(game_id, {}).get('name', 'Неизвестная игра')
    
    # Сохраняем платеж
    payment_id = db.add_payment(
        user_id=message.from_user.id,
        game_id=game_id,
        game_name=game_name,
        amount_stars=amount_stars,
        amount_real=amount_stars,
        currency="XTR",
        payment_method="stars",
        charge_id=charge_id
    )
    
    # Проверяем реферала
    user_stats = db.get_user_stats(message.from_user.id)
    if user_stats and user_stats.get('referrer_id'):
        db.process_referral_bonus(
            payment_id=payment_id,
            referrer_id=user_stats['referrer_id'],
            referral_id=message.from_user.id,
            amount_stars=amount_stars,
            bonus_percent=REFERRAL_BONUS
        )
    
    await message.answer(
        f"✅ <b>ОПЛАЧЕНО!</b>\n\n"
        f"⭐ Сумма: {amount_stars} Telegram Stars\n"
        f"🎮 Игра: {game_name}\n"
        f"💰 Статус: <b>Пополнение выполняется</b>\n\n"
        f"🔜 В течение 1-2 минут баланс будет зачислен.\n"
        f"Спасибо за покупку, бро! 💪",
        reply_markup=get_back_to_main()
    )
    
    logging.info(f"STARS PAYMENT: User {message.from_user.id} | Game: {game_id} | Stars: {amount_stars}")

# ============================================
# ОБРАБОТЧИКИ НАВИГАЦИИ
# ============================================

@dp.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    await callback.message.answer(
        "🏠 <b>Главное меню</b>\n\n"
        "👇 Выбери действие:",
        reply_markup=get_main_menu()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "back_to_games")
async def back_to_games(callback: CallbackQuery):
    await callback.message.edit_text(
        "🎮 <b>Выбери игру:</b>",
        reply_markup=get_games_inline()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "to_games")
async def to_games(callback: CallbackQuery):
    await callback.message.answer(
        "🎮 <b>Выбери игру:</b>",
        reply_markup=get_games_inline()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith('back_to_amounts_'))
async def back_to_amounts(callback: CallbackQuery):
    game_id = callback.data.replace('back_to_amounts_', '')
    game_name = GAMES.get(game_id, {}).get('name', "Неизвестная игра")
    
    await callback.message.edit_text(
        f"🎮 <b>Игра:</b> {game_name}\n"
        f"💰 <b>Выбери сумму в ⭐ Stars:</b>",
        reply_markup=get_amounts_inline(game_id)
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith('back_to_payment_'))
async def back_to_payment(callback: CallbackQuery):
    parts = callback.data.split('_')
    game_id = parts[3]
    amount = int(parts[4])
    game_name = GAMES.get(game_id, {}).get('name', "Неизвестная игра")
    
    rub_amount = amount * STARS_TO_RUB
    
    await callback.message.edit_text(
        f"🎮 <b>Игра:</b> {game_name}\n"
        f"💰 <b>Сумма:</b> {amount} ⭐ (~{rub_amount:.0f} руб)\n\n"
        f"👇 <b>Выбери способ оплаты:</b>",
        reply_markup=get_payment_methods_inline(game_id, amount)
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "my_referrals")
async def my_referrals(callback: CallbackQuery):
    referrals = db.get_referrals(callback.from_user.id)
    
    if not referrals:
        await callback.message.answer(
            "👥 У тебя пока нет рефералов.\n"
            "Поделись ссылкой и получай бонусы!",
            reply_markup=get_back_to_main()
        )
        await callback.answer()
        return
    
    text = "👥 <b>Твои рефералы:</b>\n\n"
    for ref in referrals[:10]:
        text += f"• {ref.get('first_name', 'Аноним')}"
        if ref.get('username'):
            text += f" (@{ref['username']})"
        text += f" - {ref.get('total_spent_stars', 0)} ⭐\n"
    
    if len(referrals) > 10:
        text += f"\n...и еще {len(referrals) - 10}"
    
    await callback.message.answer(text, reply_markup=get_back_to_main())
    await callback.answer()

# ============================================
# АДМИН-КОМАНДЫ
# ============================================

@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Доступ запрещен")
        return
    
    await message.answer(
        "👑 <b>Админ панель</b>\n\n"
        "Выбери раздел:",
        reply_markup=get_admin_inline()
    )

@dp.callback_query(lambda c: c.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    
    games_stats = db.get_game_stats()
    recent = db.get_recent_payments(10)
    daily = db.get_daily_stats(7)
    
    text = "👑 <b>Админ панель - Статистика</b>\n\n"
    
    # Общая статистика
    total_stars = sum(g['total_stars'] for g in games_stats) if games_stats else 0
    total_payments = sum(g['total_payments'] for g in games_stats) if games_stats else 0
    
    text += f"💰 Всего звезд: {total_stars} ⭐\n"
    text += f"🛒 Всего покупок: {total_payments}\n\n"
    
    # Статистика по дням
    text += "<b>За последние 7 дней:</b>\n"
    for day in daily:
        text += f"• {day['date']}: {day['payments']} покупок | {day['stars']} ⭐\n"
    
    text += "\n<b>По играм:</b>\n"
    for game in games_stats:
        text += f"• {game['game_name']}: {game['total_payments']} покупок | {game['total_stars']} ⭐\n"
    
    text += "\n<b>Последние 10 платежей:</b>\n"
    for p in recent:
        name = p.get('first_name', 'Unknown')
        text += f"• {p['game_name']}: {p['amount_stars']} ⭐ ({name})\n"
    
    await callback.message.answer(text, reply_markup=get_admin_inline())
    await callback.answer()

# ============================================
# ЗАПУСК БОТА
# ============================================

async def main():
    logging.info("Бот запускается...")
    
    try:
        me = await bot.get_me()
        logging.info(f"Бот @{me.username} успешно запущен!")
        print(f"\n✅ Бот @{me.username} запущен и готов к работе!")
        print("📱 Открой Telegram и напиши /start")
        print("👑 Админ-панель: /admin\n")
    except Exception as e:
        logging.error(f"Ошибка подключения: {e}")
        print(f"\n❌ Ошибка: {e}")
        print("🔌 Проверь интернет и VPN\n")
        return
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
