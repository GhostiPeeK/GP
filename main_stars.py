import logging
import asyncio
import uuid
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery, LabeledPrice,
    PreCheckoutQuery
)
from aiogram.client.bot import DefaultBotProperties
from config import (
    BOT_TOKEN, ADMIN_ID, GAMES, PAYMENT_AMOUNTS,
    STARS_ENABLED, STARS_TO_RUB,
    CRYPTO_ENABLED, CRYPTO_API_KEY, CRYPTO_API_SECRET, CRYPTO_CURRENCIES
)
from database import db
from crypto_bot import CryptoBot, crypto_bot
from keyboards import (
    get_main_menu, get_games_inline, get_amounts_inline,
    get_payment_methods_inline, get_crypto_currencies_inline,
    get_profile_inline, get_admin_inline, get_back_to_main
)

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# Инициализация CryptoBot
if CRYPTO_ENABLED:
    crypto_bot = CryptoBot(CRYPTO_API_KEY, CRYPTO_API_SECRET)

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
        f"💎 Доступные способы оплаты:\n"
        f"⭐ Telegram Stars\n"
        f"₿ Криптовалюта (USDT, TON, BTC)\n\n"
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
        "3. Выбери сумму в ⭐ Stars\n"
        "4. Выбери способ оплаты\n"
        "5. Оплати и получи пополнение\n\n"
        "💎 <b>Способы оплаты:</b>\n"
        "⭐ Telegram Stars - быстро и удобно\n"
        "₿ Криптовалюта - USDT, TON, BTC\n\n"
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
        f"💰 <b>Выбери сумму в ⭐ Stars:</b>",
        reply_markup=get_amounts_inline(game_id)
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith('amount_'))
async def process_amount(callback: CallbackQuery):
    """Выбор суммы"""
    # Формат: amount_GAMEID_AMOUNT
    parts = callback.data.split('_')
    game_id = parts[1]
    amount_stars = int(parts[2])
    
    user_id = callback.from_user.id
    game_name = GAMES.get(game_id, "Неизвестная игра")
    
    # Сохраняем данные
    if user_id not in users:
        users[user_id] = {}
    users[user_id]['game'] = game_id
    users[user_id]['game_name'] = game_name
    users[user_id]['amount'] = amount_stars
    
    # Конвертируем в рубли для информации
    rub_amount = amount_stars * STARS_TO_RUB
    
    await callback.message.edit_text(
        f"🎮 <b>Игра:</b> {game_name}\n"
        f"💰 <b>Сумма:</b> {amount_stars} ⭐ (~{rub_amount:.0f} руб)\n\n"
        f"👇 <b>Выбери способ оплаты:</b>",
        reply_markup=get_payment_methods_inline(game_id, amount_stars)
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith('back_to_amounts_'))
async def back_to_amounts(callback: CallbackQuery):
    """Возврат к выбору суммы"""
    game_id = callback.data.replace('back_to_amounts_', '')
    game_name = GAMES.get(game_id, "Неизвестная игра")
    
    await callback.message.edit_text(
        f"🎮 <b>Игра:</b> {game_name}\n"
        f"💰 <b>Выбери сумму в ⭐ Stars:</b>",
        reply_markup=get_amounts_inline(game_id)
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith('back_to_payment_'))
async def back_to_payment(callback: CallbackQuery):
    """Возврат к выбору способа оплаты"""
    # Формат: back_to_payment_GAMEID_AMOUNT
    parts = callback.data.split('_')
    game_id = parts[3]
    amount = int(parts[4])
    game_name = GAMES.get(game_id, "Неизвестная игра")
    
    rub_amount = amount * STARS_TO_RUB
    
    await callback.message.edit_text(
        f"🎮 <b>Игра:</b> {game_name}\n"
        f"💰 <b>Сумма:</b> {amount} ⭐ (~{rub_amount:.0f} руб)\n\n"
        f"👇 <b>Выбери способ оплаты:</b>",
        reply_markup=get_payment_methods_inline(game_id, amount)
    )
    await callback.answer()

# ============================================
# ОБРАБОТЧИКИ ОПЛАТЫ
# ============================================

# 1. Telegram Stars (уже работает)
@dp.callback_query(lambda c: c.data.startswith('pay_stars_'))
async def pay_with_stars(callback: CallbackQuery):
    """Оплата Telegram Stars"""
    # Формат: pay_stars_GAMEID_AMOUNT
    parts = callback.data.split('_')
    game_id = parts[2]
    amount_stars = int(parts[3])
    user_id = callback.from_user.id
    game_name = GAMES.get(game_id, "Неизвестная игра")
    
    # Создаем счет в Stars
    prices = [LabeledPrice(label=f"Пополнение {game_name}", amount=amount_stars)]
    
    await callback.message.answer_invoice(
        title=f"Пополнение {game_name}",
        description=f"Оплата {amount_stars} ⭐ Telegram Stars",
        payload=f"stars_{game_id}_{amount_stars}_{user_id}",
        provider_token="",  # Пусто для Stars
        currency="XTR",
        prices=prices,
        start_parameter="game_payment"
    )
    await callback.answer()

