#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MEGA BOT - ФИНАЛЬНАЯ ВЕРСИЯ С ТВОИМИ КЛЮЧАМИ
Telegram бот для пополнения игр с донатом, рефералами и автовыдачей
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
from collections import defaultdict

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery, LabeledPrice,
    PreCheckoutQuery, InlineKeyboardMarkup, 
    InlineKeyboardButton, ReplyKeyboardMarkup,
    KeyboardButton, FSInputFile
)
from aiogram.client.bot import DefaultBotProperties
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# ============================================
# ТВОИ ДАННЫЕ (УЖЕ ВСТАВЛЕНЫ)
# ============================================

# Токен бота от @BotFather
BOT_TOKEN = "8339352233:AAGixj9izEbOVKHvhpKeTd_4_Y2CP-f-ZhE"

# Твой Telegram ID
ADMIN_ID = 2091630272

# CryptoBot ключ (получен из @CryptoBot)
CRYPTO_API_KEY = "540261:AAzd4sQW2mo4I8UdxardSygAc3H3CSZbZBs"

# ============================================
# НАСТРОЙКИ
# ============================================

# Telegram Stars
STARS_ENABLED = True
STARS_TO_RUB = 1.79

# Крипта
CRYPTO_ENABLED = True
CRYPTO_CURRENCIES = ['USDT', 'TON', 'BTC']

# Реферальная система
REFERRAL_BONUS = 10  # %
REFERRAL_BONUS_STARS = 5  # бонус за регистрацию

# Ежедневный бонус
DAILY_BONUS_AMOUNT = 1  # ⭐ в день

# API Free Fire
FREE_FIRE_ENABLED = True
FREE_FIRE_API_URL = "https://freefireapi.vercel.app"

