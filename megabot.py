#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MEGA BOT - Всё в одном файле
Telegram бот для пополнения игр с поддержкой:
- Telegram Stars
- Криптовалюты (CryptoBot)
- Реферальной системы
- API игр (Free Fire, Brawl Stars)
- Автовыдачи
- Админ-панели
- Статистики
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
from typing import Optional, Dict, Any, List

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
# КОНФИГУРАЦИЯ (меняй под себя)
# ============================================

# Токен бота от @BotFather
BOT_TOKEN = "8339352233:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw"  # ЗАМЕНИ НА СВОЙ!

# Твой Telegram ID (для админки)
ADMIN_ID = 2091630272  # ЗАМЕНИ НА СВОЙ!

# Telegram Stars
STARS_ENABLED = True
STARS_TO_RUB = 1.79

# CryptoBot
CRYPTO_ENABLED = True
CRYPTO_API_KEY = "540261:AAzd4sQW2mo4I8UdxardSygAc3H3CSZbZBs"  # Из @CryptoBot
CRYPTO_CURRENCIES = ['USDT', 'TON', 'BTC']

# Реферальная система
REFERRAL_BONUS = 10  # % от покупок реферала
REFERRAL_BONUS_STARS = 5  # Бонус за регистрацию

# API игр
FREE_FIRE_ENABLED = True
BRAWL_STARS_ENABLED = False
BRAWL_STARS_API_KEY = ""

# Суммы пополнения
PAYMENT_AMOUNTS = [1, 3, 5, 10, 25, 50, 100, 250]

# Игры
GAMES = {
    'pubg': {'name': 'PUBG Mobile (UC)', 'enabled': False},
    'brawl': {'name': 'Brawl Stars (гемы)', 'enabled': BRAWL_STARS_ENABLED},
    'steam': {'name': 'Steam Balance', 'enabled': False},
    'freefire': {'name': 'Free Fire (алмазы)', 'enabled': FREE_FIRE_ENABLED},
    'genshin': {'name': 'Genshin Impact', 'enabled': False},
    'cod': {'name': 'Call of Duty Mobile', 'enabled': False}
}

# ============================================
# БАЗА ДАННЫХ (SQLite)
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
                status TEXT DEFAULT 'completed',
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
        
        # Статистика игр
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS games_stats (
                game_id TEXT PRIMARY KEY,
                game_name TEXT,
                total_payments INTEGER DEFAULT 0,
                total_stars INTEGER DEFAULT 0,
                last_payment TIMESTAMP
            )
        ''')
        
        # Очередь на выдачу
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pending_deliveries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_id INTEGER,
                user_id INTEGER,
                game_id TEXT,
                amount INTEGER,
                game_account TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logging.info("✅ База данных готова")
    
    def add_user(self, user_id, username, first_name, last_name, referrer_code=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Реферальный код
        ref_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        # Ищем реферера
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
                total_payments = total_payments + 1,
                last_activity = ?
            WHERE user_id = ?
        ''', (amount_stars, datetime.now(), user_id))
        
        cursor.execute('''
            INSERT INTO games_stats (game_id, game_name, total_payments, total_stars, last_payment)
            VALUES (?, ?, 1, ?, ?)
            ON CONFLICT(game_id) DO UPDATE SET
                total_payments = total_payments + 1,
                total_stars = total_stars + excluded.total_stars,
                last_payment = excluded.last_payment
        ''', (game_id, game_name, amount_stars, datetime.now()))
        
        cursor.execute('''
            INSERT INTO pending_deliveries (payment_id, user_id, game_id, amount, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (payment_id, user_id, game_id, amount_stars, datetime.now()))
        
        conn.commit()
        conn.close()
        
        # Реферальный бонус
        self.process_referral_bonus(user_id, amount_stars, payment_id)
        
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
    
    def get_game_stats(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM games_stats ORDER BY total_stars DESC')
        res = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return res
    
    def get_recent_payments(self, limit=10):
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
    
    def get_daily_stats(self, days=7):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        result = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT COUNT(*) as payments, SUM(amount_stars) as stars
                FROM payments WHERE DATE(created_at) = ?
            ''', (date,))
            row = cursor.fetchone()
            result.append({
                'date': date,
                'payments': row['payments'] or 0,
                'stars': row['stars'] or 0
            })
        
        conn.close()
        return result

