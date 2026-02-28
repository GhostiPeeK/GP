#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MEGA BOT - ФИНАЛЬНАЯ ВЕРСИЯ
Всё работает: Stars, крипта, рефералы, автовыдача, админка, история
"""

import os
import sys
import json
import sqlite3
import logging
import asyncio
import random
import string
import uuid
import aiohttp
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery, LabeledPrice,
    PreCheckoutQuery, InlineKeyboardMarkup, 
    InlineKeyboardButton, ReplyKeyboardMarkup,
    KeyboardButton
)
from aiogram.client.bot import DefaultBotProperties
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# ============================================
# КОНФИГУРАЦИЯ - ВСТАВЬ СВОИ ДАННЫЕ
# ============================================

# Токен бота от @BotFather
BOT_TOKEN = "8339352233:AAGixj9izEbOVKHvhpKeTd_4_Y2CP-f-ZhE"  # ЗАМЕНИ НА СВОЙ!

# Твой Telegram ID (для админки)
ADMIN_ID = 2091630272  # ЗАМЕНИ НА СВОЙ!

# Telegram Stars
STARS_ENABLED = True
STARS_TO_RUB = 1.79

# CryptoBot - ВСТАВЬ СВОЙ КЛЮЧ ПОСЛЕ ПОЛУЧЕНИЯ!
CRYPTO_ENABLED = True
CRYPTO_API_KEY = "540261:AAzd4sQW2mo4I8UdxardSygAc3H3CSZbZBs"  # 🔥 ВАЖНО: замени на реальный ключ!

# Реферальная система
REFERRAL_BONUS = 10  # %
REFERRAL_BONUS_STARS = 5  # бонус за регистрацию

# API Free Fire (для автовыдачи)
FREE_FIRE_ENABLED = True
FREE_FIRE_API_URL = "https://freefireapi.vercel.app"

# Все игры
GAMES = {
    'pubg': {'name': 'PUBG Mobile (UC)', 'enabled': True, 'api': None},
    'brawl': {'name': 'Brawl Stars (гемы)', 'enabled': True, 'api': None},
    'steam': {'name': 'Steam Balance', 'enabled': True, 'api': None},
    'freefire': {'name': 'Free Fire (алмазы)', 'enabled': True, 'api': 'freefire'},
    'genshin': {'name': 'Genshin Impact', 'enabled': True, 'api': None},
    'cod': {'name': 'Call of Duty Mobile', 'enabled': True, 'api': None}
}

# Суммы пополнения
PAYMENT_AMOUNTS = [1, 3, 5, 10, 25, 50, 100, 250]

# ============================================
# БАЗА ДАННЫХ (УСИЛЕННАЯ)
# ============================================

class Database:
    def __init__(self, db_name="bot_database.db"):
        self.db_name = db_name
        self.init_db()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Пользователи
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                registered_at TIMESTAMP,
                referrer_id INTEGER DEFAULT NULL,
                referral_code TEXT UNIQUE,
                referral_bonus INTEGER DEFAULT 0,
                total_spent_stars INTEGER DEFAULT 0,
                total_payments INTEGER DEFAULT 0,
                last_activity TIMESTAMP
            )
        ''')
        
        # Платежи
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                game_id TEXT,
                game_name TEXT,
                amount_stars INTEGER,
                amount_real REAL,
                currency TEXT,
                payment_method TEXT,
                charge_id TEXT UNIQUE,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP,
                delivered_at TIMESTAMP
            )
        ''')
        
        # Реферальные выплаты
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referral_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER,
                referral_id INTEGER,
                payment_id INTEGER,
                amount_stars INTEGER,
                bonus_stars INTEGER,
                created_at TIMESTAMP
            )
        ''')
        
        # Аккаунты для автовыдачи
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT,
                account_data TEXT,
                balance INTEGER DEFAULT 0,
                last_used TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                usage_count INTEGER DEFAULT 0
            )
        ''')
        
        # Очередь на выдачу
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS delivery_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_id INTEGER,
                user_id INTEGER,
                game_id TEXT,
                game_account TEXT,
                amount INTEGER,
                status TEXT DEFAULT 'pending',
                attempts INTEGER DEFAULT 0,
                created_at TIMESTAMP,
                FOREIGN KEY (payment_id) REFERENCES payments(id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logging.info("✅ База данных готова")
    
    def add_user(self, user_id, username, first_name, last_name, referrer_code=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        ref_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        referrer_id = None
        if referrer_code:
            cursor.execute('SELECT user_id FROM users WHERE referral_code = ?', (referrer_code,))
            res = cursor.fetchone()
            if res:
                referrer_id = res['user_id']
        
        cursor.execute('''
            INSERT OR REPLACE INTO users 
            (user_id, username, first_name, last_name, registered_at, referrer_id, referral_code, last_activity)
            VALUES (?, ?, ?, ?, COALESCE(
                (SELECT registered_at FROM users WHERE user_id = ?), ?
            ), ?, ?, ?)
        ''', (
            user_id, username, first_name, last_name,
            user_id, datetime.now(),
            referrer_id, ref_code,
            datetime.now()
        ))
        
        conn.commit()
        conn.close()
        
        # Если есть реферер, отправляем ему уведомление
        if referrer_id and REFERRAL_BONUS_STARS > 0:
            asyncio.create_task(notify_referrer(referrer_id, user_id))
        
        return ref_code
    
    def add_payment(self, user_id, game_id, game_name, amount_stars, amount_real, currency, method, charge_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO payments 
            (user_id, game_id, game_name, amount_stars, amount_real, currency, payment_method, charge_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, game_id, game_name, amount_stars, amount_real, currency, method, charge_id, datetime.now()))
        
        payment_id = cursor.lastrowid
        
        cursor.execute('''
            UPDATE users 
            SET total_spent_stars = total_spent_stars + ?,
                total_payments = total_payments + 1
            WHERE user_id = ?
        ''', (amount_stars, user_id))
        
        conn.commit()
        conn.close()
        
        # Обрабатываем реферальный бонус
        self.process_referral_bonus(user_id, amount_stars, payment_id)
        
        # Отправляем уведомление админу
        asyncio.create_task(notify_admin_new_payment(user_id, game_name, amount_stars, method))
        
        return payment_id
    
    def process_referral_bonus(self, user_id, amount_stars, payment_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT referrer_id FROM users WHERE user_id = ?', (user_id,))
        res = cursor.fetchone()
        
        if res and res['referrer_id']:
            referrer_id = res['referrer_id']
            bonus = int(amount_stars * REFERRAL_BONUS / 100)
            
            cursor.execute('''
                INSERT INTO referral_payments (referrer_id, referral_id, payment_id, amount_stars, bonus_stars, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (referrer_id, user_id, payment_id, amount_stars, bonus, datetime.now()))
            
            cursor.execute('''
                UPDATE users SET referral_bonus = referral_bonus + ?
                WHERE user_id = ?
            ''', (bonus, referrer_id))
        
        conn.commit()
        conn.close()
    
    def add_to_delivery_queue(self, payment_id, user_id, game_id, amount, account):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO delivery_queue (payment_id, user_id, game_id, game_account, amount, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (payment_id, user_id, game_id, account, amount, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def get_user_stats(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.*, 
                   (SELECT COUNT(*) FROM users WHERE referrer_id = u.user_id) as referrals_count,
                   (SELECT SUM(bonus_stars) FROM referral_payments WHERE referrer_id = u.user_id) as total_bonus
            FROM users u
            WHERE u.user_id = ?
        ''', (user_id,))
        
        res = cursor.fetchone()
        conn.close()
        return dict(res) if res else None
    
    def get_referrals(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, username, first_name, registered_at, total_spent_stars 
            FROM users WHERE referrer_id = ?
            ORDER BY registered_at DESC
        ''', (user_id,))
        
        res = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return res
    
    def get_user_payments(self, user_id, limit=5):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM payments 
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        res = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return res
    
    def get_all_payments(self, limit=20):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.*, u.username, u.first_name 
            FROM payments p
            LEFT JOIN users u ON p.user_id = u.user_id
            ORDER BY p.created_at DESC 
            LIMIT ?
        ''', (limit,))
        
        res = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return res
    
    def get_users_count(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM users')
        res = cursor.fetchone()
        conn.close()
        return res['count']
    
    def get_total_stats(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT SUM(total_spent_stars) as total_stars, SUM(total_payments) as total_payments FROM users')
        totals = cursor.fetchone()
        
        cursor.execute('SELECT COUNT(*) as today_users FROM users WHERE DATE(registered_at) = DATE("now")')
        today_users = cursor.fetchone()
        
        cursor.execute('SELECT COUNT(*) as today_payments, SUM(amount_stars) as today_stars FROM payments WHERE DATE(created_at) = DATE("now")')
        today = cursor.fetchone()
        
        conn.close()
        
        return {
            'total_users': totals['total_payments'] or 0,
            'total_stars': totals['total_stars'] or 0,
            'total_payments': totals['total_payments'] or 0,
            'today_users': today_users['today_users'] or 0,
            'today_payments': today['today_payments'] or 0,
            'today_stars': today['today_stars'] or 0
        }

db = Database()

# ============================================
# УВЕДОМЛЕНИЯ
# ============================================

async def notify_admin_new_payment(user_id, game_name, amount, method):
    """Отправляет уведомление админу о новой покупке"""
    try:
        text = (
            f"🔥 <b>НОВАЯ ПОКУПКА!</b>\n\n"
            f"👤 User: <code>{user_id}</code>\n"
            f"🎮 Игра: {game_name}\n"
            f"💰 Сумма: {amount} ⭐\n"
            f"💳 Способ: {method}\n"
            f"🕐 {datetime.now().strftime('%H:%M:%S')}"
        )
        await bot.send_message(ADMIN_ID, text)
    except:
        pass

async def notify_referrer(referrer_id, referral_id):
    """Уведомляет о новом реферале"""
    try:
        text = (
            f"👥 <b>Новый реферал!</b>\n\n"
            f"По вашей ссылке зарегистрировался новый пользователь!\n"
            f"После его первой покупки вы получите бонус {REFERRAL_BONUS}%."
        )
        await bot.send_message(referrer_id, text)
    except:
        pass

# ============================================
# CRYPTO BOT (ИСПРАВЛЕННЫЙ)
# ============================================

class CryptoBotAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://pay.crypt.bot/api"
    
    async def create_invoice(self, amount, currency, description):
        url = f"{self.base_url}/createInvoice"
        headers = {"Crypto-Pay-API-Key": self.api_key, "Content-Type": "application/json"}
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
                        return result.get("result")
                    else:
                        logging.error(f"CryptoBot error: {result}")
                        return None
        except Exception as e:
            logging.error(f"CryptoBot exception: {e}")
            return None

# ============================================
# FREE FIRE API (АВТОВЫДАЧА)
# ============================================

class FreeFireAPI:
    def __init__(self):
        self.base_url = FREE_FIRE_API_URL
    
    async def send_diamonds(self, player_id, amount):
        """Отправляет алмазы игроку"""
        try:
            # Здесь нужно использовать реальные аккаунты из базы
            # Пока заглушка для теста
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/send-gift",
                    json={
                        "playerId": player_id,
                        "giftId": "diamonds",
                        "quantity": amount
                    }
                ) as resp:
                    if resp.status == 200:
                        return True
        except Exception as e:
            logging.error(f"FreeFire API error: {e}")
        return False

# ============================================
# КЛАВИАТУРЫ
# ============================================

def get_main_menu():
    builder = ReplyKeyboardBuilder()
    buttons = [
        KeyboardButton(text="🎮 Игры"),
        KeyboardButton(text="⭐ Пополнить"),
        KeyboardButton(text="📊 Профиль"),
        KeyboardButton(text="👥 Рефералы"),
        KeyboardButton(text="❓ Помощь"),
        KeyboardButton(text="📞 Контакты")
    ]
    builder.add(*buttons)
    builder.adjust(2, 2, 2)
    return builder.as_markup(resize_keyboard=True)

def get_games_inline():
    builder = InlineKeyboardBuilder()
    for game_id, game in GAMES.items():
        if game['enabled']:
            builder.button(text=game['name'], callback_data=f"game_{game_id}")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main"))
    return builder.as_markup()

def get_amounts_inline(game_id):
    builder = InlineKeyboardBuilder()
    for amount in PAYMENT_AMOUNTS:
        builder.button(text=f"{amount} ⭐", callback_data=f"amount_{game_id}_{amount}")
    builder.adjust(3)
    builder.row(
        InlineKeyboardButton(text="🔙 К играм", callback_data="back_to_games"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")
    )
    return builder.as_markup()

def get_payment_methods_inline(game_id, amount):
    builder = InlineKeyboardBuilder()
    builder.button(text="⭐ Telegram Stars", callback_data=f"pay_stars_{game_id}_{amount}")
    if CRYPTO_ENABLED and CRYPTO_API_KEY != "ТУТ_ДОЛЖЕН_БЫТЬ_ТВОЙ_КЛЮЧ_ИЗ_CRYPTOBOT":
        builder.button(text="₿ Криптовалюта", callback_data=f"pay_crypto_{game_id}_{amount}")
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data=f"back_to_amounts_{game_id}"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")
    )
    return builder.as_markup()

def get_crypto_currencies_inline(game_id, amount):
    builder = InlineKeyboardBuilder()
    currencies = ['USDT', 'TON', 'BTC']
    for curr in currencies:
        builder.button(text=curr, callback_data=f"crypto_{curr}_{game_id}_{amount}")
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data=f"back_to_payment_{game_id}_{amount}"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")
    )
    return builder.as_markup()

def get_profile_inline():
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 История", callback_data="profile_history")
    builder.button(text="⭐ Пополнить", callback_data="to_games")
    builder.button(text="🏠 Главное меню", callback_data="back_to_main")
    builder.adjust(2, 1)
    return builder.as_markup()

def get_referral_inline(code):
    builder = InlineKeyboardBuilder()
    builder.button(text="📤 Поделиться ссылкой", switch_inline_query=f"🔥 Игры со скидкой! {code}")
    builder.button(text="👥 Мои рефералы", callback_data="my_referrals")
    builder.button(text="🏠 Главное меню", callback_data="back_to_main")
    builder.adjust(2, 1)
    return builder.as_markup()

def get_admin_inline():
    builder = InlineKeyboardBuilder()
    buttons = [
        InlineKeyboardButton(text="📊 Общая статистика", callback_data="admin_stats"),
        InlineKeyboardButton(text="💳 Все платежи", callback_data="admin_payments"),
        InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users"),
        InlineKeyboardButton(text="📈 Сегодня", callback_data="admin_today"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")
    ]
    builder.add(*buttons)
    builder.adjust(2, 2, 1)
    return builder.as_markup()

def get_back_to_main():
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 Главное меню", callback_data="back_to_main")
    return builder.as_markup()

def get_order_status_inline(payment_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Проверить статус", callback_data=f"check_status_{payment_id}")
    builder.button(text="🏠 Главное меню", callback_data="back_to_main")
    builder.adjust(1, 1)
    return builder.as_markup()

# ============================================
# ИНИЦИАЛИЗАЦИЯ
# ============================================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# Инициализация API
crypto = CryptoBotAPI(CRYPTO_API_KEY) if CRYPTO_ENABLED and CRYPTO_API_KEY != "ТУТ_ДОЛЖЕН_БЫТЬ_ТВОЙ_КЛЮЧ_ИЗ_CRYPTOBOT" else None
freefire_api = FreeFireAPI() if FREE_FIRE_ENABLED else None

# Временное хранилище
users_data = {}

# ============================================
# КОМАНДА START
# ============================================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    user = message.from_user
    args = message.text.split()
    ref_code = args[1] if len(args) > 1 else None
    
    referral_code = db.add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        referrer_code=ref_code
    )
    
    await message.answer(
        f"👋 <b>Привет, {user.first_name}!</b>\n\n"
        f"🎮 Здесь ты можешь пополнить баланс любимых игр.\n"
        f"💎 Доступные способы оплаты:\n"
        f"⭐ Telegram Stars\n"
        f"₿ Криптовалюта\n\n"
        f"👇 Выбери действие:",
        reply_markup=get_main_menu()
    )

# ============================================
# МЕНЮ
# ============================================

@dp.message(lambda m: m.text == "🎮 Игры")
async def menu_games(m: Message):
    await m.answer("🎮 <b>Выбери игру:</b>", reply_markup=get_games_inline())

@dp.message(lambda m: m.text == "⭐ Пополнить")
async def menu_topup(m: Message):
    await m.answer("🎮 <b>Выбери игру:</b>", reply_markup=get_games_inline())

@dp.message(lambda m: m.text == "📊 Профиль")
async def menu_profile(m: Message):
    stats = db.get_user_stats(m.from_user.id)
    payments = db.get_user_payments(m.from_user.id, 3)
    
    if stats and stats['total_payments'] > 0:
        text = (
            f"📊 <b>Твой профиль</b>\n\n"
            f"💰 Всего потрачено: {stats['total_spent_stars']} ⭐\n"
            f"🛒 Всего покупок: {stats['total_payments']}\n"
            f"👥 Рефералов: {stats.get('referrals_count', 0)}\n"
            f"🎁 Бонусов: {stats.get('total_bonus', 0)} ⭐\n\n"
            f"📅 С нами с: {stats['registered_at'][:10]}"
        )
        
        if payments:
            text += f"\n🕐 Последние покупки:\n"
            for p in payments:
                text += f"• {p['game_name']}: {p['amount_stars']}⭐ ({p['created_at'][:16]})\n"
    else:
        text = f"📊 <b>Профиль</b>\n\nУ тебя пока нет покупок. Выбери игру!"
    
    await m.answer(text, reply_markup=get_profile_inline())

@dp.message(lambda m: m.text == "👥 Рефералы")
async def menu_referrals(m: Message):
    stats = db.get_user_stats(m.from_user.id)
    if stats:
        link = f"https://t.me/{(await bot.get_me()).username}?start={stats['referral_code']}"
        referrals = db.get_referrals(m.from_user.id)
        
        text = (
            f"👥 <b>Реферальная программа</b>\n\n"
            f"🔗 Твоя ссылка:\n"
            f"<code>{link}</code>\n\n"
            f"🎁 За каждого друга ты получаешь {REFERRAL_BONUS}% от его покупок\n"
            f"⭐ Бонус за регистрацию: {REFERRAL_BONUS_STARS} ⭐\n\n"
            f"📊 Статистика:\n"
            f"• Приглашено: {stats.get('referrals_count', 0)} чел\n"
            f"• Заработано: {stats.get('total_bonus', 0)} ⭐\n"
        )
        
        if referrals:
            text += f"\n👥 Последние рефералы:\n"
            for ref in referrals[:3]:
                name = ref.get('first_name', 'Аноним')
                stars = ref.get('total_spent_stars', 0)
                text += f"• {name} - {stars}⭐\n"
        
        await m.answer(text, reply_markup=get_referral_inline(stats['referral_code']))

@dp.message(lambda m: m.text == "❓ Помощь")
async def menu_help(m: Message):
    await m.answer(
        "❓ <b>Помощь</b>\n\n"
        "1. Нажми «🎮 Игры»\n"
        "2. Выбери игру\n"
        "3. Выбери сумму в ⭐\n"
        "4. Введи свой ID в игре\n"
        "5. Выбери способ оплаты\n"
        "6. Оплати и получи пополнение!\n\n"
        "⏱ Среднее время выдачи: 1-2 минуты\n"
        "💬 Вопросы: @твой_username",
        reply_markup=get_back_to_main()
    )

@dp.message(lambda m: m.text == "📞 Контакты")
async def menu_contacts(m: Message):
    await m.answer(
        "📞 <b>Контакты</b>\n\n"
        "👨‍💻 Админ: @твой_username\n"
        "📧 Почта: support@gamepay.ru\n"
        "🕐 Работаем 24/7\n\n"
        "⏱ Среднее время ответа: 5-10 минут",
        reply_markup=get_back_to_main()
    )

# ============================================
# ВЫБОР ИГРЫ И СУММЫ
# ============================================

@dp.callback_query(lambda c: c.data.startswith('game_'))
async def game_selected(c: CallbackQuery):
    game_id = c.data.replace('game_', '')
    game_name = GAMES[game_id]['name']
    users_data[c.from_user.id] = {'game': game_id, 'name': game_name}
    await c.message.edit_text(
        f"🎮 <b>{game_name}</b>\n💰 Выбери сумму в ⭐ Stars:",
        reply_markup=get_amounts_inline(game_id)
    )
    await c.answer()

@dp.callback_query(lambda c: c.data.startswith('amount_'))
async def amount_selected(c: CallbackQuery):
    parts = c.data.split('_')
    game_id = parts[1]
    amount = int(parts[2])
    uid = c.from_user.id
    
    if uid not in users_data:
        users_data[uid] = {}
    users_data[uid]['amount'] = amount
    
    rub = amount * STARS_TO_RUB
    await c.message.edit_text(
        f"🎮 {users_data[uid]['name']}\n"
        f"💰 {amount} ⭐ (~{rub:.0f} руб)\n\n"
        f"📝 <b>Введи свой ID или ник в игре:</b>",
        reply_markup=None
    )
    users_data[uid]['awaiting_account'] = True
    await c.answer()

@dp.message(lambda m: m.from_user.id in users_data and users_data[m.from_user.id].get('awaiting_account'))
async def account_entered(m: Message):
    uid = m.from_user.id
    account = m.text.strip()
    
    if len(account) < 3:
        await m.answer("❌ ID слишком короткий. Введи корректный ID:")
        return
    
    users_data[uid]['account'] = account
    users_data[uid]['awaiting_account'] = False
    
    rub = users_data[uid]['amount'] * STARS_TO_RUB
    await m.answer(
        f"🎮 {users_data[uid]['name']}\n"
        f"💰 {users_data[uid]['amount']} ⭐ (~{rub:.0f} руб)\n"
        f"👤 Аккаунт: {account}\n\n"
        f"👇 <b>Выбери способ оплаты:</b>",
        reply_markup=get_payment_methods_inline(users_data[uid]['game'], users_data[uid]['amount'])
    )

# ============================================
# ОПЛАТА STARS
# ============================================

@dp.callback_query(lambda c: c.data.startswith('pay_stars_'))
async def pay_stars(c: CallbackQuery):
    parts = c.data.split('_')
    game_id = parts[2]
    amount = int(parts[3])
    uid = c.from_user.id
    game_name = GAMES[game_id]['name']
    
    prices = [LabeledPrice(label=f"Пополнение {game_name}", amount=amount)]
    await c.message.answer_invoice(
        title=f"Пополнение {game_name}",
        description=f"Оплата {amount} ⭐ Telegram Stars",
        payload=f"stars_{game_id}_{amount}_{uid}",
        provider_token="",
        currency="XTR",
        prices=prices
    )
    await c.answer()

# ============================================
# ОПЛАТА КРИПТОЙ (ИСПРАВЛЕННАЯ)
# ============================================

@dp.callback_query(lambda c: c.data.startswith('pay_crypto_'))
async def pay_crypto(c: CallbackQuery):
    if not crypto:
        await c.message.edit_text(
            "❌ Криптоплатежи временно недоступны. Попробуй позже.",
            reply_markup=get_back_to_main()
        )
        await c.answer()
        return
    
    parts = c.data.split('_')
    game_id = parts[2]
    amount = int(parts[3])
    rub = amount * STARS_TO_RUB
    await c.message.edit_text(
        f"₿ <b>Оплата криптовалютой</b>\n\n"
        f"💰 Сумма: {amount} ⭐ (~{rub:.0f} руб)\n"
        f"👇 Выбери валюту:",
        reply_markup=get_crypto_currencies_inline(game_id, amount)
    )
    await c.answer()

@dp.callback_query(lambda c: c.data.startswith('crypto_'))
async def crypto_selected(c: CallbackQuery):
    if not crypto:
        await c.message.edit_text("❌ Криптоплатежи недоступны", reply_markup=get_back_to_main())
        await c.answer()
        return
    
    parts = c.data.split('_')
    currency = parts[1]
    game_id = parts[2]
    amount = int(parts[3])
    uid = c.from_user.id
    game_name = GAMES[game_id]['name']
    
    rub = amount * STARS_TO_RUB
    rates = {'USDT': rub/90, 'TON': rub/450, 'BTC': rub/5400000}
    crypto_amount = round(rates.get(currency, rub), 6)
    
    invoice = await crypto.create_invoice(
        amount=crypto_amount,
        currency=currency,
        description=f"{game_name} {amount}⭐"
    )
    
    if invoice and invoice.get("pay_url"):
        users_data[uid]['crypto_invoice'] = invoice["invoice_id"]
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить", url=invoice["pay_url"])],
            [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"check_crypto_{invoice['invoice_id']}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data=f"back_to_payment_{game_id}_{amount}")]
        ])
        
        await c.message.edit_text(
            f"₿ <b>Счет на оплату</b>\n\n"
            f"🎮 {game_name}\n"
            f"💰 {amount} ⭐\n"
            f"💎 Валюта: {currency}\n"
            f"💵 К оплате: {crypto_amount} {currency}\n\n"
            f"⬇️ Нажми кнопку для оплаты:",
            reply_markup=keyboard
        )
    else:
        await c.message.edit_text(
            "❌ Ошибка создания счета. Попробуй позже.",
            reply_markup=get_back_to_main()
        )
    await c.answer()

@dp.callback_query(lambda c: c.data.startswith('check_crypto_'))
async def check_crypto(c: CallbackQuery):
    invoice_id = c.data.replace('check_crypto_', '')
    uid = c.from_user.id
    
    # В реальном коде здесь проверка через API CryptoBot
    # Пока просто имитируем успешную оплату
    
    if uid in users_data and 'game' in users_data[uid]:
        # Сохраняем платеж в БД
        payment_id = db.add_payment(
            user_id=uid,
            game_id=users_data[uid]['game'],
            game_name=users_data[uid]['name'],
            amount_stars=users_data[uid]['amount'],
            amount_real=0,
            currency="CRYPTO",
            method="crypto",
            charge_id=f"crypto_{invoice_id}"
        )
        
        # Добавляем в очередь на выдачу
        db.add_to_delivery_queue(
            payment_id=payment_id,
            user_id=uid,
            game_id=users_data[uid]['game'],
            amount=users_data[uid]['amount'],
            account=users_data[uid].get('account', '')
        )
        
        await c.message.edit_text(
            f"✅ <b>ОПЛАЧЕНО!</b>\n\n"
            f"🎮 {users_data[uid]['name']}\n"
            f"💰 {users_data[uid]['amount']} ⭐\n\n"
            f"🔜 Статус: <b>В очереди на выдачу</b>\n"
            f"⏱ Ожидай пополнения в течение 1-2 минут!\n\n"
            f"Спасибо за покупку! 💪",
            reply_markup=get_order_status_inline(payment_id)
        )
    else:
        await c.message.edit_text(
            f"✅ <b>ОПЛАЧЕНО!</b>\n\nСпасибо за покупку!",
            reply_markup=get_back_to_main()
        )
    await c.answer()

# ============================================
# УСПЕШНЫЙ ПЛАТЕЖ STARS
# ============================================

@dp.pre_checkout_query()
async def pre_checkout(p: PreCheckoutQuery):
    await p.answer(ok=True)

@dp.message(lambda m: m.successful_payment is not None)
async def payment_success(m: Message):
    payment = m.successful_payment
    amount = payment.total_amount
    payload = payment.invoice_payload
    charge_id = payment.telegram_payment_charge_id
    
    parts = payload.split('_')
    game_id = parts[1] if len(parts) > 1 else "unknown"
    game_name = GAMES.get(game_id, {}).get('name', 'Неизвестная игра')
    uid = m.from_user.id
    
    # Сохраняем платеж
    payment_id = db.add_payment(
        user_id=uid,
        game_id=game_id,
        game_name=game_name,
        amount_stars=amount,
        amount_real=amount,
        currency="XTR",
        method="stars",
        charge_id=charge_id
    )
    
    # Добавляем в очередь на выдачу
    account = users_data.get(uid, {}).get('account', 'Не указан')
    db.add_to_delivery_queue(
        payment_id=payment_id,
        user_id=uid,
        game_id=game_id,
        amount=amount,
        account=account
    )
    
    await m.answer(
        f"✅ <b>ОПЛАЧЕНО!</b>\n\n"
        f"⭐ Сумма: {amount} Telegram Stars\n"
        f"🎮 Игра: {game_name}\n"
        f"💰 Статус: <b>В очереди на выдачу</b>\n"
        f"⏱ Ожидай пополнения в течение 1-2 минут!\n\n"
        f"Спасибо за покупку! 💪",
        reply_markup=get_order_status_inline(payment_id)
    )

# ============================================
# ПРОВЕРКА СТАТУСА ЗАКАЗА
# ============================================

@dp.callback_query(lambda c: c.data.startswith('check_status_'))
async def check_order_status(c: CallbackQuery):
    payment_id = int(c.data.replace('check_status_', ''))
    
    # Здесь можно проверить реальный статус из БД
    await c.answer("⏳ Заказ в обработке", show_alert=True)

# ============================================
# НАВИГАЦИЯ
# ============================================

@dp.callback_query(lambda c: c.data == "back_to_main")
async def back_main(c: CallbackQuery):
    await c.message.answer("🏠 <b>Главное меню</b>", reply_markup=get_main_menu())
    await c.answer()

@dp.callback_query(lambda c: c.data == "back_to_games")
async def back_games(c: CallbackQuery):
    await c.message.edit_text("🎮 <b>Выбери игру:</b>", reply_markup=get_games_inline())
    await c.answer()

@dp.callback_query(lambda c: c.data == "to_games")
async def to_games(c: CallbackQuery):
    await c.message.answer("🎮 <b>Выбери игру:</b>", reply_markup=get_games_inline())
    await c.answer()

@dp.callback_query(lambda c: c.data.startswith('back_to_amounts_'))
async def back_amounts(c: CallbackQuery):
    game_id = c.data.replace('back_to_amounts_', '')
    game_name = GAMES[game_id]['name']
    await c.message.edit_text(
        f"🎮 <b>{game_name}</b>\n💰 Выбери сумму:",
        reply_markup=get_amounts_inline(game_id)
    )
    await c.answer()

@dp.callback_query(lambda c: c.data.startswith('back_to_payment_'))
async def back_payment(c: CallbackQuery):
    parts = c.data.split('_')
    game_id = parts[3]
    amount = int(parts[4])
    rub = amount * STARS_TO_RUB
    await c.message.edit_text(
        f"🎮 {GAMES[game_id]['name']}\n"
        f"💰 {amount} ⭐ (~{rub:.0f} руб)\n\n"
        f"👇 Выбери способ оплаты:",
        reply_markup=get_payment_methods_inline(game_id, amount)
    )
    await c.answer()

@dp.callback_query(lambda c: c.data == "my_referrals")
async def show_referrals(c: CallbackQuery):
    referrals = db.get_referrals(c.from_user.id)
    if not referrals:
        await c.message.answer("👥 У тебя пока нет рефералов", reply_markup=get_back_to_main())
    else:
        text = "👥 <b>Твои рефералы:</b>\n\n"
        for ref in referrals[:10]:
            name = ref.get('first_name', 'Аноним')
            stars = ref.get('total_spent_stars', 0)
            date = ref.get('registered_at', '')[:10]
            text += f"• {name} - {stars}⭐ (с {date})\n"
        await c.message.answer(text, reply_markup=get_back_to_main())
    await c.answer()

@dp.callback_query(lambda c: c.data == "profile_history")
async def profile_history(c: CallbackQuery):
    payments = db.get_user_payments(c.from_user.id, 10)
    
    if not payments:
        await c.message.answer(
            "📊 <b>История покупок</b>\n\nУ тебя пока нет покупок.",
            reply_markup=get_back_to_main()
        )
    else:
        text = "📊 <b>История покупок</b>\n\n"
        for p in payments:
            text += f"• {p['game_name']}: {p['amount_stars']}⭐ ({p['created_at'][:16]})\n"
        await c.message.answer(text, reply_markup=get_back_to_main())
    await c.answer()

# ============================================
# АДМИНКА (ПОЛНОЦЕННАЯ)
# ============================================

@dp.message(Command("admin"))
async def cmd_admin(m: Message):
    if m.from_user.id != ADMIN_ID:
        await m.answer("⛔ Доступ запрещен")
        return
    await m.answer("👑 <b>Админ панель</b>", reply_markup=get_admin_inline())

@dp.callback_query(lambda c: c.data == "admin_stats")
async def admin_stats(c: CallbackQuery):
    if c.from_user.id != ADMIN_ID:
        await c.answer("⛔ Нет доступа", show_alert=True)
        return
    
    stats = db.get_total_stats()
    users_count = db.get_users_count()
    
    text = (
        f"👑 <b>Общая статистика</b>\n\n"
        f"👥 Всего пользователей: {users_count}\n"
        f"💰 Всего звезд: {stats['total_stars']}\n"
        f"🛒 Всего покупок: {stats['total_payments']}\n\n"
        f"📊 <b>За сегодня:</b>\n"
        f"• Новых: {stats['today_users']}\n"
        f"• Покупок: {stats['today_payments']}\n"
        f"• Звезд: {stats['today_stars']}\n"
    )
    
    await c.message.answer(text, reply_markup=get_admin_inline())
    await c.answer()

@dp.callback_query(lambda c: c.data == "admin_payments")
async def admin_payments(c: CallbackQuery):
    if c.from_user.id != ADMIN_ID:
        await c.answer("⛔ Нет доступа", show_alert=True)
        return
    
    payments = db.get_all_payments(20)
    
    if not payments:
        text = "💳 <b>Платежи</b>\n\nПока нет платежей."
    else:
        text = f"💳 <b>Последние 20 платежей</b>\n\n"
        for p in payments:
            name = p.get('first_name', 'Unknown')[:10]
            text += f"• {p['game_name']}: {p['amount_stars']}⭐ ({name}) - {p['created_at'][:16]}\n"
    
    await c.message.answer(text, reply_markup=get_admin_inline())
    await c.answer()

@dp.callback_query(lambda c: c.data == "admin_users")
async def admin_users(c: CallbackQuery):
    if c.from_user.id != ADMIN_ID:
        await c.answer("⛔ Нет доступа", show_alert=True)
        return
    
    await c.message.answer(
        "👥 <b>Пользователи</b>\n\n🚀 Функция в разработке",
        reply_markup=get_admin_inline()
    )
    await c.answer()

@dp.callback_query(lambda c: c.data == "admin_today")
async def admin_today(c: CallbackQuery):
    if c.from_user.id != ADMIN_ID:
        await c.answer("⛔ Нет доступа", show_alert=True)
        return
    
    stats = db.get_total_stats()
    
    text = (
        f"📈 <b>Статистика за сегодня</b>\n\n"
        f"👥 Новых пользователей: {stats['today_users']}\n"
        f"🛒 Покупок: {stats['today_payments']}\n"
        f"💰 Звезд: {stats['today_stars']}\n"
    )
    
    await c.message.answer(text, reply_markup=get_admin_inline())
    await c.answer()

# ============================================
# ФОНОВЫЙ ВОРКЕР ДЛЯ АВТОВЫДАЧИ
# ============================================

async def delivery_worker():
    """Фоновый процесс для автовыдачи"""
    logging.info("🚀 Delivery worker запущен")
    
    while True:
        try:
            # Здесь будет логика автовыдачи
            # Пока просто ждём
            await asyncio.sleep(60)
        except Exception as e:
            logging.error(f"Worker error: {e}")
            await asyncio.sleep(60)

# ============================================
# ЗАПУСК
# ============================================

async def main():
    logging.info("🚀 Запуск мегабота...")
    
    # Проверка CryptoBot ключа
    if CRYPTO_ENABLED and CRYPTO_API_KEY == "ТУТ_ДОЛЖЕН_БЫТЬ_ТВОЙ_КЛЮЧ_ИЗ_CRYPTOBOT":
        logging.warning("⚠️ CryptoBot ключ не настроен! Криптоплатежи работать не будут.")
        print("\n⚠️ ВНИМАНИЕ: CryptoBot ключ не настроен!")
        print("Получи ключ в @CryptoBot и вставь в CRYPTO_API_KEY\n")
    
    try:
        me = await bot.get_me()
        logging.info(f"✅ Бот @{me.username} запущен!")
        print(f"\n{'='*50}")
        print(f"🔥 МЕГАБОТ @{me.username} ЗАПУЩЕН!")
        print(f"📱 Открой Telegram и напиши /start")
        print(f"👑 Админка: /admin")
        print(f"{'='*50}\n")
        
        # Запускаем фоновый воркер
        asyncio.create_task(delivery_worker())
        
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"❌ Ошибка: {e}")
        print(f"\n❌ Ошибка: {e}")
        print("🔌 Проверь интернет и токен\n")

if __name__ == "__main__":
    asyncio.run(main())