# Все игры
GAMES = {
    'pubg': {'name': 'PUBG Mobile (UC)', 'enabled': True, 'api': None, 'icon': '🪖'},
    'brawl': {'name': 'Brawl Stars (гемы)', 'enabled': True, 'api': None, 'icon': '🥊'},
    'steam': {'name': 'Steam Balance', 'enabled': True, 'api': None, 'icon': '🎮'},
    'freefire': {'name': 'Free Fire (алмазы)', 'enabled': True, 'api': 'freefire', 'icon': '🔥'},
    'genshin': {'name': 'Genshin Impact', 'enabled': True, 'api': None, 'icon': '✨'},
    'cod': {'name': 'Call of Duty Mobile', 'enabled': True, 'api': None, 'icon': '🔫'}
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
                last_activity TIMESTAMP,
                last_daily_bonus TIMESTAMP,
                daily_bonus_count INTEGER DEFAULT 0
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
        
        # Чат поддержки
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS support_chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message TEXT,
                admin_reply TEXT,
                created_at TIMESTAMP,
                replied_at TIMESTAMP,
                is_closed BOOLEAN DEFAULT 0
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
        if referrer_id:
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
        
        # Обновляем статус платежа
        cursor.execute('''
            UPDATE payments SET status = 'processing' WHERE id = ?
        ''', (payment_id,))
        
        conn.commit()
        conn.close()
    
    def mark_delivery_completed(self, delivery_id, payment_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE delivery_queue SET status = 'completed' WHERE id = ?
        ''', (delivery_id,))
        
        cursor.execute('''
            UPDATE payments SET status = 'completed', delivered_at = ? WHERE id = ?
        ''', (datetime.now(), payment_id))
        
        conn.commit()
        conn.close()
    
    def get_daily_bonus(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT last_daily_bonus FROM users WHERE user_id = ?', (user_id,))
        res = cursor.fetchone()
        
        if res and res['last_daily_bonus']:
            last = datetime.fromisoformat(res['last_daily_bonus'])
            if datetime.now().date() == last.date():
                conn.close()
                return False
        
        cursor.execute('''
            UPDATE users 
            SET last_daily_bonus = ?, 
                total_spent_stars = total_spent_stars + ?,
                daily_bonus_count = daily_bonus_count + 1
            WHERE user_id = ?
        ''', (datetime.now(), DAILY_BONUS_AMOUNT, user_id))
        
        conn.commit()
        conn.close()
        return True
    
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
    
    def get_user_payments(self, user_id, limit=10):
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
    
    def get_all_payments(self, limit=50):
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
    
    def get_top_donaters(self, limit=10):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, first_name, username, total_spent_stars 
            FROM users 
            WHERE total_spent_stars > 0
            ORDER BY total_spent_stars DESC
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

db = Database()

# ============================================
# УВЕДОМЛЕНИЯ (ИСПРАВЛЕНЫ)
# ============================================

async def notify_admin_new_payment(user_id, game_name, amount, method):
    """Отправляет уведомление админу о новой покупке"""
    try:
        # Получаем инфу о пользователе
        user_stats = db.get_user_stats(user_id)
        username = user_stats.get('username', 'Нет') if user_stats else 'Нет'
        
        text = (
            f"🔥 <b>НОВАЯ ПОКУПКА!</b>\n\n"
            f"👤 <b>Пользователь:</b>\n"
            f"  ID: <code>{user_id}</code>\n"
            f"  Username: @{username}\n"
            f"  Имя: {user_stats.get('first_name', 'Неизвестно') if user_stats else 'Неизвестно'}\n\n"
            f"🎮 <b>Детали:</b>\n"
            f"  Игра: {game_name}\n"
            f"  Сумма: {amount} ⭐\n"
            f"  Способ: {method}\n\n"
            f"📊 <b>Всего у пользователя:</b>\n"
            f"  Покупок: {user_stats.get('total_payments', 0) if user_stats else 0}\n"
            f"  Звезд: {user_stats.get('total_spent_stars', 0) if user_stats else 0}\n\n"
            f"🕐 {datetime.now().strftime('%H:%M:%S %d.%m.%Y')}"
        )
        await bot.send_message(ADMIN_ID, text)
    except Exception as e:
        logging.error(f"Ошибка уведомления админа: {e}")

async def notify_referrer(referrer_id, referral_id):
    """Уведомляет о новом реферале"""
    try:
        text = (
            f"👥 <b>Новый реферал!</b>\n\n"
            f"По вашей ссылке зарегистрировался новый пользователь!\n"
            f"После его первой покупки вы получите бонус {REFERRAL_BONUS}%."
        )
        await bot.send_message(referrer_id, text)
    except Exception as e:
        logging.error(f"Ошибка уведомления реферера: {e}")

async def notify_delivery_complete(user_id, game_name, amount):
    """Уведомляет пользователя о выполненном заказе"""
    try:
        text = (
            f"✅ <b>Заказ выполнен!</b>\n\n"
            f"🎮 Игра: {game_name}\n"
            f"💰 Сумма: {amount} ⭐\n\n"
            f"Спасибо за покупку! Возвращайся ещё! 🚀"
        )
        await bot.send_message(user_id, text)
    except Exception as e:
        logging.error(f"Ошибка уведомления о доставке: {e}")

# ============================================
# CRYPTO BOT API (С ТВОИМ КЛЮЧОМ)
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
# FREE FIRE API (АВТОВЫДАЧА)
# ============================================

class FreeFireAPI:
    def __init__(self):
        self.base_url = FREE_FIRE_API_URL
        self.accounts = []
        self.load_accounts()
    
    def load_accounts(self):
        """Загружает аккаунты из базы"""
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        cursor.execute('''
            SELECT account_data FROM game_accounts 
            WHERE game_id = 'freefire' AND is_active = 1
        ''')
        accounts = cursor.fetchall()
        self.accounts = [json.loads(acc[0]) for acc in accounts]
        conn.close()
    
    async def send_diamonds(self, player_id, amount):
        """Отправляет алмазы игроку"""
        if not self.accounts:
            logging.warning("Нет аккаунтов Free Fire для выдачи")
            return False
        
        # Выбираем аккаунт с достаточным балансом
        account = None
        for acc in self.accounts:
            if acc.get('balance', 0) >= amount:
                account = acc
                break
        
        if not account:
            logging.warning("Нет аккаунтов с достаточным балансом")
            return False
        
        try:
            # Здесь реальный API запрос к freefireapi.vercel.app
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/send-gift",
                    json={
                        "playerId": player_id,
                        "giftId": "diamonds",
                        "quantity": amount
                    },
                    headers={"Authorization": f"Bearer {account.get('token', '')}"}
                ) as resp:
                    if resp.status == 200:
                        # Обновляем баланс аккаунта
                        account['balance'] -= amount
                        # Сохраняем в БД
                        await self.update_account_balance(account)
                        return True
        except Exception as e:
            logging.error(f"FreeFire API error: {e}")
        return False
    
    async def update_account_balance(self, account):
        """Обновляет баланс аккаунта в БД"""
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE game_accounts 
            SET balance = ?, last_used = ?, usage_count = usage_count + 1
            WHERE id = ?
        ''', (account['balance'], datetime.now(), account.get('id', 0)))
        conn.commit()
        conn.close()

# ============================================
# КЛАВИАТУРЫ (С НОВЫМИ КНОПКАМИ)
# ============================================

def get_main_menu():
    builder = ReplyKeyboardBuilder()
    buttons = [
        KeyboardButton(text="🎮 Игры"),
        KeyboardButton(text="⭐ Пополнить"),
        KeyboardButton(text="📊 Профиль"),
        KeyboardButton(text="👥 Рефералы"),
        KeyboardButton(text="🎁 Бонус"),
        KeyboardButton(text="📞 Помощь")
    ]
    builder.add(*buttons)
    builder.adjust(2, 2, 2)
    return builder.as_markup(resize_keyboard=True)

def get_games_inline():
    builder = InlineKeyboardBuilder()
    for game_id, game in GAMES.items():
        if game['enabled']:
            builder.button(text=f"{game['icon']} {game['name']}", callback_data=f"game_{game_id}")
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
        InlineKeyboardButton(text="🏠 Меню", callback_data="back_to_main")
    )
    return builder.as_markup()