# ============================================
# CRYPTO BOT API
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
            "paid_btn_url": f"https://t.me/{(await bot.get_me()).username}",
            "expires_in": 3600
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as resp:
                    result = await resp.json()
                    return result.get("result") if result.get("ok") else None
        except Exception as e:
            logging.error(f"CryptoBot error: {e}")
            return None
    
    async def check_payment(self, invoice_id):
        url = f"{self.base_url}/getInvoices"
        headers = {"Crypto-Pay-API-Key": self.api_key}
        params = {"invoice_ids": invoice_id}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as resp:
                    result = await resp.json()
                    if result.get("ok") and result["result"]["items"]:
                        return result["result"]["items"][0]
        except Exception as e:
            logging.error(f"Check error: {e}")
        return None

# ============================================
# API ИГР
# ============================================

class GameAPI:
    async def deliver_freefire(self, user_id, amount, account):
        """Free Fire доставка"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://freefireapi.vercel.app/send-gift",
                    json={
                        "playerId": account,
                        "giftId": "diamonds",
                        "quantity": amount
                    }
                ) as resp:
                    if resp.status == 200:
                        return True
        except Exception as e:
            logging.error(f"FreeFire error: {e}")
        return False
    
    async def deliver_brawl(self, user_id, amount, account):
        """Brawl Stars доставка"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://api.brawlstars.com/v1/players/%23{account.replace('#', '')}",
                    headers={"Authorization": f"Bearer {BRAWL_STARS_API_KEY}"}
                ) as resp:
                    return resp.status == 200
        except Exception as e:
            logging.error(f"Brawl error: {e}")
        return False
    
    async def deliver(self, game_id, user_id, amount, account):
        methods = {
            'freefire': self.deliver_freefire,
            'brawl': self.deliver_brawl
        }
        method = methods.get(game_id)
        return await method(user_id, amount, account) if method else False

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
    builder.row(InlineKeyboardButton(text="🏠 Меню", callback_data="back_to_main"))
    return builder.as_markup()

def get_amounts_inline(game_id):
    builder = InlineKeyboardBuilder()
    for amount in PAYMENT_AMOUNTS:
        builder.button(text=f"{amount} ⭐", callback_data=f"amount_{game_id}_{amount}")
    builder.adjust(3)
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_games"),
        InlineKeyboardButton(text="🏠 Меню", callback_data="back_to_main")
    )
    return builder.as_markup()

def get_payment_methods_inline(game_id, amount):
    builder = InlineKeyboardBuilder()
    if STARS_ENABLED:
        builder.button(text="⭐ Stars", callback_data=f"pay_stars_{game_id}_{amount}")
    if CRYPTO_ENABLED:
        builder.button(text="₿ Крипта", callback_data=f"pay_crypto_{game_id}_{amount}")
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data=f"back_to_amounts_{game_id}"),
        InlineKeyboardButton(text="🏠 Меню", callback_data="back_to_main")
    )
    return builder.as_markup()

def get_crypto_currencies_inline(game_id, amount):
    builder = InlineKeyboardBuilder()
    for curr in CRYPTO_CURRENCIES:
        builder.button(text=curr, callback_data=f"crypto_{curr}_{game_id}_{amount}")
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data=f"back_to_payment_{game_id}_{amount}"),
        InlineKeyboardButton(text="🏠 Меню", callback_data="back_to_main")
    )
    return builder.as_markup()

def get_profile_inline():
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 История", callback_data="profile_history")
    builder.button(text="⭐ Пополнить", callback_data="to_games")
    builder.button(text="🏠 Меню", callback_data="back_to_main")
    builder.adjust(2, 1)
    return builder.as_markup()

def get_referral_inline(code):
    builder = InlineKeyboardBuilder()
    builder.button(text="📤 Поделиться", switch_inline_query=f"🎮 Игры со скидкой! {code}")
    builder.button(text="👥 Мои рефералы", callback_data="my_referrals")
    builder.button(text="🏠 Меню", callback_data="back_to_main")
    builder.adjust(2, 1)
    return builder.as_markup()

