#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════╗
║              P2P ГЕЙМИНГ МАРКЕТПЛЕЙС 4.0                       ║
║         С ЗАМОРОЗКОЙ ДЕНЕГ, ОТЗЫВАМИ И ПЛАТЕЖАМИ              ║
║                    🎮 + 💰 = 🔥 + 🔒                           ║
╚═══════════════════════════════════════════════════════════════╝
"""

import os
import sys
import sqlite3
import logging
import asyncio
import random
import string
import json
import aiohttp
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

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
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ============================================
# ТВОИ ДАННЫЕ (ВСТАВЬ СВОИ)
# ============================================

BOT_TOKEN = "8339352233:AAGixj9izEbOVKHvhpKeTd_4_Y2CP-f-ZhE"
ADMIN_ID = 2091630272

# ============================================
# НАСТРОЙКИ ПЛАТФОРМЫ
# ============================================

COMMISSION = 1.0  # Комиссия бота (%)
ESCROW_TIME = 60  # Время на оплату (минут)
MIN_AMOUNT = 100  # Минимальная сумма сделки (руб)
MAX_AMOUNT = 100000  # Максимальная сумма сделки (руб)
REFERRAL_BONUS = 10  # Бонус рефереру (%)
SUPPORT_USERNAME = "@GhostiPeeK_2"  # Юзернейм саппорта
CHANNEL_ID = 1003664296821  # ID твоего канала для ордеров (ЗАМЕНИ НА СВОЙ!)

# ============================================
# ПЛАТЁЖНЫЕ СИСТЕМЫ
# ============================================

# ЮKassa (для карт)
YOOKASSA_SHOP_ID = "000000"
YOOKASSA_SECRET_KEY = "test_00000000000000000000000000000000"
# CryptoBot (для крипты)
CRYPTO_API_KEY = "540261:AAzd4sQW2mo4I8UdxardSygAc3H3CSZbZBs"  # Получи в @CryptoBot

# Telegram Stars (встроенные)
STARS_ENABLED = True
STARS_TO_RUB = 1.79

# ============================================
# ИГРЫ
# ============================================

GAMES = [
    {"id": "pubg", "name": "PUBG Mobile", "currency": "UC", "icon": "🪖"},
    {"id": "brawl", "name": "Brawl Stars", "currency": "гемы", "icon": "🥊"},
    {"id": "freefire", "name": "Free Fire", "currency": "алмазы", "icon": "🔥"},
    {"id": "steam", "name": "Steam", "currency": "руб", "icon": "🎮"},
    {"id": "genshin", "name": "Genshin Impact", "currency": "кристаллы", "icon": "✨"},
    {"id": "cod", "name": "Call of Duty", "currency": "CP", "icon": "🔫"},
    {"id": "roblox", "name": "Roblox", "currency": "Robux", "icon": "🎲"},
    {"id": "fortnite", "name": "Fortnite", "currency": "V-bucks", "icon": "🛡️"},
]

# ============================================
# КРИПТОВАЛЮТЫ
# ============================================

CRYPTO = [
    {"id": "usdt", "name": "USDT", "network": "TRC20", "icon": "💵"},
    {"id": "ton", "name": "TON", "network": "TON", "icon": "💎"},
    {"id": "btc", "name": "Bitcoin", "network": "BTC", "icon": "₿"},
]

# ============================================
# FSM СОСТОЯНИЯ
# ============================================

class OrderStates(StatesGroup):
    choosing_market = State()
    choosing_item = State()
    choosing_type = State()
    entering_amount = State()
    entering_price = State()
    entering_comment = State()
    choosing_payment = State()
    confirming = State()

class TradeStates(StatesGroup):
    entering_amount = State()
    waiting_payment = State()
    waiting_confirmation = State()
    waiting_review = State()

class DepositStates(StatesGroup):
    choosing_amount = State()
    choosing_method = State()
    waiting_payment = State()

# ============================================
# БАЗА ДАННЫХ С БЕЗОПАСНОСТЬЮ
# ============================================

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('p2p_secure.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()
    
    def create_tables(self):
        # Пользователи с балансами
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                registered_at TEXT,
                referrer_id INTEGER,
                referral_code TEXT UNIQUE,
                rating REAL DEFAULT 5.0,
                deals_count INTEGER DEFAULT 0,
                successful_deals INTEGER DEFAULT 0,
                balance REAL DEFAULT 0,  # Доступные рубли
                locked_balance REAL DEFAULT 0,  # Замороженные рубли
                crypto_balance TEXT DEFAULT '{}',  # JSON с балансами крипты
                is_verified BOOLEAN DEFAULT 0,
                is_banned BOOLEAN DEFAULT 0,
                last_active TEXT
            )
        ''')
        
        # Ордера
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                market_type TEXT,
                item_id TEXT,
                item_name TEXT,
                item_icon TEXT,
                order_type TEXT,
                amount REAL,
                price REAL,
                total REAL,
                min_amount REAL,
                comment TEXT,
                payment_method TEXT,
                status TEXT DEFAULT 'active',
                created_at TEXT,
                views INTEGER DEFAULT 0,
                favorites INTEGER DEFAULT 0
            )
        ''')
        
        # Сделки с эскроу
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                seller_id INTEGER,
                buyer_id INTEGER,
                amount REAL,
                price REAL,
                total REAL,
                commission REAL,
                escrow_status TEXT DEFAULT 'pending',  # 'pending', 'locked', 'released', 'disputed'
                payment_status TEXT DEFAULT 'waiting',  # 'waiting', 'paid', 'confirmed'
                created_at TEXT,
                expires_at TEXT,
                completed_at TEXT,
                dispute_reason TEXT,
                dispute_resolved_by INTEGER
            )
        ''')
        
        # Платежи (пополнения/выводы)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT,  # 'deposit', 'withdraw'
                amount REAL,
                currency TEXT,
                method TEXT,  # 'card', 'crypto', 'stars', 'sbp'
                status TEXT DEFAULT 'pending',  # 'pending', 'success', 'failed'
                payment_id TEXT UNIQUE,
                created_at TEXT,
                completed_at TEXT
            )
        ''')
        
        # Отзывы
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id INTEGER,
                from_user_id INTEGER,
                to_user_id INTEGER,
                rating INTEGER CHECK(rating >= 1 AND rating <= 5),
                comment TEXT,
                created_at TEXT,
                FOREIGN KEY (trade_id) REFERENCES trades(id)
            )
        ''')
        
        # Избранное
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS favorites (
                user_id INTEGER,
                order_id INTEGER,
                created_at TEXT,
                PRIMARY KEY (user_id, order_id)
            )
        ''')
        
        self.conn.commit()
    
    # ========== УПРАВЛЕНИЕ БАЛАНСАМИ ==========
    
    def get_balance(self, user_id):
        """Получает баланс пользователя"""
        self.cursor.execute('SELECT balance, locked_balance, crypto_balance FROM users WHERE user_id = ?', (user_id,))
        row = self.cursor.fetchone()
        if row:
            return {
                'balance': row[0],
                'locked': row[1],
                'crypto': json.loads(row[2]) if row[2] else {}
            }
        return {'balance': 0, 'locked': 0, 'crypto': {}}
    
    def add_balance(self, user_id, amount):
        """Добавляет рубли на баланс"""
        self.cursor.execute('''
            UPDATE users SET balance = balance + ? WHERE user_id = ?
        ''', (amount, user_id))
        self.conn.commit()
    
    def lock_funds(self, user_id, amount):
        """Замораживает рубли у пользователя"""
        self.cursor.execute('''
            UPDATE users 
            SET balance = balance - ?,
                locked_balance = locked_balance + ?
            WHERE user_id = ? AND balance >= ?
        ''', (amount, amount, user_id, amount))
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def release_funds(self, user_id, amount):
        """Размораживает рубли"""
        self.cursor.execute('''
            UPDATE users 
            SET locked_balance = locked_balance - ?
            WHERE user_id = ? AND locked_balance >= ?
        ''', (amount, user_id, amount))
        self.conn.commit()
    
    def transfer_funds(self, from_id, to_id, amount, commission):
        """Переводит рубли от одного пользователя другому (с комиссией)"""
        # Размораживаем у покупателя
        self.cursor.execute('''
            UPDATE users 
            SET locked_balance = locked_balance - ?
            WHERE user_id = ? AND locked_balance >= ?
        ''', (amount, from_id, amount))
        
        # Начисляем продавцу (минус комиссия)
        self.cursor.execute('''
            UPDATE users 
            SET balance = balance + ?
            WHERE user_id = ?
        ''', (amount - commission, to_id))
        
        # Начисляем комиссию админу
        self.cursor.execute('''
            UPDATE users 
            SET balance = balance + ?
            WHERE user_id = ?
        ''', (commission, ADMIN_ID))
        
        self.conn.commit()
    
    # ========== ПОЛЬЗОВАТЕЛИ ==========
    
    def add_user(self, user_id, username, first_name, referrer_code=None):
        self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        if self.cursor.fetchone():
            return
        
        ref_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        referrer_id = None
        if referrer_code:
            self.cursor.execute('SELECT user_id FROM users WHERE referral_code = ?', (referrer_code,))
            res = self.cursor.fetchone()
            if res:
                referrer_id = res[0]
        
        self.cursor.execute('''
            INSERT INTO users 
            (user_id, username, first_name, registered_at, referrer_id, referral_code, last_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, username, first_name, 
            datetime.now().isoformat(), 
            referrer_id, ref_code,
            datetime.now().isoformat()
        ))
        
        self.conn.commit()
        return ref_code
    
    def get_user(self, user_id):
        self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        row = self.cursor.fetchone()
        if row:
            return {
                'user_id': row[0],
                'username': row[1],
                'first_name': row[2],
                'registered_at': row[3],
                'referrer_id': row[4],
                'referral_code': row[5],
                'rating': row[6],
                'deals_count': row[7],
                'successful_deals': row[8],
                'balance': row[9],
                'locked_balance': row[10],
                'crypto_balance': json.loads(row[11]) if row[11] else {},
                'is_verified': row[12],
                'is_banned': row[13],
                'last_active': row[14]
            }
        return None
    
    # ========== ОРДЕРА ==========
    
    def create_order(self, user_id, market_type, item, order_type, amount, price, comment, payment_method):
        total = amount * price
        min_amount = MIN_AMOUNT / price
        
        self.cursor.execute('''
            INSERT INTO orders 
            (user_id, market_type, item_id, item_name, item_icon, order_type, 
             amount, price, total, min_amount, comment, payment_method, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, 
            market_type, 
            item['id'], 
            item['name'], 
            item['icon'], 
            order_type, 
            amount, 
            price, 
            total, 
            min_amount,
            comment, 
            payment_method,
            datetime.now().isoformat()
        ))
        
        order_id = self.cursor.lastrowid
        self.conn.commit()
        return order_id
    
    def get_orders(self, market_type=None, item_id=None, status='active', limit=50):
        query = 'SELECT * FROM orders WHERE status = ?'
        params = [status]
        
        if market_type:
            query += ' AND market_type = ?'
            params.append(market_type)
        
        if item_id:
            query += ' AND item_id = ?'
            params.append(item_id)
        
        query += ' ORDER BY created_at DESC LIMIT ?'
        params.append(limit)
        
        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()
        
        orders = []
        for row in rows:
            orders.append({
                'id': row[0],
                'user_id': row[1],
                'market_type': row[2],
                'item_id': row[3],
                'item_name': row[4],
                'item_icon': row[5],
                'order_type': row[6],
                'amount': row[7],
                'price': row[8],
                'total': row[9],
                'min_amount': row[10],
                'comment': row[11],
                'payment_method': row[12],
                'status': row[13],
                'created_at': row[14],
                'views': row[15],
                'favorites': row[16]
            })
        return orders
    
    def get_order(self, order_id):
        self.cursor.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
        row = self.cursor.fetchone()
        if row:
            self.cursor.execute('UPDATE orders SET views = views + 1 WHERE id = ?', (order_id,))
            self.conn.commit()
            
            return {
                'id': row[0],
                'user_id': row[1],
                'market_type': row[2],
                'item_id': row[3],
                'item_name': row[4],
                'item_icon': row[5],
                'order_type': row[6],
                'amount': row[7],
                'price': row[8],
                'total': row[9],
                'min_amount': row[10],
                'comment': row[11],
                'payment_method': row[12],
                'status': row[13],
                'created_at': row[14],
                'views': row[15],
                'favorites': row[16]
            }
        return None
    
    def update_order_amount(self, order_id, new_amount):
        if new_amount <= 0:
            self.cursor.execute('UPDATE orders SET status = "completed" WHERE id = ?', (order_id,))
        else:
            self.cursor.execute('UPDATE orders SET amount = ? WHERE id = ?', (new_amount, order_id))
        self.conn.commit()
    
    # ========== СДЕЛКИ С ЭСКРОУ ==========
    
    def create_secure_trade(self, order_id, buyer_id, amount):
        """Создаёт сделку с заморозкой денег"""
        order = self.get_order(order_id)
        if not order or order['status'] != 'active':
            return None
        
        if amount < order['min_amount'] or amount > order['amount']:
            return None
        
        total = amount * order['price']
        commission = total * (COMMISSION / 100)
        
        # Проверяем баланс покупателя
        buyer = self.get_user(buyer_id)
        if not buyer or buyer['balance'] < total:
            return None
        
        # Замораживаем рубли у покупателя
        self.cursor.execute('''
            UPDATE users 
            SET balance = balance - ?,
                locked_balance = locked_balance + ?
            WHERE user_id = ? AND balance >= ?
        ''', (total, total, buyer_id, total))
        
        if self.cursor.rowcount == 0:
            return None
        
        # Создаём сделку
        self.cursor.execute('''
            INSERT INTO trades 
            (order_id, seller_id, buyer_id, amount, price, total, commission, 
             escrow_status, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'locked', ?, ?)
        ''', (
            order_id, order['user_id'], buyer_id, amount, order['price'], 
            total, commission, datetime.now().isoformat(),
            (datetime.now() + timedelta(minutes=ESCROW_TIME)).isoformat()
        ))
        
        trade_id = self.cursor.lastrowid
        
        # Обновляем ордер
        new_amount = order['amount'] - amount
        self.update_order_amount(order_id, new_amount)
        
        self.conn.commit()
        return trade_id
    
    def get_trade(self, trade_id):
        self.cursor.execute('SELECT * FROM trades WHERE id = ?', (trade_id,))
        row = self.cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'order_id': row[1],
                'seller_id': row[2],
                'buyer_id': row[3],
                'amount': row[4],
                'price': row[5],
                'total': row[6],
                'commission': row[7],
                'escrow_status': row[8],
                'payment_status': row[9],
                'created_at': row[10],
                'expires_at': row[11],
                'completed_at': row[12],
                'dispute_reason': row[13],
                'dispute_resolved_by': row[14]
            }
        return None
    
    def get_user_trades(self, user_id, limit=20):
        self.cursor.execute('''
            SELECT * FROM trades 
            WHERE seller_id = ? OR buyer_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, user_id, limit))
        
        rows = self.cursor.fetchall()
        trades = []
        for row in rows:
            trades.append({
                'id': row[0],
                'order_id': row[1],
                'seller_id': row[2],
                'buyer_id': row[3],
                'amount': row[4],
                'total': row[6],
                'escrow_status': row[8],
                'payment_status': row[9],
                'created_at': row[10]
            })
        return trades
    
    def confirm_payment(self, trade_id):
        """Покупатель подтверждает оплату"""
        self.cursor.execute('''
            UPDATE trades SET payment_status = 'paid' WHERE id = ?
        ''', (trade_id,))
        self.conn.commit()
    
    def complete_trade(self, trade_id):
        """Продавец подтверждает получение денег"""
        trade = self.get_trade(trade_id)
        if not trade:
            return False
        
        # Переводим деньги продавцу (с комиссией)
        self.cursor.execute('''
            UPDATE users 
            SET locked_balance = locked_balance - ?,
                balance = balance + ?
            WHERE user_id = ?
        ''', (trade['total'], trade['total'] - trade['commission'], trade['seller_id']))
        
        # Комиссия админу
        self.cursor.execute('''
            UPDATE users 
            SET balance = balance + ?
            WHERE user_id = ?
        ''', (trade['commission'], ADMIN_ID))
        
        # Обновляем сделку
        self.cursor.execute('''
            UPDATE trades 
            SET escrow_status = 'released', 
                payment_status = 'confirmed',
                completed_at = ? 
            WHERE id = ?
        ''', (datetime.now().isoformat(), trade_id))
        
        # Обновляем статистику
        self.cursor.execute('''
            UPDATE users 
            SET deals_count = deals_count + 1,
                successful_deals = successful_deals + 1
            WHERE user_id IN (?, ?)
        ''', (trade['seller_id'], trade['buyer_id']))
        
        self.conn.commit()
        return True
    
    def cancel_trade(self, trade_id):
        """Отмена сделки (возврат денег)"""
        trade = self.get_trade(trade_id)
        if not trade:
            return False
        
        # Возвращаем деньги покупателю
        self.cursor.execute('''
            UPDATE users 
            SET locked_balance = locked_balance - ?,
                balance = balance + ?
            WHERE user_id = ?
        ''', (trade['total'], trade['total'], trade['buyer_id']))
        
        # Возвращаем товар продавцу (обновляем ордер)
        order = self.get_order(trade['order_id'])
        if order:
            new_amount = order['amount'] + trade['amount']
            self.cursor.execute('''
                UPDATE orders SET amount = ?, status = 'active' WHERE id = ?
            ''', (new_amount, trade['order_id']))
        
        self.cursor.execute('''
            UPDATE trades SET escrow_status = 'cancelled' WHERE id = ?
        ''', (trade_id,))
        
        self.conn.commit()
        return True
    
    # ========== ОТЗЫВЫ ==========
    
    def add_review(self, trade_id, from_id, to_id, rating, comment):
        self.cursor.execute('''
            INSERT INTO reviews (trade_id, from_user_id, to_user_id, rating, comment, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (trade_id, from_id, to_id, rating, comment, datetime.now().isoformat()))
        
        # Пересчитываем средний рейтинг
        self.cursor.execute('''
            SELECT AVG(rating) as avg_rating FROM reviews WHERE to_user_id = ?
        ''', (to_id,))
        avg = self.cursor.fetchone()[0]
        
        self.cursor.execute('''
            UPDATE users SET rating = ? WHERE user_id = ?
        ''', (avg, to_id))
        
        self.conn.commit()
    
    def get_user_reviews(self, user_id, limit=10):
        self.cursor.execute('''
            SELECT * FROM reviews WHERE to_user_id = ? ORDER BY created_at DESC LIMIT ?
        ''', (user_id, limit))
        rows = self.cursor.fetchall()
        reviews = []
        for row in rows:
            reviews.append({
                'id': row[0],
                'trade_id': row[1],
                'from_id': row[2],
                'to_id': row[3],
                'rating': row[4],
                'comment': row[5],
                'created_at': row[6]
            })
        return reviews
    
    # ========== ПЛАТЕЖИ ==========
    
    def add_payment(self, user_id, type, amount, currency, method, payment_id):
        self.cursor.execute('''
            INSERT INTO payments (user_id, type, amount, currency, method, payment_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, type, amount, currency, method, payment_id, datetime.now().isoformat()))
        
        payment_db_id = self.cursor.lastrowid
        self.conn.commit()
        return payment_db_id
    
    def confirm_payment_db(self, payment_id):
        self.cursor.execute('''
            UPDATE payments SET status = 'success', completed_at = ? WHERE payment_id = ?
        ''', (datetime.now().isoformat(), payment_id))
        self.conn.commit()
    
    # ========== ИЗБРАННОЕ ==========
    
    def add_favorite(self, user_id, order_id):
        self.cursor.execute('''
            INSERT OR IGNORE INTO favorites (user_id, order_id, created_at)
            VALUES (?, ?, ?)
        ''', (user_id, order_id, datetime.now().isoformat()))
        self.conn.commit()
    
    def remove_favorite(self, user_id, order_id):
        self.cursor.execute('DELETE FROM favorites WHERE user_id = ? AND order_id = ?', (user_id, order_id))
        self.conn.commit()
    
    def get_favorites(self, user_id):
        self.cursor.execute('SELECT order_id FROM favorites WHERE user_id = ?', (user_id,))
        rows = self.cursor.fetchall()
        return [row[0] for row in rows]

db = Database()

# ============================================
# ПЛАТЁЖНЫЕ СИСТЕМЫ
# ============================================

class PaymentProcessor:
    """Обработчик платежей"""
    
    @staticmethod
    async def create_yookassa_payment(amount, description):
        """Создаёт платёж через ЮKassa"""
        try:
            import yookassa
            yookassa.Configuration.account_id = YOOKASSA_SHOP_ID
            yookassa.Configuration.secret_key = YOOKASSA_SECRET_KEY
            
            payment = yookassa.Payment.create({
                "amount": {
                    "value": f"{amount:.2f}",
                    "currency": "RUB"
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": "https://t.me/GhostiPeeKPaY_bot"
                },
                "capture": True,
                "description": description
            })
            
            return payment.confirmation.confirmation_url, payment.id
        except Exception as e:
            logging.error(f"YooKassa error: {e}")
            return None, None
    
    @staticmethod
    async def create_crypto_invoice(amount, currency, description):
        """Создаёт счёт в CryptoBot"""
        try:
            url = "https://pay.crypt.bot/api/createInvoice"
            headers = {"Crypto-Pay-API-Key": CRYPTO_API_KEY}
            data = {
                "asset": currency,
                "amount": str(amount),
                "description": description,
                "paid_btn_name": "openBot",
                "paid_btn_url": "https://t.me/GhostiPeeKPaY_bot",
                "expires_in": 3600
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as resp:
                    result = await resp.json()
                    if result.get("ok"):
                        return result["result"]["pay_url"], result["result"]["invoice_id"]
            return None, None
        except Exception as e:
            logging.error(f"CryptoBot error: {e}")
            return None, None

# ============================================
# БОТ
# ============================================

storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=storage)

# ============================================
# КЛАВИАТУРЫ
# ============================================

def main_keyboard():
    builder = ReplyKeyboardBuilder()
    buttons = [
        KeyboardButton(text="🎮 ИГРЫ"),
        KeyboardButton(text="💰 КРИПТА"),
        KeyboardButton(text="👤 ПРОФИЛЬ"),
        KeyboardButton(text="💰 ПОПОЛНИТЬ"),
        KeyboardButton(text="📤 ВЫВЕСТИ"),
        KeyboardButton(text="❓ ПОМОЩЬ")
    ]
    builder.add(*buttons)
    builder.adjust(2, 2, 2)
    return builder.as_markup(resize_keyboard=True)

def games_keyboard():
    builder = InlineKeyboardBuilder()
    for game in GAMES:
        builder.button(text=f"{game['icon']} {game['name']}", callback_data=f"game_{game['id']}")
    builder.adjust(2)
    builder.row(
        InlineKeyboardButton(text="➕ СОЗДАТЬ ОРДЕР", callback_data="create_game"),
        InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu")
    )
    return builder.as_markup()

def crypto_keyboard():
    builder = InlineKeyboardBuilder()
    for crypto in CRYPTO:
        builder.button(text=f"{crypto['icon']} {crypto['name']}", callback_data=f"crypto_{crypto['id']}")
    builder.adjust(2)
    builder.row(
        InlineKeyboardButton(text="➕ СОЗДАТЬ ОРДЕР", callback_data="create_crypto"),
        InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu")
    )
    return builder.as_markup()

def deposit_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Банковская карта", callback_data="deposit_card")
    builder.button(text="₿ Криптовалюта", callback_data="deposit_crypto")
    if STARS_ENABLED:
        builder.button(text="⭐ Telegram Stars", callback_data="deposit_stars")
    builder.button(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu")
    builder.adjust(2, 1, 1)
    return builder.as_markup()

def amount_keyboard():
    builder = InlineKeyboardBuilder()
    for amount in [100, 500, 1000, 5000, 10000]:
        builder.button(text=f"{amount} ₽", callback_data=f"amount_{amount}")
    builder.adjust(3, 2)
    builder.row(InlineKeyboardButton(text="🔙 НАЗАД", callback_data="back"))
    return builder.as_markup()

def order_type_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📈 ПРОДАТЬ", callback_data="type_sell")
    builder.button(text="📉 КУПИТЬ", callback_data="type_buy")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="❌ ОТМЕНА", callback_data="cancel_order"))
    return builder.as_markup()

def confirm_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ ПОДТВЕРДИТЬ", callback_data="confirm_order")
    builder.button(text="❌ ОТМЕНА", callback_data="cancel_order")
    builder.adjust(2)
    return builder.as_markup()

def cancel_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ ОТМЕНИТЬ", callback_data="cancel_order")
    return builder.as_markup()

def back_keyboard(target="back"):
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 НАЗАД", callback_data=target)
    builder.button(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu")
    builder.adjust(2)
    return builder.as_markup()

def order_actions_keyboard(order_id, is_owner=False, is_favorite=False):
    builder = InlineKeyboardBuilder()
    if not is_owner:
        builder.button(text="💎 КУПИТЬ", callback_data=f"buy_{order_id}")
    if is_favorite:
        builder.button(text="★ В ИЗБРАННОМ", callback_data=f"unfav_{order_id}")
    else:
        builder.button(text="☆ В ИЗБРАННОЕ", callback_data=f"fav_{order_id}")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="🔙 НАЗАД", callback_data="back"))
    return builder.as_markup()

def trade_actions_keyboard(trade_id, user_role):
    builder = InlineKeyboardBuilder()
    if user_role == 'buyer':
        builder.button(text="💳 Я ОПЛАТИЛ", callback_data=f"trade_paid_{trade_id}")
    elif user_role == 'seller':
        builder.button(text="✅ ПОДТВЕРДИТЬ", callback_data=f"trade_confirm_{trade_id}")
    builder.button(text="⚠️ ОТКРЫТЬ СПОР", callback_data=f"trade_dispute_{trade_id}")
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu"))
    return builder.as_markup()

def review_keyboard(trade_id, to_id):
    builder = InlineKeyboardBuilder()
    for i in range(1, 6):
        builder.button(text=f"{i}⭐", callback_data=f"rate_{trade_id}_{to_id}_{i}")
    builder.adjust(5)
    builder.row(InlineKeyboardButton(text="🔙 ПРОПУСТИТЬ", callback_data="skip_review"))
    return builder.as_markup()

def profile_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 МОИ СДЕЛКИ", callback_data="my_trades")
    builder.button(text="📋 МОИ ОРДЕРА", callback_data="my_orders")
    builder.button(text="⭐ ИЗБРАННОЕ", callback_data="my_favorites")
    builder.button(text="📝 МОИ ОТЗЫВЫ", callback_data="my_reviews")
    builder.button(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu")
    builder.adjust(2, 2, 1)
    return builder.as_markup()

# ============================================
# СТАРТ
# ============================================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    user = message.from_user
    args = message.text.split()
    ref_code = args[1] if len(args) > 1 else None
    
    referral_code = db.add_user(user.id, user.username, user.first_name, ref_code)
    
    welcome_text = (
        f"🌟 <b>ДОБРО ПОЖАЛОВАТЬ В БЕЗОПАСНЫЙ P2P МАРКЕТПЛЕЙС!</b> 🌟\n\n"
        f"👋 <b>Привет, {user.first_name}!</b>\n\n"
        f"🔒 <b>Здесь всё безопасно:</b>\n"
        f"├ 💰 Деньги замораживаются на время сделки\n"
        f"├ 🤝 Эскроу-гарант защищает продавца и покупателя\n"
        f"├ ⭐ Рейтинг и отзывы на продавцов\n"
        f"└ 💳 Пополнение картой, криптой и Stars\n\n"
        f"📊 <b>Твоя реферальная ссылка:</b>\n"
        f"<code>https://t.me/{(await bot.get_me()).username}?start={referral_code}</code>\n\n"
        f"👇 <b>Выбери действие:</b>"
    )
    
    await message.answer(welcome_text, reply_markup=main_keyboard())

# ============================================
# ГЛАВНОЕ МЕНЮ
# ============================================

@dp.message(lambda m: m.text == "🎮 ИГРЫ")
async def games_section(message: Message):
    await message.answer("🎮 <b>ИГРОВОЙ МАРКЕТПЛЕЙС</b>\n\nВыбери игру:", reply_markup=games_keyboard())

@dp.message(lambda m: m.text == "💰 КРИПТА")
async def crypto_section(message: Message):
    await message.answer("💰 <b>КРИПТО-БИРЖА</b>\n\nВыбери валюту:", reply_markup=crypto_keyboard())

@dp.message(lambda m: m.text == "👤 ПРОФИЛЬ")
async def profile_section(message: Message):
    user = db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Ошибка загрузки профиля")
        return
    
    balance = db.get_balance(message.from_user.id)
    rating = user['rating']
    stars = "⭐" * int(rating) + ("✨" if rating % 1 >= 0.5 else "")
    
    text = (
        f"👤 <b>ТВОЙ ПРОФИЛЬ</b>\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"├ Сделок: {user['successful_deals']}/{user['deals_count']}\n"
        f"├ Рейтинг: {stars} ({rating:.1f})\n"
        f"└ Верификация: {'✅' if user['is_verified'] else '❌'}\n\n"
        f"💰 <b>Баланс:</b>\n"
        f"├ Доступно: {balance['balance']} ₽\n"
        f"├ Заморожено: {balance['locked']} ₽\n"
        f"└ Всего: {balance['balance'] + balance['locked']} ₽\n\n"
        f"💎 <b>Крипта:</b>\n"
    )
    
    for curr, amount in balance['crypto'].items():
        text += f"├ {curr.upper()}: {amount}\n"
    
    await message.answer(text, reply_markup=profile_keyboard())

@dp.message(lambda m: m.text == "💰 ПОПОЛНИТЬ")
async def deposit_section(message: Message):
    await message.answer(
        "💰 <b>ПОПОЛНЕНИЕ БАЛАНСА</b>\n\n"
        "Выбери способ пополнения:",
        reply_markup=deposit_keyboard()
    )

@dp.message(lambda m: m.text == "📤 ВЫВЕСТИ")
async def withdraw_section(message: Message):
    await message.answer(
        "📤 <b>ВЫВОД СРЕДСТВ</b>\n\n"
        "Минимальная сумма вывода: 100 ₽\n"
        "Комиссия: 2%\n\n"
        "Напиши сумму для вывода:",
        reply_markup=cancel_keyboard()
    )

@dp.message(lambda m: m.text == "❓ ПОМОЩЬ")
async def help_section(message: Message):
    text = (
        "❓ <b>ЦЕНТР ПОМОЩИ</b>\n\n"
        "🔒 <b>Безопасность:</b>\n"
        "• Деньги замораживаются на время сделки\n"
        "• Никто не может их забрать без подтверждения\n"
        "• В случае спора — решает администратор\n\n"
        "📌 <b>Как проходит сделка:</b>\n"
        "1️⃣ Находишь ордер\n"
        "2️⃣ Нажимаешь «Купить» и вводишь количество\n"
        "3️⃣ Бот замораживает деньги на твоём счету\n"
        "4️⃣ Ты переводишь деньги продавцу\n"
        "5️⃣ Продавец подтверждает получение\n"
        "6️⃣ Бот переводит валюту и размораживает деньги\n\n"
        f"⏱ <b>Время на оплату:</b> {ESCROW_TIME} минут\n"
        f"💰 <b>Комиссия:</b> {COMMISSION}%\n\n"
        f"📞 <b>Связь с поддержкой:</b> @{SUPPORT_USERNAME}"
    )
    await message.answer(text, reply_markup=back_keyboard())

# ============================================
# НАВИГАЦИЯ
# ============================================

@dp.callback_query(lambda c: c.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("🏠 <b>ГЛАВНОЕ МЕНЮ</b>", reply_markup=main_keyboard())
    await callback.answer()

@dp.callback_query(lambda c: c.data == "back")
async def back_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("🎮 <b>ИГРОВОЙ МАРКЕТПЛЕЙС</b>", reply_markup=games_keyboard())
    await callback.answer()

@dp.callback_query(lambda c: c.data == "cancel_order")
async def cancel_order_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Действие отменено", reply_markup=games_keyboard())
    await callback.answer()

# ============================================
# ПОПОЛНЕНИЕ БАЛАНСА
# ============================================

@dp.callback_query(lambda c: c.data == "deposit_card")
async def deposit_card(callback: CallbackQuery, state: FSMContext):
    await state.set_state(DepositStates.choosing_amount)
    await callback.message.edit_text(
        "💳 <b>ПОПОЛНЕНИЕ КАРТОЙ</b>\n\n"
        "Выбери сумму:",
        reply_markup=amount_keyboard()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "deposit_crypto")
async def deposit_crypto(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    for crypto in CRYPTO:
        builder.button(text=f"{crypto['icon']} {crypto['name']}", callback_data=f"deposit_crypto_{crypto['id']}")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="🔙 НАЗАД", callback_data="back"))
    
    await callback.message.edit_text(
        "₿ <b>ПОПОЛНЕНИЕ КРИПТОЙ</b>\n\n"
        "Выбери валюту:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "deposit_stars")
async def deposit_stars(callback: CallbackQuery, state: FSMContext):
    await state.set_state(DepositStates.choosing_amount)
    await callback.message.edit_text(
        "⭐ <b>ПОПОЛНЕНИЕ STARS</b>\n\n"
        "Выбери сумму в звёздах:",
        reply_markup=amount_keyboard()
    )
    await callback.answer()

@dp.callback_query(DepositStates.choosing_amount, lambda c: c.data.startswith('amount_'))
async def process_deposit_amount(callback: CallbackQuery, state: FSMContext):
    amount = int(callback.data.replace('amount_', ''))
    await state.update_data(amount=amount)
    
    # Здесь создаётся платёж
    payment_url, payment_id = await PaymentProcessor.create_yookassa_payment(
        amount=amount,
        description=f"Пополнение баланса в P2P боте"
    )
    
    if payment_url:
        db.add_payment(callback.from_user.id, 'deposit', amount, 'RUB', 'card', payment_id)
        
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="💳 ОПЛАТИТЬ", url=payment_url)
        keyboard.button(text="✅ Я ОПЛАТИЛ", callback_data=f"check_payment_{payment_id}")
        keyboard.adjust(1)
        keyboard.row(InlineKeyboardButton(text="🔙 ОТМЕНА", callback_data="main_menu"))
        
        await callback.message.edit_text(
            f"💰 <b>СЧЁТ НА ОПЛАТУ</b>\n\n"
            f"Сумма: {amount} ₽\n\n"
            f"Нажми кнопку для оплаты:",
            reply_markup=keyboard.as_markup()
        )
    else:
        await callback.message.edit_text(
            "❌ Ошибка создания платежа. Попробуй позже.",
            reply_markup=back_keyboard()
        )
    
    await state.clear()
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith('check_payment_'))
async def check_payment(callback: CallbackQuery):
    payment_id = callback.data.replace('check_payment_', '')
    
    # Здесь проверка статуса платежа
    db.confirm_payment_db(payment_id)
    db.add_balance(callback.from_user.id, 100)  # Тестовая сумма
    
    await callback.message.edit_text(
        "✅ <b>БАЛАНС ПОПОЛНЕН!</b>\n\n"
        "Средства зачислены на твой счёт.",
        reply_markup=back_keyboard()
    )
    await callback.answer()

# ============================================
# ПОКАЗ ОРДЕРОВ
# ============================================

@dp.callback_query(lambda c: c.data.startswith('game_'))
async def show_game_orders(callback: CallbackQuery):
    game_id = callback.data.replace('game_', '')
    game = next((g for g in GAMES if g['id'] == game_id), None)
    if not game:
        await callback.answer("❌ Игра не найдена")
        return
    
    orders = db.get_orders(market_type='game', item_id=game_id)
    
    if not orders:
        await callback.message.edit_text(
            f"{game['icon']} <b>{game['name']}</b>\n\n😕 Пока нет активных ордеров.",
            reply_markup=back_keyboard()
        )
        await callback.answer()
        return
    
    text = f"{game['icon']} <b>{game['name']} - ОРДЕРА:</b>\n\n"
    builder = InlineKeyboardBuilder()
    
    for order in orders[:5]:
        emoji = "📈" if order['order_type'] == 'sell' else "📉"
        text += f"{emoji} {order['amount']:.0f} {game['currency']} × {order['price']}₽ = {order['total']:.0f}₽\n"
        builder.button(text=f"{order['amount']:.0f} {game['currency']}", callback_data=f"view_order_{order['id']}")
    
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="🔙 НАЗАД", callback_data="back"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith('crypto_'))
async def show_crypto_orders(callback: CallbackQuery):
    crypto_id = callback.data.replace('crypto_', '')
    crypto = next((c for c in CRYPTO if c['id'] == crypto_id), None)
    if not crypto:
        await callback.answer("❌ Валюта не найдена")
        return
    
    orders = db.get_orders(market_type='crypto', item_id=crypto_id)
    
    if not orders:
        await callback.message.edit_text(
            f"{crypto['icon']} <b>{crypto['name']}</b>\n\n😕 Пока нет активных ордеров.",
            reply_markup=back_keyboard()
        )
        await callback.answer()
        return
    
    text = f"{crypto['icon']} <b>{crypto['name']} - ОРДЕРА:</b>\n\n"
    builder = InlineKeyboardBuilder()
    
    for order in orders[:5]:
        emoji = "📈" if order['order_type'] == 'sell' else "📉"
        text += f"{emoji} {order['amount']} {crypto_id.upper()} × {order['price']}₽ = {order['total']:.0f}₽\n"
        builder.button(text=f"{order['amount']} {crypto_id.upper()}", callback_data=f"view_order_{order['id']}")
    
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="🔙 НАЗАД", callback_data="back"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith('view_order_'))
async def view_order(callback: CallbackQuery):
    order_id = int(callback.data.replace('view_order_', ''))
    order = db.get_order(order_id)
    if not order:
        await callback.answer("❌ Ордер не найден", show_alert=True)
        return
    
    user = db.get_user(callback.from_user.id)
    favorites = db.get_favorites(callback.from_user.id) if user else []
    is_owner = (order['user_id'] == callback.from_user.id)
    is_favorite = order_id in favorites
    
    emoji = "📈" if order['order_type'] == 'sell' else "📉"
    type_text = "ПРОДАЖА" if order['order_type'] == 'sell' else "ПОКУПКА"
    
    text = (
        f"{order['item_icon']} <b>{order['item_name']}</b>\n"
        f"{emoji} <b>{type_text}</b>\n\n"
        f"💰 <b>Количество:</b> {order['amount']}\n"
        f"💵 <b>Цена:</b> {order['price']} ₽\n"
        f"💎 <b>Сумма:</b> {order['total']} ₽\n"
    )
    
    if order['comment']:
        text += f"\n📝 <b>Комментарий:</b>\n{order['comment']}\n"
    
    seller = db.get_user(order['user_id'])
    if seller:
        rating = seller['rating']
        stars = "⭐" * int(rating) + ("✨" if rating % 1 >= 0.5 else "")
        text += f"\n👤 <b>Продавец:</b> {seller['first_name']} {stars}\n"
    
    text += f"\n🕐 <b>Создан:</b> {order['created_at'][:16]}"
    
    await callback.message.edit_text(text, reply_markup=order_actions_keyboard(order_id, is_owner, is_favorite))
    await callback.answer()

# ============================================
# ИЗБРАННОЕ
# ============================================

@dp.callback_query(lambda c: c.data.startswith('fav_'))
async def add_favorite(callback: CallbackQuery):
    order_id = int(callback.data.replace('fav_', ''))
    db.add_favorite(callback.from_user.id, order_id)
    await callback.answer("⭐ Добавлено в избранное!", show_alert=True)
    await view_order(callback)

@dp.callback_query(lambda c: c.data.startswith('unfav_'))
async def remove_favorite(callback: CallbackQuery):
    order_id = int(callback.data.replace('unfav_', ''))
    db.remove_favorite(callback.from_user.id, order_id)
    await callback.answer("☆ Убрано из избранного", show_alert=True)
    await view_order(callback)

@dp.callback_query(lambda c: c.data == "my_favorites")
async def my_favorites(callback: CallbackQuery):
    favorites = db.get_favorites(callback.from_user.id)
    if not favorites:
        await callback.message.edit_text(
            "⭐ <b>ИЗБРАННОЕ</b>\n\nУ тебя пока нет избранных ордеров.",
            reply_markup=back_keyboard()
        )
        await callback.answer()
        return
    
    text = "⭐ <b>ТВОИ ИЗБРАННЫЕ ОРДЕРА:</b>\n\n"
    builder = InlineKeyboardBuilder()
    
    for order_id in favorites[:5]:
        order = db.get_order(order_id)
        if order:
            text += f"{order['item_icon']} {order['item_name']} — {order['amount']} | {order['total']}₽\n"
            builder.button(text=f"📋 Ордер #{order_id}", callback_data=f"view_order_{order_id}")
    
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="🔙 НАЗАД", callback_data="back"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

# ============================================
# СОЗДАНИЕ ОРДЕРА
# ============================================

@dp.callback_query(lambda c: c.data == "create_game")
async def create_game_start(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    for game in GAMES:
        builder.button(text=f"{game['icon']} {game['name']}", callback_data=f"create_game_{game['id']}")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="❌ ОТМЕНА", callback_data="cancel_order"))
    
    await callback.message.edit_text("🎮 <b>Выбери игру:</b>", reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(lambda c: c.data == "create_crypto")
async def create_crypto_start(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    for crypto in CRYPTO:
        builder.button(text=f"{crypto['icon']} {crypto['name']}", callback_data=f"create_crypto_{crypto['id']}")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="❌ ОТМЕНА", callback_data="cancel_order"))
    
    await callback.message.edit_text("💰 <b>Выбери валюту:</b>", reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith('create_game_'))
async def create_game_order(callback: CallbackQuery, state: FSMContext):
    game_id = callback.data.replace('create_game_', '')
    game = next((g for g in GAMES if g['id'] == game_id), None)
    if not game:
        await callback.answer("❌ Игра не найдена")
        return
    
    await state.update_data(market_type='game', item=game, item_id=game_id, item_name=game['name'], item_icon=game['icon'])
    await state.set_state(OrderStates.choosing_type)
    await callback.message.edit_text(f"{game['icon']} <b>{game['name']}</b>\n\nТы хочешь продать или купить?", reply_markup=order_type_keyboard())
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith('create_crypto_'))
async def create_crypto_order(callback: CallbackQuery, state: FSMContext):
    crypto_id = callback.data.replace('create_crypto_', '')
    crypto = next((c for c in CRYPTO if c['id'] == crypto_id), None)
    if not crypto:
        await callback.answer("❌ Валюта не найдена")
        return
    
    await state.update_data(market_type='crypto', item=crypto, item_id=crypto_id, item_name=crypto['name'], item_icon=crypto['icon'])
    await state.set_state(OrderStates.choosing_type)
    await callback.message.edit_text(f"{crypto['icon']} <b>{crypto['name']}</b>\n\nТы хочешь продать или купить?", reply_markup=order_type_keyboard())
    await callback.answer()

@dp.callback_query(OrderStates.choosing_type, lambda c: c.data.startswith('type_'))
async def process_order_type(callback: CallbackQuery, state: FSMContext):
    order_type = callback.data.replace('type_', '')
    await state.update_data(order_type=order_type)
    await state.set_state(OrderStates.entering_amount)
    await callback.message.edit_text("💰 <b>ВВЕДИ КОЛИЧЕСТВО:</b>\n\nОтправь число (например: 100)", reply_markup=cancel_keyboard())
    await callback.answer()

@dp.message(OrderStates.entering_amount)
async def enter_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError
    except:
        await message.answer("❌ Введи положительное число", reply_markup=cancel_keyboard())
        return
    
    await state.update_data(amount=amount)
    await state.set_state(OrderStates.entering_price)
    await message.answer("💵 <b>ВВЕДИ ЦЕНУ ЗА ЕДИНИЦУ (В ₽):</b>\n\nНапример: 1.5", reply_markup=cancel_keyboard())

@dp.message(OrderStates.entering_price)
async def enter_price(message: Message, state: FSMContext):
    try:
        price = float(message.text)
        if price <= 0:
            raise ValueError
    except:
        await message.answer("❌ Введи положительное число", reply_markup=cancel_keyboard())
        return
    
    data = await state.get_data()
    total = data['amount'] * price
    
    if total < MIN_AMOUNT:
        await message.answer(f"❌ Минимальная сумма {MIN_AMOUNT} ₽. Твоя сумма: {total:.0f} ₽.", reply_markup=cancel_keyboard())
        return
    if total > MAX_AMOUNT:
        await message.answer(f"❌ Максимальная сумма {MAX_AMOUNT} ₽. Твоя сумма: {total:.0f} ₽.", reply_markup=cancel_keyboard())
        return
    
    await state.update_data(price=price)
    await state.set_state(OrderStates.entering_comment)
    await message.answer("📝 <b>КОММЕНТАРИЙ:</b>\n\nНапиши комментарий к ордеру\nИли отправь «-» чтобы пропустить", reply_markup=cancel_keyboard())

@dp.message(OrderStates.entering_comment)
async def enter_comment(message: Message, state: FSMContext):
    comment = message.text if message.text != '-' else ''
    await state.update_data(comment=comment)
    await state.set_state(OrderStates.choosing_payment)
    
    # Здесь выбор метода оплаты (упрощённо)
    await state.set_state(OrderStates.confirming)
    
    data = await state.get_data()
    total = data['amount'] * data['price']
    
    text = (
        f"{data['item_icon']} <b>ПРОВЕРЬ ДАННЫЕ:</b>\n\n"
        f"📌 <b>Тип:</b> {'📈 ПРОДАЖА' if data['order_type'] == 'sell' else '📉 ПОКУПКА'}\n"
        f"🎮 <b>Товар:</b> {data['item_name']}\n"
        f"💰 <b>Количество:</b> {data['amount']}\n"
        f"💵 <b>Цена:</b> {data['price']} ₽\n"
        f"💎 <b>Сумма:</b> {total:.0f} ₽\n"
    )
    
    if data['comment']:
        text += f"📝 <b>Комментарий:</b> {data['comment']}\n"
    
    text += f"\n✅ <b>Всё верно?</b>"
    
    await message.answer(text, reply_markup=confirm_keyboard())

@dp.callback_query(OrderStates.confirming, lambda c: c.data == "confirm_order")
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    order_id = db.create_order(
        user_id=callback.from_user.id,
        market_type=data['market_type'],
        item={'id': data['item_id'], 'name': data['item_name'], 'icon': data['item_icon']},
        order_type=data['order_type'],
        amount=data['amount'],
        price=data['price'],
        comment=data['comment'],
        payment_method="any"
    )
    
    await state.clear()
    
    # Публикация в канал
    # await post_order_to_channel(order_id)
    
    text = (
        f"✅ <b>ОРДЕР УСПЕШНО СОЗДАН!</b>\n\n"
        f"📋 <b>ID ордера:</b> #{order_id}\n\n"
        f"🔍 <b>Что дальше?</b>\n"
        f"• Ордер появится в общем списке\n"
        f"• Покупатели смогут его найти\n"
        f"• Деньги будут заморожены на время сделки"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 ПЕРЕЙТИ К ОРДЕРУ", callback_data=f"view_order_{order_id}")
    builder.button(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu")
    builder.adjust(2)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

# ============================================
# ПОКУПКА (С ЗАМОРОЗКОЙ ДЕНЕГ)
# ============================================

@dp.callback_query(lambda c: c.data.startswith('buy_'))
async def buy_order_start(callback: CallbackQuery, state: FSMContext):
    order_id = int(callback.data.replace('buy_', ''))
    order = db.get_order(order_id)
    
    if not order or order['status'] != 'active':
        await callback.answer("❌ Ордер уже недоступен", show_alert=True)
        return
    if order['user_id'] == callback.from_user.id:
        await callback.answer("❌ Нельзя купить свой ордер", show_alert=True)
        return
    
    # Проверяем баланс
    balance = db.get_balance(callback.from_user.id)
    min_total = order['min_amount'] * order['price']
    
    if balance['balance'] < min_total:
        await callback.answer(f"❌ Недостаточно средств. Нужно минимум {min_total:.0f} ₽", show_alert=True)
        return
    
    await state.update_data(order_id=order_id)
    await state.set_state(TradeStates.entering_amount)
    
    await callback.message.edit_text(
        f"💰 <b>ВВЕДИ КОЛИЧЕСТВО:</b>\n\n"
        f"Доступно: {order['amount']}\n"
        f"Цена: {order['price']} ₽\n"
        f"Мин. сделка: {order['min_amount']:.0f}\n\n"
        f"Твой баланс: {balance['balance']} ₽",
        reply_markup=cancel_keyboard()
    )
    await callback.answer()

@dp.message(TradeStates.entering_amount)
async def buy_enter_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError
    except:
        await message.answer("❌ Введи положительное число", reply_markup=cancel_keyboard())
        return
    
    data = await state.get_data()
    order = db.get_order(data['order_id'])
    
    if not order or order['status'] != 'active':
        await message.answer("❌ Ордер уже недоступен")
        await state.clear()
        return
    
    if amount < order['min_amount']:
        await message.answer(f"❌ Минимальное количество: {order['min_amount']:.0f}", reply_markup=cancel_keyboard())
        return
    if amount > order['amount']:
        await message.answer(f"❌ Максимальное количество: {order['amount']:.0f}", reply_markup=cancel_keyboard())
        return
    
    total = amount * order['price']
    
    # Создаём сделку с заморозкой
    trade_id = db.create_secure_trade(data['order_id'], message.from_user.id, amount)
    
    if not trade_id:
        await message.answer("❌ Ошибка создания сделки. Проверь баланс.")
        await state.clear()
        return
    
    await state.clear()
    
    # Клавиатура для покупателя
    buyer_keyboard = InlineKeyboardBuilder()
    buyer_keyboard.button(text="💳 Я ОПЛАТИЛ", callback_data=f"trade_paid_{trade_id}")
    buyer_keyboard.button(text="⚠️ ОТКРЫТЬ СПОР", callback_data=f"trade_dispute_{trade_id}")
    buyer_keyboard.adjust(1)
    buyer_keyboard.row(InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu"))
    
    await message.answer(
        f"✅ <b>СДЕЛКА СОЗДАНА С ЗАМОРОЗКОЙ ДЕНЕГ!</b>\n\n"
        f"📋 <b>ID сделки:</b> #{trade_id}\n"
        f"💰 <b>Сумма:</b> {total:.0f} ₽\n\n"
        f"🔒 <b>Твои деньги заморожены</b> до завершения сделки\n"
        f"⏱ <b>Время на оплату:</b> {ESCROW_TIME} минут\n\n"
        f"📞 <b>Свяжись с продавцом</b> и переведи деньги.\n\n"
        f"✅ <b>После оплаты нажми кнопку ниже:</b>",
        reply_markup=buyer_keyboard.as_markup()
    )
    
    # Клавиатура для продавца
    seller_keyboard = InlineKeyboardBuilder()
    seller_keyboard.button(text="✅ ПОДТВЕРДИТЬ", callback_data=f"trade_confirm_{trade_id}")
    seller_keyboard.button(text="⚠️ ОТКРЫТЬ СПОР", callback_data=f"trade_dispute_{trade_id}")
    seller_keyboard.adjust(1)
    seller_keyboard.row(InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu"))
    
    await bot.send_message(
        order['user_id'],
        f"🔄 <b>НОВАЯ СДЕЛКА С ЗАМОРОЗКОЙ!</b>\n\n"
        f"Покупатель хочет купить {amount} {order['item_name']}\n"
        f"на сумму {total:.0f} ₽\n\n"
        f"🔒 Деньги покупателя уже заморожены\n"
        f"⏱ Ожидай оплаты в течение {ESCROW_TIME} минут",
        reply_markup=seller_keyboard.as_markup()
    )

# ============================================
# ОБРАБОТЧИКИ СДЕЛОК
# ============================================

@dp.callback_query(lambda c: c.data.startswith('trade_paid_'))
async def trade_paid(callback: CallbackQuery):
    trade_id = int(callback.data.replace('trade_paid_', ''))
    trade = db.get_trade(trade_id)
    
    if not trade:
        await callback.answer("❌ Сделка не найдена", show_alert=True)
        return
    if trade['buyer_id'] != callback.from_user.id:
        await callback.answer("❌ Это не твоя сделка", show_alert=True)
        return
    
    db.confirm_payment(trade_id)
    
    seller_keyboard = InlineKeyboardBuilder()
    seller_keyboard.button(text="✅ ПОДТВЕРДИТЬ", callback_data=f"trade_confirm_{trade_id}")
    seller_keyboard.button(text="⚠️ ОТКРЫТЬ СПОР", callback_data=f"trade_dispute_{trade_id}")
    seller_keyboard.adjust(1)
    seller_keyboard.row(InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu"))
    
    await bot.send_message(
        trade['seller_id'],
        f"💰 <b>ПОКУПАТЕЛЬ ОПЛАТИЛ!</b>\n\n"
        f"Сделка #{trade_id}\n"
        f"Сумма: {trade['total']} ₽\n\n"
        f"🔒 Деньги всё ещё заморожены\n"
        f"✅ Проверь поступление и подтверди:",
        reply_markup=seller_keyboard.as_markup()
    )
    
    await callback.message.edit_text(
        f"✅ <b>ТЫ ПОДТВЕРДИЛ ОПЛАТУ!</b>\n\n"
        f"🔒 Деньги остаются замороженными\n"
        f"⏳ Ожидай подтверждения от продавца",
        reply_markup=back_keyboard()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith('trade_confirm_'))
async def trade_confirm(callback: CallbackQuery):
    trade_id = int(callback.data.replace('trade_confirm_', ''))
    trade = db.get_trade(trade_id)
    
    if not trade:
        await callback.answer("❌ Сделка не найдена", show_alert=True)
        return
    if trade['seller_id'] != callback.from_user.id:
        await callback.answer("❌ Это не твоя сделка", show_alert=True)
        return
    if trade['payment_status'] != 'paid':
        await callback.answer("❌ Покупатель ещё не подтвердил оплату", show_alert=True)
        return
    
    # Завершаем сделку (размораживаем и переводим деньги)
    db.complete_trade(trade_id)
    
    # Предлагаем оставить отзыв
    await bot.send_message(
        trade['buyer_id'],
        f"✅ <b>СДЕЛКА ЗАВЕРШЕНА!</b>\n\n"
        f"Продавец подтвердил получение денег.\n"
        f"🔒 Деньги разморожены и переведены продавцу.\n\n"
        f"Оцени продавца:",
        reply_markup=review_keyboard(trade_id, trade['seller_id'])
    )
    
    await callback.message.edit_text(
        f"✅ <b>СДЕЛКА ЗАВЕРШЕНА!</b>\n\n"
        f"Ты подтвердил получение денег.\n"
        f"🔒 Деньги разморожены и переведены на твой счёт.\n\n"
        f"Комиссия платформы: {trade['commission']} ₽",
        reply_markup=back_keyboard()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith('trade_dispute_'))
async def trade_dispute(callback: CallbackQuery):
    trade_id = int(callback.data.replace('trade_dispute_', ''))
    
    # Уведомляем админа
    await bot.send_message(
        ADMIN_ID,
        f"⚠️ <b>ОТКРЫТ СПОР ПО СДЕЛКЕ!</b>\n\n"
        f"Сделка #{trade_id}\n"
        f"Пользователь: {callback.from_user.id}\n"
        f"Username: @{callback.from_user.username}\n\n"
        f"Требуется вмешательство!"
    )
    
    await callback.message.edit_text(
        f"⚠️ <b>СПОР ОТКРЫТ!</b>\n\n"
        f"Администратор уже уведомлен.\n"
        f"Деньги остаются замороженными.\n"
        f"Ожидай решения в ближайшее время.",
        reply_markup=back_keyboard()
    )
    await callback.answer()

# ============================================
# ОТЗЫВЫ
# ============================================

@dp.callback_query(lambda c: c.data.startswith('rate_'))
async def add_review(callback: CallbackQuery):
    parts = callback.data.split('_')
    trade_id = int(parts[1])
    to_id = int(parts[2])
    rating = int(parts[3])
    
    await callback.message.edit_text(
        f"📝 <b>НАПИШИ ОТЗЫВ</b>\n\n"
        f"Ты поставил {rating}⭐\n"
        f"Напиши комментарий (или отправь «-» чтобы пропустить):",
        reply_markup=cancel_keyboard()
    )
    
    # Сохраняем в state
    await state = dp.fsm.get_context(bot=bot, chat_id=callback.from_user.id, user_id=callback.from_user.id)
    await state.update_data(trade_id=trade_id, to_id=to_id, rating=rating)
    await state.set_state(TradeStates.waiting_review)
    
    await callback.answer()

@dp.message(TradeStates.waiting_review)
async def process_review(message: Message, state: FSMContext):
    data = await state.get_data()
    comment = message.text if message.text != '-' else ''
    
    db.add_review(data['trade_id'], message.from_user.id, data['to_id'], data['rating'], comment)
    
    await state.clear()
    await message.answer(
        "✅ <b>СПАСИБО ЗА ОТЗЫВ!</b>\n\n"
        "Твой отзыв поможет другим пользователям.",
        reply_markup=main_keyboard()
    )

@dp.callback_query(lambda c: c.data == "skip_review")
async def skip_review(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "✅ <b>СДЕЛКА ЗАВЕРШЕНА!</b>\n\n"
        "Спасибо за использование платформы!",
        reply_markup=main_keyboard()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "my_reviews")
async def my_reviews(callback: CallbackQuery):
    reviews = db.get_user_reviews(callback.from_user.id)
    
    if not reviews:
        await callback.message.edit_text(
            "📝 <b>МОИ ОТЗЫВЫ</b>\n\n"
            "У тебя пока нет отзывов.",
            reply_markup=back_keyboard()
        )
        await callback.answer()
        return
    
    text = "📝 <b>МОИ ОТЗЫВЫ:</b>\n\n"
    for review in reviews[:10]:
        from_user = db.get_user(review['from_id'])
        from_name = from_user['first_name'] if from_user else 'Пользователь'
        text += f"{review['rating']}⭐ от {from_name}:\n"
        text += f"«{review['comment']}»\n"
        text += f"🕐 {review['created_at'][:16]}\n\n"
    
    await callback.message.edit_text(text, reply_markup=back_keyboard())
    await callback.answer()

# ============================================
# МОИ СДЕЛКИ И ОРДЕРА
# ============================================

@dp.callback_query(lambda c: c.data == "my_trades")
async def my_trades(callback: CallbackQuery):
    trades = db.get_user_trades(callback.from_user.id)
    
    if not trades:
        await callback.message.edit_text(
            "📊 <b>МОИ СДЕЛКИ</b>\n\nУ тебя пока нет сделок.",
            reply_markup=back_keyboard()
        )
        await callback.answer()
        return
    
    text = "📊 <b>МОИ СДЕЛКИ:</b>\n\n"
    builder = InlineKeyboardBuilder()
    
    for trade in trades[:10]:
        status_emoji = "✅" if trade['status'] == 'completed' else "⏳"
        role = "📤" if trade['seller_id'] == callback.from_user.id else "📥"
        text += f"{status_emoji} {role} #{trade['id']} - {trade['total']} ₽\n"
        builder.button(text=f"#{trade['id']}", callback_data=f"trade_info_{trade['id']}")
    
    builder.adjust(5)
    builder.row(InlineKeyboardButton(text="🔙 НАЗАД", callback_data="back"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(lambda c: c.data == "my_orders")
async def my_orders(callback: CallbackQuery):
    # Заглушка - можно реализовать позже
    await callback.message.edit_text(
        "📋 <b>МОИ ОРДЕРА</b>\n\nФункция в разработке.",
        reply_markup=back_keyboard()
    )
    await callback.answer()

# ============================================
# ЗАПУСК БОТА
# ============================================

async def on_startup():
    print("\n" + "="*60)
    print("🔥 P2P БЕЗОПАСНЫЙ МАРКЕТПЛЕЙС ЗАПУЩЕН!")
    print("="*60)
    print(f"🤖 Бот: @{(await bot.get_me()).username}")
    print(f"👑 Админ ID: {ADMIN_ID}")
    print(f"🎮 Игр в базе: {len(GAMES)}")
    print(f"💰 Криптовалют: {len(CRYPTO)}")
    print(f"🔒 Система эскроу: АКТИВНА")
    print(f"⚡ Комиссия: {COMMISSION}%")
    print("="*60 + "\n")
    
    await bot.send_message(
        ADMIN_ID,
        f"🚀 <b>P2P БЕЗОПАСНЫЙ МАРКЕТПЛЕЙС ЗАПУЩЕН!</b>\n\n"
        f"🔒 Система заморозки денег активна\n"
        f"💳 Приём платежей настроен\n"
        f"⭐ Отзывы и рейтинги работают\n\n"
        f"✅ Все системы готовы!"
    )

async def main():
    await on_startup()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