# 2. Криптовалюта
@dp.callback_query(lambda c: c.data.startswith('pay_crypto_'))
async def pay_with_crypto(callback: CallbackQuery):
    """Оплата криптовалютой"""
    # Формат: pay_crypto_GAMEID_AMOUNT
    parts = callback.data.split('_')
    game_id = parts[2]
    amount_stars = int(parts[3])
    game_name = GAMES.get(game_id, "Неизвестная игра")
    
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
    """Выбор криптовалюты и создание счета"""
    # Формат: crypto_CURRENCY_GAMEID_AMOUNT
    parts = callback.data.split('_')
    currency = parts[1]
    game_id = parts[2]
    amount_stars = int(parts[3])
    user_id = callback.from_user.id
    game_name = GAMES.get(game_id, "Неизвестная игра")
    
    if not crypto_bot:
        await callback.message.edit_text(
            "❌ Криптоплатежи временно недоступны",
            reply_markup=get_back_to_main()
        )
        await callback.answer()
        return
    
    # Конвертируем в крипту (упрощенно)
    rub_amount = amount_stars * STARS_TO_RUB
    
    # Примерные курсы (в реальности нужно через API)
    rates = {
        'USDT': rub_amount,  # 1 USDT = 1 USD ≈ 90 руб
        'TON': rub_amount / 5,  # 1 TON ≈ 5 USD
        'BTC': rub_amount / 60000  # 1 BTC ≈ 60000 USD
    }
    
    crypto_amount = round(rates.get(currency, rub_amount), 6)
    
    # Создаем счет в CryptoBot
    description = f"{game_name} - {amount_stars}⭐"
    invoice = await crypto_bot.create_invoice(
        amount=crypto_amount,
        currency=currency,
        description=description,
        user_id=user_id,
        game_id=game_id
    )
    
    if invoice and invoice.get("pay_url"):
        # Сохраняем в users для проверки
        users[user_id]['crypto_invoice'] = invoice["invoice_id"]
        users[user_id]['crypto_currency'] = currency
        users[user_id]['crypto_amount'] = crypto_amount
        users[user_id]['stars_amount'] = amount_stars
        
        # Отправляем ссылку на оплату
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить", url=invoice["pay_url"])],
            [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"check_crypto_{invoice['invoice_id']}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data=f"back_to_payment_{game_id}_{amount_stars}")]
        ])
        
        await callback.message.edit_text(
            f"₿ <b>Счет на оплату</b>\n\n"
            f"🎮 Игра: {game_name}\n"
            f"💰 Сумма: {amount_stars} ⭐\n"
            f"💎 Криптовалюта: {currency}\n"
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

@dp.callback_query(lambda c: c.data.startswith('check_crypto_'))
async def check_crypto_payment(callback: CallbackQuery):
    """Проверка оплаты криптовалюты"""
    invoice_id = callback.data.replace('check_crypto_', '')
    user_id = callback.from_user.id
    
    if not crypto_bot:
        await callback.answer("❌ Сервис недоступен", show_alert=True)
        return
    
    invoice = await crypto_bot.check_payment(invoice_id)
    
    if invoice and invoice.get("status") == "paid":
        # Платеж прошел!
        if user_id in users and 'crypto_invoice' in users[user_id]:
            game_id = users[user_id]['game']
            game_name = users[user_id]['game_name']
            amount_stars = users[user_id]['stars_amount']
            currency = users[user_id]['crypto_currency']
            crypto_amount = users[user_id]['crypto_amount']
            
            # Сохраняем в БД
            db.add_payment(
                user_id=user_id,
                game_id=game_id,
                game_name=game_name,
                amount_stars=amount_stars,
                amount_real=crypto_amount,
                currency=currency,
                payment_method="crypto",
                charge_id=f"crypto_{invoice_id}"
            )
            
            await callback.message.edit_text(
                f"✅ <b>ОПЛАЧЕНО!</b>\n\n"
                f"⭐ Сумма: {amount_stars} Stars\n"
                f"₿ Оплачено: {crypto_amount} {currency}\n"
                f"🎮 Игра: {game_name}\n\n"
                f"🔜 В течение 1-2 минут баланс будет зачислен.\n"
                f"Спасибо за покупку, бро! 💪",
                reply_markup=get_back_to_main()
            )
            
            logging.info(f"CRYPTO PAYMENT: User={user_id}, Game={game_id}, Stars={amount_stars}")
    else:
        await callback.answer("⏳ Платеж еще не найден. Нажми через минуту.", show_alert=True)
    
    await callback.answer()

# 3. Банковские карты (заготовка)
@dp.callback_query(lambda c: c.data.startswith('pay_card_'))
async def pay_with_card(callback: CallbackQuery):
    """Оплата банковской картой (в разработке)"""
    parts = callback.data.split('_')
    game_id = parts[2]
    amount_stars = int(parts[3])
    game_name = GAMES.get(game_id, "Неизвестная игра")
    
    rub_amount = amount_stars * STARS_TO_RUB
    
    await callback.message.edit_text(
        f"💳 <b>Оплата банковской картой</b>\n\n"
        f"🎮 Игра: {game_name}\n"
        f"💰 Сумма: {amount_stars} ⭐\n"
        f"💵 К оплате: {rub_amount:.0f} RUB\n\n"
        f"🚀 Функция в разработке!\n"
        f"Скоро можно будет платить картой.\n\n"
        f"Пока воспользуйся Stars или криптовалютой.",
        reply_markup=get_back_to_main()
    )
    await callback.answer()

# ============================================
# СТАНДАРТНЫЕ ОБРАБОТЧИК