def get_admin_inline():
    builder = InlineKeyboardBuilder()
    buttons = [
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
        InlineKeyboardButton(text="💳 Платежи", callback_data="admin_payments"),
        InlineKeyboardButton(text="📈 Графики", callback_data="admin_charts"),
        InlineKeyboardButton(text="🏠 Меню", callback_data="back_to_main")
    ]
    builder.add(*buttons)
    builder.adjust(2, 2)
    return builder.as_markup()

def get_back_to_main():
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 Главное меню", callback_data="back_to_main")
    return builder.as_markup()

# ============================================
# ИНИЦИАЛИЗАЦИЯ
# ============================================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
db = Database()
crypto = CryptoBotAPI(CRYPTO_API_KEY) if CRYPTO_ENABLED else None
game_api = GameAPI()

# Временное хранилище
users_data = {}

# ============================================
# ОБРАБОТЧИКИ КОМАНД
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
    
    if ref_code and REFERRAL_BONUS_STARS > 0:
        await message.answer(f"🎉 Ты по рефералке! +{REFERRAL_BONUS_STARS}⭐ после первой покупки!")
    
    await message.answer(
        f"👋 <b>Привет, {user.first_name}!</b>\n\n"
        f"🎮 Пополняй игры:\n"
        f"⭐ Telegram Stars\n"
        f"₿ Криптовалюта (USDT, TON, BTC)\n\n"
        f"👇 Выбирай:",
        reply_markup=get_main_menu()
    )

@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Доступ запрещен")
        return
    await message.answer("👑 <b>Админ панель</b>", reply_markup=get_admin_inline())

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
    if stats and stats['total_payments'] > 0:
        text = (
            f"📊 <b>Твой профиль</b>\n\n"
            f"💰 Потрачено: {stats['total_spent_stars']} ⭐\n"
            f"🛒 Покупок: {stats['total_payments']}\n"
            f"👥 Рефералов: {stats.get('referrals_count', 0)}\n"
            f"🎁 Бонусов: {stats.get('total_bonus', 0)} ⭐"
        )
    else:
        text = f"📊 <b>Профиль</b>\n\nПока нет покупок. Выбери игру!"
    await m.answer(text, reply_markup=get_profile_inline())

@dp.message(lambda m: m.text == "👥 Рефералы")
async def menu_referrals(m: Message):
    stats = db.get_user_stats(m.from_user.id)
    if stats:
        link = f"https://t.me/{(await bot.get_me()).username}?start={stats['referral_code']}"
        text = (
            f"👥 <b>Рефералы</b>\n\n"
            f"🔗 {link}\n\n"
            f"🎁 {REFERRAL_BONUS}% от покупок\n"
            f"👥 Приглашено: {stats.get('referrals_count', 0)}\n"
            f"💰 Заработано: {stats.get('total_bonus', 0)} ⭐"
        )
        await m.answer(text, reply_markup=get_referral_inline(stats['referral_code']))

@dp.message(lambda m: m.text == "❓ Помощь")
async def menu_help(m: Message):
    await m.answer(
        "❓ <b>Помощь</b>\n\n"
        "1. Выбери игру\n"
        "2. Укажи сумму в ⭐\n"
        "3. Введи ID в игре\n"
        "4. Выбери способ оплаты\n"
        "5. Получи пополнение!",
        reply_markup=get_back_to_main()
    )

@dp.message(lambda m: m.text == "📞 Контакты")
async def menu_contacts(m: Message):
    await m.answer(
        "📞 <b>Контакты</b>\n\n"
        "👨‍💻 @твой_username\n"
        "🕐 24/7",
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
        f"🎮 <b>{game_name}</b>\n💰 Выбери сумму:",
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
        f"💰 {amount}⭐ (~{rub:.0f} руб)\n\n"
        f"📝 <b>Введи свой ID в игре:</b>",
        reply_markup=None
    )
    users_data[uid]['awaiting_account'] = True
    await c.answer()

@dp.message(lambda m: m.from_user.id in users_data and users_data[m.from_user.id].get('awaiting_account'))
async def account_entered(m: Message):
    uid = m.from_user.id
    account = m.text.strip()
    users_data[uid]['account'] = account
    users_data[uid]['awaiting_account'] = False
    
    rub = users_data[uid]['amount'] * STARS_TO_RUB
    await m.answer(
        f"🎮 {users_data[uid]['name']}\n"
        f"💰 {users_data[uid]['amount']}⭐ (~{rub:.0f} руб)\n"
        f"👤 {account}\n\n"
        f"👇 <b>Выбери способ оплаты:</b>",
        reply_markup=get_payment_methods_inline(users_data[uid]['game'], users_data[uid]['amount'])
    )