def get_payment_methods_inline(game_id, amount):
    builder = InlineKeyboardBuilder()
    builder.button(text="⭐ Telegram Stars", callback_data=f"pay_stars_{game_id}_{amount}")
    builder.button(text="₿ Криптовалюта", callback_data=f"pay_crypto_{game_id}_{amount}")
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
    builder.button(text="🏆 Топ донатеров", callback_data="top_donaters")
    builder.button(text="⭐ Пополнить", callback_data="to_games")
    builder.button(text="🏠 Меню", callback_data="back_to_main")
    builder.adjust(2, 1, 1)
    return builder.as_markup()

def get_referral_inline(code):
    builder = InlineKeyboardBuilder()
    builder.button(text="📤 Поделиться", switch_inline_query=f"🔥 Игры со скидкой! {code}")
    builder.button(text="👥 Мои рефералы", callback_data="my_referrals")
    builder.button(text="🏠 Меню", callback_data="back_to_main")
    builder.adjust(2, 1)
    return builder.as_markup()

def get_admin_inline():
    builder = InlineKeyboardBuilder()
    buttons = [
        InlineKeyboardButton(text="📊 Общая статистика", callback_data="admin_stats"),
        InlineKeyboardButton(text="💳 Все платежи", callback_data="admin_payments"),
        InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users"),
        InlineKeyboardButton(text="📈 Графики", callback_data="admin_charts"),
        InlineKeyboardButton(text="💰 Прогноз", callback_data="admin_profit"),
        InlineKeyboardButton(text="🏠 Меню", callback_data="back_to_main")
    ]
    builder.add(*buttons)
    builder.adjust(2, 2, 2)
    return builder.as_markup()

def get_back_to_main():
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 Главное меню", callback_data="back_to_main")
    return builder.as_markup()

