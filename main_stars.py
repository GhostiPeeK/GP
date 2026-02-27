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

# Класс для CryptoBot (если нет файла crypto_bot.py)
class CryptoBot:
    def __init__(self, api_key, api_secret=None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://pay.crypt.bot/api"
        self.pending_payments = {}
    
    async def create_invoice(self, amount, currency, description, user_id, game_id):
        """Создает счет в криптовалюте"""
        import aiohttp
        
        url = f"{self.base_url}/createInvoice"
        
        headers = {
            "Crypto-Pay-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        invoice_id = str(uuid.uuid4())[:8]
        
        data = {
            "asset": currency,
            "amount": str(amount),
            "description": description,
            "paid_btn_name": "openBot",
            "paid_btn_url": "https://t.me/GhostiPeeKPaY_bot",
            "expires_in": 3600
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as resp:
                    result = await resp.json()
                    
                    if result.get("ok"):
                        invoice = result["result"]
                        self.pending_payments[invoice["invoice_id"]] = {
                            "user_id": user_id,
                            "game_id": game_id,
                            "amount_crypto": float(amount),
                            "currency": currency,
                            "stars_amount": amount * 10,
                            "created_at": datetime.now(),
                            "status": "pending"
                        }
                        return invoice
                    else:
                        logging.error(f"CryptoBot error: {result}")
                        return None
        except Exception as e:
            logging.error(f"CryptoBot exception: {e}")
            return None
    
    async def check_payment(self, invoice_id):
        """Проверяет статус оплаты"""
        import aiohttp
        
        url = f"{self.base_url}/getInvoices"
        
        headers = {
            "Crypto-Pay-API-Key": self.api_key
        }
        
        params = {
            "invoice_ids": invoice_id
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as resp:
                    result = await resp.json()
                    
                    if result.get("ok") and result["result"]["items"]:
                        invoice = result["result"]["items"][0]
                        return invoice
        except Exception as e:
            logging.error(f"Check payment error: {e}")
        
        return None

# Инициализация CryptoBot
if CRYPTO_ENABLED:
    crypto_bot = CryptoBot(CRYPTO_API_KEY, CRYPTO_API_SECRET)
else:
    crypto_bot = None

# Хранилище пользователей
users = {}

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user = message.from_user
    
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
    parts = callback.data.split('_')
    game_id = parts[1]
    amount_stars = int(parts[2])
    
    user_id = callback.from_user.id
    game_name = GAMES.get(game_id, "Неизвестная игра")
    
    if user_id not in users:
        users[user_id] = {}
    users[user_id]['game'] = game_id
    users[user_id]['game_name'] = game_name
    users[user_id]['amount'] = amount_stars
    
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

# Обработчик для Stars
@dp.callback_query(lambda c: c.data.startswith('pay_stars_'))
async def pay_with_stars(callback: CallbackQuery):
    """Оплата Telegram Stars"""
    parts = callback.data.split('_')
    game_id = parts[2]
    amount_stars = int(parts[3])
    user_id = callback.from_user.id
    game_name = GAMES.get(game_id, "Неизвестная игра")
    
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

# Обработчик для крипты
@dp.callback_query(lambda c: c.data.startswith('pay_crypto_'))
async def pay_with_crypto(callback: CallbackQuery):
    """Оплата криптовалютой"""
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
    
    rub_amount = amount_stars * STARS_TO_RUB
    
    rates = {
        'USDT': rub_amount / 90,  # 1 USDT ≈ 90 руб
        'TON': rub_amount / 450,   # 1 TON ≈ 450 руб
        'BTC': rub_amount / 5400000  # 1 BTC ≈ 5400000 руб
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
        
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
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
        if user_id in users and 'crypto_invoice' in users[user_id]:
            game_id = users[user_id]['game']
            game_name = users[user_id]['game_name']
            amount_stars = users[user_id]['stars_amount']
            currency = users[user_id]['crypto_currency']
            crypto_amount = users[user_id]['crypto_amount']
            
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

# Обработчик для карт (заготовка)
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

# Обработчики навигации
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
    await callback.message.answer(
        "📊 <b>История покупок</b>\n\n"
        "🚀 Функция в разработке!",
        reply_markup=get_back_to_main()
    )
    await callback.answer()

# Обработчики предпроверки платежей
@dp.pre_checkout_query()
async def on_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    """Обязательный обработчик предпроверки"""
    await pre_checkout_query.answer(ok=True)

@dp.message(lambda message: message.successful_payment is not None)
async def on_successful_payment(message: Message):
    """Обработчик успешного платежа Stars"""
    payment = message.successful_payment
    amount_stars = payment.total_amount
    payload = payment.invoice_payload
    charge_id = payment.telegram_payment_charge_id
    
    parts = payload.split('_')
    game_id = parts[1] if len(parts) > 1 else "unknown"
    game_name = GAMES.get(game_id, 'Неизвестная игра')
    
    db.add_payment(
        user_id=message.from_user.id,
        game_id=game_id,
        game_name=game_name,
        amount_stars=amount_stars,
        amount_real=amount_stars,
        currency="XTR",
        payment_method="stars",
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
    
    logging.info(f"STARS PAYMENT: User {message.from_user.id} | Game: {game_id} | Stars: {amount_stars}")

# Админские команды
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

@dp.callback_query(lambda c: c.data == "admin_payments")
async def admin_payments(callback: CallbackQuery):
    """Все платежи"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    
    await callback.message.answer(
        "💳 <b>Все платежи</b>\n\n"
        "🚀 Функция в разработке!\n"
        "Скоро можно будет смотреть все транзакции.",
        reply_markup=get_admin_inline()
    )
    await callback.answer()

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
        print(f"\n✅ Бот @{me.username} запущен и готов к работе!")
        print("📱 Открой Telegram и напиши /start\n")
    except Exception as e:
        logging.error(f"Ошибка подключения: {e}")
        print(f"\n❌ Ошибка: {e}")
        print("🔌 Проверь интернет и VPN\n")
        return
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