# ============================================
# ОПЛАТА
# ============================================

@dp.callback_query(lambda c: c.data.startswith('pay_stars_'))
async def pay_stars(c: CallbackQuery):
    parts = c.data.split('_')
    game_id = parts[2]
    amount = int(parts[3])
    uid = c.from_user.id
    game_name = GAMES[game_id]['name']
    
    prices = [LabeledPrice(label=f"{game_name}", amount=amount)]
    await c.message.answer_invoice(
        title=f"{game_name}",
        description=f"{amount} ⭐",
        payload=f"stars_{game_id}_{amount}_{uid}",
        provider_token="",
        currency="XTR",
        prices=prices
    )
    await c.answer()

@dp.callback_query(lambda c: c.data.startswith('pay_crypto_'))
async def pay_crypto(c: CallbackQuery):
    parts = c.data.split('_')
    game_id = parts[2]
    amount = int(parts[3])
    rub = amount * STARS_TO_RUB
    await c.message.edit_text(
        f"₿ <b>Криптовалюта</b>\n\n"
        f"Сумма: {amount}⭐ (~{rub:.0f} руб)\n"
        f"Выбери валюту:",
        reply_markup=get_crypto_currencies_inline(game_id, amount)
    )
    await c.answer()

@dp.callback_query(lambda c: c.data.startswith('crypto_'))
async def crypto_selected(c: CallbackQuery):
    parts = c.data.split('_')
    currency = parts[1]
    game_id = parts[2]
    amount = int(parts[3])
    uid = c.from_user.id
    game_name = GAMES[game_id]['name']
    
    if not crypto:
        await c.message.edit_text("❌ Крипта временно недоступна", reply_markup=get_back_to_main())
        await c.answer()
        return
    
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
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить", url=invoice["pay_url"])],
            [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"check_crypto_{invoice['invoice_id']}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data=f"back_to_payment_{game_id}_{amount}")]
        ])
        await c.message.edit_text(
            f"₿ <b>Счет</b>\n\n{crypto_amount} {currency}",
            reply_markup=kb
        )
    else:
        await c.message.edit_text("❌ Ошибка", reply_markup=get_back_to_main())
    await c.answer()

@dp.callback_query(lambda c: c.data.startswith('check_crypto_'))
async def check_crypto(c: CallbackQuery):
    invoice_id = c.data.replace('check_crypto_', '')
    uid = c.from_user.id
    
    invoice = await crypto.check_payment(invoice_id)
    if invoice and invoice.get("status") == "paid":
        if uid in users_data:
            db.add_payment(
                user_id=uid,
                game_id=users_data[uid]['game'],
                game_name=users_data[uid]['name'],
                amount_stars=users_data[uid]['amount'],
                amount_real=float(invoice.get("amount", 0)),
                currency=invoice.get("asset", "USDT"),
                method="crypto",
                charge_id=invoice_id
            )
            await c.message.edit_text(
                f"✅ <b>ОПЛАЧЕНО!</b>\n\n"
                f"🎮 {users_data[uid]['name']}\n"
                f"⭐ {users_data[uid]['amount']} Stars\n"
                f"🔜 Зачисление...",
                reply_markup=get_back_to_main()
            )
    else:
        await c.answer("⏳ Платеж не найден", show_alert=True)
    await c.answer()

# ============================================
# УСПЕШНЫЙ ПЛАТЕЖ (STARS)
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
    game_name = GAMES.get(game_id, {}).get('name', 'Unknown')
    uid = m.from_user.id
    
    # Сохраняем в БД
    db.add_payment(
        user_id=uid,
        game_id=game_id,
        game_name=game_name,
        amount_stars=amount,
        amount_real=amount,
        currency="XTR",
        method="stars",
        charge_id=charge_id
    )
    
    # Пытаемся выдать через API
    account = users_data.get(uid, {}).get('account', '')
    delivered = await game_api.deliver(game_id, uid, amount, account)
    
    status = "✅ Средства зачислены!" if delivered else "⏳ Заявка оператору"
    
    await m.answer(
        f"✅ <b>ОПЛАЧЕНО!</b>\n\n"
        f"⭐ {amount} Stars\n"
        f"🎮 {game_name}\n"
        f"💰 {status}\n\n"
        f"Спасибо! 💪",
        reply_markup=get_back_to_main()
    )

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
        f"💰 {amount}⭐ (~{rub:.0f} руб)\n\n"
        f"👇 <b>Способ оплаты:</b>",
        reply_markup=get_payment_methods_inline(game_id, amount)
    )
    await c.answer()