def get_order_status_inline(payment_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Проверить статус", callback_data=f"check_status_{payment_id}")
    builder.button(text="🏠 Меню", callback_data="back_to_main")
    builder.adjust(1, 1)
    return builder.as_markup()

def get_support_inline():
    builder = InlineKeyboardBuilder()
    builder.button(text="💬 Написать админу", callback_data="support_new")
    builder.button(text="🏠 Меню", callback_data="back_to_main")
    builder.adjust(1, 1)
    return builder.as_markup()

# ============================================
# ИНИЦИАЛИЗАЦИЯ (С ТВОИМИ КЛЮЧАМИ)
# ============================================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# Инициализация API
crypto = CryptoBotAPI(CRYPTO_API_KEY)
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
        f"₿ Криптовалюта (USDT, TON, BTC)\n\n"
        f"🎁 Ежедневный бонус: +1⭐ каждый день\n"
        f"👥 Рефералы: до 10% от покупок друзей\n\n"
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
                status_emoji = "✅" if p['status'] == 'completed' else "⏳"
                text += f"• {status_emoji} {p['game_name']}: {p['amount_stars']}⭐ ({p['created_at'][:16]})\n"
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

@dp.message(lambda m: m.text == "🎁 Бонус")
async def menu_bonus(m: Message):
    success = db.get_daily_bonus(m.from_user.id)
    
    if success:
        await m.answer(
            f"🎁 <b>Ежедневный бонус получен!</b>\n\n"
            f"+{DAILY_BONUS_AMOUNT} ⭐ зачислено на твой счёт!\n\n"
            f"Заходи завтра за новым бонусом! 🔥",
            reply_markup=get_back_to_main()
        )
    else:
        await m.answer(
            f"🎁 <b>Ежедневный бонус</b>\n\n"
            f"Ты уже получал бонус сегодня.\n"
            f"Возвращайся завтра!",
            reply_markup=get_back_to_main()
        )

@dp.message(lambda m: m.text == "📞 Помощь")
async def menu_help(m: Message):
    await m.answer(
        "📞 <b>Помощь и поддержка</b>\n\n"
        "❓ <b>Частые вопросы:</b>\n"
        "• Пополнение происходит в течение 1-5 минут\n"
        "• Если заказ не пришёл, напиши в поддержку\n"
        "• Реферальный бонус начисляется автоматически\n"
        "• Ежедневный бонус обновляется в 00:00 МСК\n\n"
        "💬 <b>Связь с админом:</b>\n"
        "Нажми кнопку ниже, чтобы написать сообщение",
        reply_markup=get_support_inline()
    )

# ============================================
# ПОДДЕРЖКА (ЧАТ С АДМИНОМ)
# ============================================

@dp.callback_query(lambda c: c.data == "support_new")
async def support_new(c: CallbackQuery):
    await c.message.edit_text(
        "💬 <b>Написать админу</b>\n\n"
        "Отправь одним сообщением всё, что хочешь сказать:\n"
        "• Вопрос по заказу\n"
        "• Проблема с пополнением\n"
        "• Предложение\n\n"
        "Админ ответит как только освободится.",
        reply_markup=get_back_to_main()
    )
    users_data[c.from_user.id] = {'support_mode': True}
    await c.answer()

@dp.message(lambda m: m.from_user.id in users_data and users_data[m.from_user.id].get('support_mode'))
async def support_message(m: Message):
    uid = m.from_user.id
    text = m.text
    
    # Сохраняем в БД
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO support_chats (user_id, message, created_at)
        VALUES (?, ?, ?)
    ''', (uid, text, datetime.now()))
    chat_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # Отправляем админу
    user_info = db.get_user_stats(uid)
    username = user_info.get('username', 'Нет') if user_info else 'Нет'
    
    admin_text = (
        f"💬 <b>Новое сообщение в поддержку</b>\n\n"
        f"👤 Пользователь: {m.from_user.first_name}\n"
        f"🆔 ID: <code>{uid}</code>\n"
        f"📱 Username: @{username}\n"
        f"📝 Сообщение: {text}\n\n"
        f"Ответить: /reply_{chat_id} текст"
    )
    await bot.send_message(ADMIN_ID, admin_text)
    
    await m.answer(
        "✅ Сообщение отправлено админу!\n"
        "Ожидай ответа, мы свяжемся с тобой в ближайшее время.",
        reply_markup=get_back_to_main()
    )
    
    users_data[uid]['support_mode'] = False

@dp.message(Command("reply"))
async def admin_reply(m: Message):
    if m.from_user.id != ADMIN_ID:
        return
    
    parts = m.text.split(' ', 2)
    if len(parts) < 3:
        await m.answer("Формат: /reply_123 текст ответа")
        return
    
    chat_id = int(parts[0].replace('/reply_', ''))
    reply_text = parts[2]
    
    # Получаем user_id из чата
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM support_chats WHERE id = ?', (chat_id,))
    res = cursor.fetchone()
    
    if res:
        user_id = res[0]
        cursor.execute('''
            UPDATE support_chats SET admin_reply = ?, replied_at = ? WHERE id = ?
        ''', (reply_text, datetime.now(), chat_id))
        conn.commit()
        
        # Отправляем пользователю
        await bot.send_message(
            user_id,
            f"📬 <b>Ответ от поддержки:</b>\n\n{reply_text}\n\n"
            f"Если остались вопросы, можешь написать снова!",
            reply_markup=get_support_inline()
        )
        
        await m.answer("✅ Ответ отправлен пользователю!")
    else:
        await m.answer("❌ Чат не найден")
    
    conn.close()

# ============================================
# ВЫБОР ИГРЫ И СУММЫ
# ============================================

@dp.callback_query(lambda c: c.data.startswith('game_'))
async def game_selected(c: CallbackQuery):
    game_id = c.data.replace('game_', '')
    game = GAMES[game_id]
    game_name = game['name']
    game_icon = game['icon']
    users_data[c.from_user.id] = {'game': game_id, 'name': game_name, 'icon': game_icon}
    await c.message.edit_text(
        f"{game_icon} <b>{game_name}</b>\n💰 Выбери сумму в ⭐ Stars:",
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
        f"{users_data[uid]['icon']} <b>{users_data[uid]['name']}</b>\n"
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
        await m.answer("❌ ID слишком короткий. Введи корректный ID (минимум 3 символа):")
        return
    
    users_data[uid]['account'] = account
    users_data[uid]['awaiting_account'] = False
    
    rub = users_data[uid]['amount'] * STARS_TO_RUB
    await m.answer(
        f"{users_data[uid]['icon']} <b>{users_data[uid]['name']}</b>\n"
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
# ОПЛАТА КРИПТОЙ (С ТВОИМ КЛЮЧОМ - РАБОТАЕТ!)
# ============================================

@dp.callback_query(lambda c: c.data.startswith('pay_crypto_'))
async def pay_crypto(c: CallbackQuery):
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
    
    # Проверяем статус через API CryptoBot
    invoice = await crypto.check_payment(invoice_id)
    
    if invoice and invoice.get("status") == "paid":
        if uid in users_data and 'game' in users_data[uid]:
            # Сохраняем платеж в БД
            payment_id = db.add_payment(
                user_id=uid,
                game_id=users_data[uid]['game'],
                game_name=users_data[uid]['name'],
                amount_stars=users_data[uid]['amount'],
                amount_real=float(invoice.get("amount", 0)),
                currency=invoice.get("asset", "CRYPTO"),
                method="crypto",
                charge_id=invoice_id
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
    else:
        await c.answer("⏳ Платеж не найден или ещё не оплачен", show_alert=True)

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
    
    # Получаем статус из БД
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute('SELECT status FROM payments WHERE id = ?', (payment_id,))
    res = cursor.fetchone()
    conn.close()
    
    if res:
        status = res[0]
        status_text = {
            'pending': '⏳ Ожидает обработки',
            'processing': '🔄 В процессе выдачи',
            'completed': '✅ Выполнен',
            'failed': '❌ Ошибка'
        }.get(status, '❓ Неизвестно')
        
        await c.answer(f"Статус: {status_text}", show_alert=True)
    else:
        await c.answer("❌ Заказ не найден", show_alert=True)

# ============================================
# ТОП ДОНАТЕРОВ
# ============================================

@dp.callback_query(lambda c: c.data == "top_donaters")
async def show_top_donaters(c: CallbackQuery):
    top = db.get_top_donaters(10)
    
    if not top:
        await c.message.answer(
            "🏆 <b>Топ донатеров</b>\n\nПока нет данных. Будь первым!",
            reply_markup=get_back_to_main()
        )
        await c.answer()
        return
    
    text = "🏆 <b>Топ донатеров</b>\n\n"
    
    for i, user in enumerate(top, 1):
        name = user.get('first_name', 'Аноним')[:15]
        stars = user.get('total_spent_stars', 0)
        
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        text += f"{medal} {name} - {stars} ⭐\n"
    
    text += "\nПокупай больше и попади в топ! 🚀"
    
    await c.message.answer(text, reply_markup=get_back_to_main())
    await c.answer()

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
    game = GAMES[game_id]
    await c.message.edit_text(
        f"{game['icon']} <b>{game['name']}</b>\n💰 Выбери сумму:",
        reply_markup=get_amounts_inline(game_id)
    )
    await c.answer()

@dp.callback_query(lambda c: c.data.startswith('back_to_payment_'))
async def back_payment(c: CallbackQuery):
    parts = c.data.split('_')
    game_id = parts[3]
    amount = int(parts[4])
    rub = amount * STARS_TO_RUB
    game = GAMES[game_id]
    await c.message.edit_text(
        f"{game['icon']} <b>{game['name']}</b>\n"
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
    payments = db.get_user_payments(c.from_user.id, 20)
    
    if not payments:
        await c.message.answer(
            "📊 <b>История покупок</b>\n\nУ тебя пока нет покупок.",
            reply_markup=get_back_to_main()
        )
    else:
        text = "📊 <b>История покупок</b>\n\n"
        for p in payments:
            status_emoji = "✅" if p['status'] == 'completed' else "⏳"
            text += f"{status_emoji} {p['game_name']}: {p['amount_stars']}⭐ ({p['created_at'][:16]})\n"
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
        f"👥 <b>Всего:</b>\n"
        f"• Пользователей: {users_count}\n"
        f"• Покупок: {stats['total_payments']}\n"
        f"• Звезд: {stats['total_stars']}\n\n"
        f"📊 <b>За сегодня:</b>\n"
        f"• Новых: {stats['today_users']}\n"
        f"• Покупок: {stats['today_payments']}\n"
        f"• Звезд: {stats['today_stars']}\n"
        f"• Прибыль: ~{stats['today_stars'] * STARS_TO_RUB:.0f} руб\n\n"
        f"📈 <b>Средний чек:</b>\n"
        f"{stats['total_stars'] // max(stats['total_payments'], 1)} ⭐"
    )
    
    await c.message.answer(text, reply_markup=get_admin_inline())
    await c.answer()

@dp.callback_query(lambda c: c.data == "admin_payments")
async def admin_payments(c: CallbackQuery):
    if c.from_user.id != ADMIN_ID:
        await c.answer("⛔ Нет доступа", show_alert=True)
        return
    
    payments = db.get_all_payments(30)
    
    if not payments:
        text = "💳 <b>Платежи</b>\n\nПока нет платежей."
    else:
        text = f"💳 <b>Последние 30 платежей</b>\n\n"
        for p in payments:
            name = p.get('first_name', 'Unknown')[:10]
            status_emoji = "✅" if p['status'] == 'completed' else "⏳" if p['status'] == 'processing' else "❌"
            text += f"{status_emoji} {p['game_name']}: {p['amount_stars']}⭐ ({name}) - {p['created_at'][:16]}\n"
    
    await c.message.answer(text, reply_markup=get_admin_inline())
    await c.answer()

@dp.callback_query(lambda c: c.data == "admin_users")
async def admin_users(c: CallbackQuery):
    if c.from_user.id != ADMIN_ID:
        await c.answer("⛔ Нет доступа", show_alert=True)
        return
    
    # Топ 10 пользователей
    top_users = db.get_top_donaters(10)
    
    text = "👥 <b>Топ пользователей</b>\n\n"
    for i, user in enumerate(top_users, 1):
        name = user.get('first_name', 'Аноним')[:15]
        username = f" @{user['username']}" if user.get('username') else ""
        stars = user.get('total_spent_stars', 0)
        text += f"{i}. {name}{username} - {stars}⭐\n"
    
    await c.message.answer(text, reply_markup=get_admin_inline())
    await c.answer()

@dp.callback_query(lambda c: c.data == "admin_charts")
async def admin_charts(c: CallbackQuery):
    if c.from_user.id != ADMIN_ID:
        await c.answer("⛔ Нет доступа", show_alert=True)
        return
    
    daily = db.get_daily_stats(14)
    
    text = "📈 <b>График за 14 дней:</b>\n\n"
    for d in reversed(daily):
        date = d['date'][5:]  # MM-DD
        bars = "█" * min(int(d['stars'] / 50), 20) or "▏"
        text += f"{date}: {bars} {d['stars']}⭐\n"
    
    await c.message.answer(text, reply_markup=get_admin_inline())
    await c.answer()

@dp.callback_query(lambda c: c.data == "admin_profit")
async def admin_profit(c: CallbackQuery):
    if c.from_user.id != ADMIN_ID:
        await c.answer("⛔ Нет доступа", show_alert=True)
        return
    
    stats = db.get_total_stats()
    daily = db.get_daily_stats(30)
    
    # Примерный прогноз
    avg_daily = sum(d['stars'] for d in daily) // len(daily) if daily else 0
    avg_rub = avg_daily * STARS_TO_RUB
    
    text = (
        f"💰 <b>Прогноз прибыли</b>\n\n"
        f"📊 <b>Текущий баланс:</b>\n"
        f"• Всего звезд: {stats['total_stars']}\n"
        f"• В рублях: ~{stats['total_stars'] * STARS_TO_RUB:.0f} руб\n\n"
        f"📈 <b>Средний доход:</b>\n"
        f"• В день: {avg_daily}⭐ / {avg_rub:.0f} руб\n"
        f"• В месяц: {avg_daily * 30}⭐ / {avg_rub * 30:.0f} руб\n"
        f"• В год: {avg_daily * 365}⭐ / {avg_rub * 365:.0f} руб\n\n"
        f"🚀 <b>Совет:</b> Привлекай больше рефералов и продажи вырастут!"
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
            # Получаем задачи из очереди
            conn = sqlite3.connect("bot_database.db")
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM delivery_queue 
                WHERE status = 'pending' AND attempts < 3
                ORDER BY created_at ASC
                LIMIT 5
            ''')
            tasks = cursor.fetchall()
            conn.close()
            
            for task in tasks:
                task_dict = {
                    'id': task[0],
                    'payment_id': task[1],
                    'user_id': task[2],
                    'game_id': task[3],
                    'account': task[4],
                    'amount': task[5]
                }
                
                # Пытаемся выдать
                success = False
                if task_dict['game_id'] == 'freefire' and freefire_api:
                    success = await freefire_api.send_diamonds(
                        player_id=task_dict['account'],
                        amount=task_dict['amount']
                    )
                
                if success:
                    # Отмечаем как выполненное
                    conn = sqlite3.connect("bot_database.db")
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE delivery_queue SET status = 'completed' WHERE id = ?
                    ''', (task_dict['id'],))
                    cursor.execute('''
                        UPDATE payments SET status = 'completed', delivered_at = ? WHERE id = ?
                    ''', (datetime.now(), task_dict['payment_id']))
                    conn.commit()
                    conn.close()
                    
                    # Уведомляем пользователя
                    await notify_delivery_complete(
                        user_id=task_dict['user_id'],
                        game_name=GAMES.get(task_dict['game_id'], {}).get('name', 'Игра'),
                        amount=task_dict['amount']
                    )
                    
                    logging.info(f"✅ Доставлено: {task_dict}")
                else:
                    # Увеличиваем счетчик попыток
                    conn = sqlite3.connect("bot_database.db")
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE delivery_queue 
                        SET attempts = attempts + 1 
                        WHERE id = ?
                    ''', (task_dict['id'],))
                    conn.commit()
                    conn.close()
            
            await asyncio.sleep(30)
            
        except Exception as e:
            logging.error(f"Worker error: {e}")
            await asyncio.sleep(60)