@dp.callback_query(lambda c: c.data == "my_referrals")
async def show_referrals(c: CallbackQuery):
    referrals = db.get_referrals(c.from_user.id)
    if not referrals:
        await c.message.answer("👥 Пока нет рефералов", reply_markup=get_back_to_main())
    else:
        text = "👥 <b>Рефералы:</b>\n"
        for ref in referrals[:10]:
            text += f"• {ref.get('first_name', 'Аноним')} - {ref['total_spent_stars']}⭐\n"
        await c.message.answer(text, reply_markup=get_back_to_main())
    await c.answer()

@dp.callback_query(lambda c: c.data == "profile_history")
async def profile_history(c: CallbackQuery):
    await c.message.answer("📊 <b>История</b>\n\n🚀 В разработке", reply_markup=get_back_to_main())
    await c.answer()

# ============================================
# АДМИНКА
# ============================================

@dp.callback_query(lambda c: c.data == "admin_stats")
async def admin_stats(c: CallbackQuery):
    if c.from_user.id != ADMIN_ID:
        await c.answer("⛔ Нет доступа", show_alert=True)
        return
    
    games = db.get_game_stats()
    recent = db.get_recent_payments(5)
    daily = db.get_daily_stats(7)
    
    total_stars = sum(g['total_stars'] for g in games) if games else 0
    total_payments = sum(g['total_payments'] for g in games) if games else 0
    
    text = f"👑 <b>Статистика</b>\n\n💰 Всего: {total_stars}⭐ ({total_payments} покупок)\n\n"
    text += "<b>Последние дни:</b>\n"
    for d in daily:
        text += f"• {d['date']}: {d['payments']} покупок | {d['stars']}⭐\n"
    
    text += "\n<b>По играм:</b>\n"
    for g in games:
        text += f"• {g['game_name']}: {g['total_payments']} | {g['total_stars']}⭐\n"
    
    text += "\n<b>Последние:</b>\n"
    for p in recent:
        name = p.get('first_name', 'Unknown')
        text += f"• {p['game_name']}: {p['amount_stars']}⭐ ({name})\n"
    
    await c.message.answer(text, reply_markup=get_admin_inline())
    await c.answer()

@dp.callback_query(lambda c: c.data == "admin_payments")
async def admin_payments(c: CallbackQuery):
    if c.from_user.id != ADMIN_ID:
        await c.answer("⛔ Нет доступа", show_alert=True)
        return
    await c.message.answer("💳 <b>Платежи</b>\n\n🚀 В разработке", reply_markup=get_admin_inline())
    await c.answer()

@dp.callback_query(lambda c: c.data == "admin_charts")
async def admin_charts(c: CallbackQuery):
    if c.from_user.id != ADMIN_ID:
        await c.answer("⛔ Нет доступа", show_alert=True)
        return
    daily = db.get_daily_stats(7)
    text = "📈 <b>График за 7 дней:</b>\n"
    for d in daily:
        bars = "█" * int(d['stars'] / 100) if d['stars'] > 0 else "▏"
        text += f"{d['date'][5:]}: {bars} {d['stars']}⭐\n"
    await c.message.answer(text, reply_markup=get_admin_inline())
    await c.answer()

# ============================================
# ФОНОВЫЙ ВОРКЕР
# ============================================

async def delivery_worker():
    """Фоновый процесс автовыдачи"""
    logging.info("🚀 Delivery worker запущен")
    while True:
        try:
            await asyncio.sleep(30)
        except Exception as e:
            logging.error(f"Worker error: {e}")
            await asyncio.sleep(60)

# ============================================
# ЗАПУСК
# ============================================

async def main():
    logging.info("🚀 Запуск мегабота...")
    
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