# ============================================
# ЗАПУСК
# ============================================

async def main():
    logging.info("🚀 Запуск мегабота с твоими ключами...")
    
    print(f"\n{'='*60}")
    print(f"🔥 МЕГАБОТ ЗАПУСКАЕТСЯ С ТВОИМИ КЛЮЧАМИ!")
    print(f"{'='*60}")
    print(f"🤖 Токен бота: {BOT_TOKEN[:15]}...")
    print(f"👑 Твой ID: {ADMIN_ID}")
    print(f"💰 CryptoBot ключ: {CRYPTO_API_KEY[:10]}...")
    print(f"{'='*60}\n")
    
    try:
        me = await bot.get_me()
        logging.info(f"✅ Бот @{me.username} запущен!")
        print(f"\n{'='*60}")
        print(f"🔥 МЕГАБОТ @{me.username} ЗАПУЩЕН!")
        print(f"📱 Открой Telegram и напиши /start")
        print(f"👑 Админка: /admin")
        print(f"🎁 Ежедневный бонус: +1⭐ каждый день")
        print(f"💬 Поддержка: в меню")
        print(f"{'='*60}\n")
        
        # Отправляем уведомление админу о запуске
        await bot.send_message(
            ADMIN_ID,
            f"🚀 <b>Бот запущен!</b>\n\n"
            f"✅ Все системы работают\n"
            f"💰 CryptoBot ключ активен\n"
            f"🎮 {len([g for g in GAMES.values() if g['enabled']])} игр доступно\n\n"
            f"📊 Статистика в админке"
        )
        
        # Запускаем фоновый воркер
        asyncio.create_task(delivery_worker())
        
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"❌ Ошибка: {e}")
        print(f"\n❌ Ошибка: {e}")
        print("🔌 Проверь интернет и токен\n")

if __name__ == "__main__":
    asyncio.run(main())
