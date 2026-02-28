#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════╗
║                    P2P ГЕЙМИНГ МАРКЕТПЛЕЙС                     ║
║                    🎮 + 💰 = 🔥                                ║
║                    ВЕРСИЯ 3.0 - ФИНАЛ                          ║
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
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
    FSInputFile
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
SUPPORT_USERNAME = "p2p_support"  # Юзернейм саппорта

# ============================================
# ИГРЫ (ПОЛНЫЙ СПИСОК)
# ============================================

GAMES = [
    {"id": "pubg", "name": "PUBG Mobile", "currency": "UC", "icon": "🪖", "popular": True},
    {"id": "brawl", "name": "Brawl Stars", "currency": "гемы", "icon": "🥊", "popular": True},
    {"id": "freefire", "name": "Free Fire", "currency": "алмазы", "icon": "🔥", "popular": True},
    {"id": "steam", "name": "Steam", "currency": "руб", "icon": "🎮", "popular": True},
    {"id": "genshin", "name": "Genshin Impact", "currency": "кристаллы", "icon": "✨", "popular": True},
    {"id": "cod", "name": "Call of Duty", "currency": "CP", "icon": "🔫", "popular": True},
    {"id": "roblox", "name": "Roblox", "currency": "Robux", "icon": "🎲", "popular": True},
    {"id": "fortnite", "name": "Fortnite", "currency": "V-bucks", "icon": "🛡️", "popular": True},
    {"id": "standoff", "name": "Standoff 2", "currency": "голда", "icon": "🔫", "popular": False},
    {"id": "warface", "name": "Warface", "currency": "кредиты", "icon": "💣", "popular": False},
    {"id": "apex", "name": "Apex Legends", "currency": "монеты", "icon": "🔺", "popular": False},
    {"id": "valorant", "name": "Valorant", "currency": "VP", "icon": "🔫", "popular": False},
]

# ============================================
# КРИПТОВАЛЮТЫ
# ============================================

CRYPTO = [
    {"id": "usdt", "name": "USDT", "network": "TRC20", "icon": "💵"},
    {"id": "ton", "name": "TON", "network": "TON", "icon": "💎"},
    {"id": "btc", "name": "Bitcoin", "network": "BTC", "icon": "₿"},
    {"id": "eth", "name": "Ethereum", "network": "ERC20", "icon": "♦️"},
    {"id": "bnb", "name": "BNB", "network": "BSC", "icon": "🟡"},
]

# ============================================
# ПЛАТЁЖНЫЕ МЕТОДЫ
# ============================================

PAYMENT_METHODS = [
    {"id": "sbp", "name": "СБП", "icon": "💳", "description": "Перевод по номеру телефона"},
    {"id": "card", "name": "Карта РФ", "icon": "💳", "description": "Перевод на карту любого банка"},
    {"id": "yoomoney", "name": "ЮMoney", "icon": "💰", "description": "Перевод на кошелёк ЮMoney"},
    {"id": "qiwi", "name": "Qiwi", "icon": "📱", "description": "Перевод на Qiwi кошелёк"},
    {"id": "cash", "name": "Наличные", "icon": "💵", "description": "При личной встрече"},
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

# ============================================
# БАЗА ДАННЫХ
# ============================================

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('p2p_final.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()
    
    def create_tables(self):
        # Пользователи
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
                balance REAL DEFAULT 0,
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
        
        # Сделки
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
                status TEXT DEFAULT 'pending',
                payment_status TEXT DEFAULT 'waiting',
                created_at TEXT,
                expires_at TEXT,
                completed_at TEXT,
                dispute_reason TEXT
            )
        ''')
        
        # Отзывы
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id INTEGER,
                from_user_id INTEGER,
                to_user_id INTEGER,
                rating INTEGER,
                comment TEXT,
                created_at TEXT
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
        
        # Уведомления
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT,
                title TEXT,
                message TEXT,
                data TEXT,
                is_read BOOLEAN DEFAULT 0,
                created_at TEXT
            )
        ''')
        
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
                'is_verified': row[10],
                'is_banned': row[11],
                'last_active': row[12]
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
        
        self.conn.commit()
        return self.cursor.lastrowid
    
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
    
    # ========== СДЕЛКИ ==========
    
    def create_trade(self, order_id, buyer_id, amount):
        order = self.get_order(order_id)
        if not order or order['status'] != 'active':
            return None
        
        if amount < order['min_amount'] or amount > order['amount']:
            return None
        
        total = amount * order['price']
        commission = total * (COMMISSION / 100)
        
        self.cursor.execute('''
            INSERT INTO trades 
            (order_id, seller_id, buyer_id, amount, price, total, commission, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            order_id, 
            order['user_id'], 
            buyer_id, 
            amount, 
            order['price'], 
            total, 
            commission,
            datetime.now().isoformat(),
            (datetime.now() + timedelta(minutes=ESCROW_TIME)).isoformat()
        ))
        
        trade_id = self.cursor.lastrowid
        
        new_amount = order['amount'] - amount
        self.update_order_amount(order_id, new_amount)
        
        self.conn.commit()
        
        self.add_notification(
            order['user_id'],
            'new_trade',
            '🔄 Новая сделка!',
            f'Кто-то хочет купить {amount} {order["item_name"]}',
            {'trade_id': trade_id}
        )
        
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
                'status': row[8],
                'payment_status': row[9],
                'created_at': row[10],
                'expires_at': row[11],
                'completed_at': row[12],
                'dispute_reason': row[13]
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
                'status': row[8],
                'payment_status': row[9],
                'created_at': row[10]
            })
        return trades
    
    def get_pending_trades_for_seller(self, seller_id):
        self.cursor.execute('''
            SELECT * FROM trades 
            WHERE seller_id = ? AND status = 'pending' AND payment_status = 'waiting'
            ORDER BY created_at DESC
        ''', (seller_id,))
        rows = self.cursor.fetchall()
        trades = []
        for row in rows:
            trades.append({
                'id': row[0],
                'order_id': row[1],
                'buyer_id': row[3],
                'amount': row[4],
                'total': row[6],
                'created_at': row[10]
            })
        return trades
    
    def get_pending_trades_for_buyer(self, buyer_id):
        self.cursor.execute('''
            SELECT * FROM trades 
            WHERE buyer_id = ? AND status = 'pending' AND payment_status = 'waiting'
            ORDER BY created_at DESC
        ''', (buyer_id,))
        rows = self.cursor.fetchall()
        trades = []
        for row in rows:
            trades.append({
                'id': row[0],
                'order_id': row[1],
                'seller_id': row[2],
                'amount': row[4],
                'total': row[6],
                'created_at': row[10]
            })
        return trades
    
    def confirm_payment(self, trade_id):
        self.cursor.execute('''
            UPDATE trades SET payment_status = 'paid' WHERE id = ?
        ''', (trade_id,))
        self.conn.commit()
    
    def complete_trade(self, trade_id):
        trade = self.get_trade(trade_id)
        if not trade:
            return False
        
        self.cursor.execute('''
            UPDATE trades SET status = 'completed', payment_status = 'confirmed', completed_at = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), trade_id))
        
        self.cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', 
                           (trade['commission'], ADMIN_ID))
        
        self.cursor.execute('''
            UPDATE users SET deals_count = deals_count + 1, successful_deals = successful_deals + 1
            WHERE user_id = ?
        ''', (trade['seller_id'],))
        
        self.cursor.execute('''
            UPDATE users SET deals_count = deals_count + 1, successful_deals = successful_deals + 1
            WHERE user_id = ?
        ''', (trade['buyer_id'],))
        
        self.conn.commit()
        
        self.add_notification(trade['seller_id'], 'trade_complete', '✅ Сделка завершена!', 
                             f'Сделка на {trade["total"]} ₽ успешно завершена')
        self.add_notification(trade['buyer_id'], 'trade_complete', '✅ Сделка завершена!', 
                             f'Сделка на {trade["total"]} ₽ успешно завершена')
        
        return True
    
    # ========== УВЕДОМЛЕНИЯ ==========
    
    def add_notification(self, user_id, type, title, message, data=None):
        self.cursor.execute('''
            INSERT INTO notifications (user_id, type, title, message, data, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, type, title, message, json.dumps(data) if data else None, datetime.now().isoformat()))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_unread_notifications(self, user_id):
        self.cursor.execute('''
            SELECT * FROM notifications 
            WHERE user_id = ? AND is_read = 0
            ORDER BY created_at DESC
        ''', (user_id,))
        rows = self.cursor.fetchall()
        notifications = []
        for row in rows:
            notifications.append({
                'id': row[0],
                'user_id': row[1],
                'type': row[2],
                'title': row[3],
                'message': row[4],
                'data': row[5],
                'is_read': row[6],
                'created_at': row[7]
            })
        return notifications
    
    def mark_notification_read(self, notification_id):
        self.cursor.execute('UPDATE notifications SET is_read = 1 WHERE id = ?', (notification_id,))
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
        KeyboardButton(text="❓ ПОМОЩЬ")
    ]
    builder.add(*buttons)
    builder.adjust(2, 2)
    return builder.as_markup(resize_keyboard=True)

def games_keyboard():
    builder = InlineKeyboardBuilder()
    popular = [g for g in GAMES if g['popular']]
    for game in popular:
        builder.button(text=f"{game['icon']} {game['name']}", callback_data=f"game_{game['id']}")
    builder.adjust(2)
    builder.row(
        InlineKeyboardButton(text="➕ СОЗДАТЬ ОРДЕР", callback_data="create_game"),
        InlineKeyboardButton(text="📋 ВСЕ ИГРЫ", callback_data="all_games")
    )
    builder.row(InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu"))
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

def order_type_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📈 КУПИТЬ", callback_data="type_buy")
    builder.button(text="📉 ПРОДАТЬ", callback_data="type_sell")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="❌ ОТМЕНА", callback_data="cancel_order"))
    return builder.as_markup()

def payment_keyboard():
    builder = InlineKeyboardBuilder()
    for pm in PAYMENT_METHODS:
        builder.button(text=f"{pm['icon']} {pm['name']}", callback_data=f"payment_{pm['id']}")
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

def profile_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 МОИ СДЕЛКИ", callback_data="my_trades")
    builder.button(text="📋 МОИ ОРДЕРА", callback_data="my_orders")
    builder.button(text="🔔 УВЕДОМЛЕНИЯ", callback_data="my_notifications")
    builder.button(text="⭐ ИЗБРАННОЕ", callback_data="my_favorites")
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
        f"🌟 <b>ДОБРО ПОЖАЛОВАТЬ В P2P МАРКЕТПЛЕЙС!</b> 🌟\n\n"
        f"👋 <b>Привет, {user.first_name}!</b>\n\n"
        f"🎮 <b>Здесь ты можешь:</b>\n"
        f"├ 🔥 Покупать и продавать <b>игровую валюту</b>\n"
        f"├ 💰 Торговать <b>криптовалютой</b> P2P\n"
        f"├ 🤝 Безопасные сделки через <b>эскроу</b>\n"
        f"└ ⭐ Зарабатывать на <b>рефералах</b>\n\n"
        f"📊 <b>Твоя реферальная ссылка:</b>\n"
        f"<code>https://t.me/{(await bot.get_me()).username}?start={referral_code}</code>\n\n"
        f"👇 <b>Выбери раздел:</b>"
    )
    
    await message.answer(welcome_text, reply_markup=main_keyboard())

# ============================================
# ГЛАВНОЕ МЕНЮ
# ============================================

@dp.message(lambda m: m.text == "🎮 ИГРЫ")
async def games_section(message: Message):
    text = "🎮 <b>ИГРОВОЙ МАРКЕТПЛЕЙС</b>\n\n🔥 <b>Популярные игры:</b>\n"
    for game in GAMES:
        if game['popular']:
            text += f"{game['icon']} {game['name']} — {game['currency']}\n"
    text += f"\n💰 <b>Комиссия:</b> {COMMISSION}%\n⏱ <b>Время на оплату:</b> {ESCROW_TIME} мин"
    await message.answer(text, reply_markup=games_keyboard())

@dp.message(lambda m: m.text == "💰 КРИПТА")
async def crypto_section(message: Message):
    text = "💰 <b>КРИПТО-БИРЖА P2P</b>\n\n💎 <b>Доступные валюты:</b>\n"
    for crypto in CRYPTO:
        text += f"{crypto['icon']} {crypto['name']} ({crypto['network']})\n"
    text += f"\n💰 <b>Комиссия:</b> {COMMISSION}%\n⏱ <b>Время на оплату:</b> {ESCROW_TIME} мин"
    await message.answer(text, reply_markup=crypto_keyboard())

@dp.message(lambda m: m.text == "👤 ПРОФИЛЬ")
async def profile_section(message: Message):
    user = db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Ошибка загрузки профиля")
        return
    
    rating = user['rating']
    stars = "⭐" * int(rating) + ("✨" if rating % 1 >= 0.5 else "")
    deals_success = user['successful_deals']
    deals_total = user['deals_count']
    success_rate = (deals_success / deals_total * 100) if deals_total > 0 else 100
    
    text = (
        f"👤 <b>ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ</b>\n\n"
        f"🆔 <b>ID:</b> <code>{user['user_id']}</code>\n"
        f"📱 <b>Username:</b> @{user['username'] if user['username'] else 'нет'}\n"
        f"📅 <b>С нами:</b> {user['registered_at'][:10]}\n\n"
        f"⭐ <b>Рейтинг:</b> {stars} ({rating:.1f})\n"
        f"📊 <b>Сделок:</b> {deals_success}/{deals_total} ({success_rate:.0f}%)\n"
        f"💰 <b>Баланс:</b> {user['balance']} ₽\n"
    )
    
    if user['is_verified']:
        text += f"\n✅ <b>Верифицированный продавец</b>\n"
    
    await message.answer(text, reply_markup=profile_keyboard())

@dp.message(lambda m: m.text == "❓ ПОМОЩЬ")
async def help_section(message: Message):
    text = (
        f"❓ <b>ЦЕНТР ПОМОЩИ</b>\n\n"
        f"📌 <b>Как проходит сделка?</b>\n"
        f"1️⃣ Найди подходящий ордер\n"
        f"2️⃣ Нажми «Купить» и введи количество\n"
        f"3️⃣ Бот заблокирует товар у продавца\n"
        f"4️⃣ Переведи деньги продавцу\n"
        f"5️⃣ Нажми «Я оплатил»\n"
        f"6️⃣ Продавец подтверждает получение\n"
        f"7️⃣ Товар переходит к тебе\n\n"
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

@dp.callback_query(lambda c: c.data == "all_games")
async def all_games_callback(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()
    for game in GAMES:
        builder.button(text=f"{game['icon']} {game['name']}", callback_data=f"game_{game['id']}")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="🔙 НАЗАД", callback_data="back"))
    await callback.message.edit_text("🎮 <b>ВСЕ ИГРЫ:</b>", reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(lambda c: c.data == "cancel_order")
async def cancel_order_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Действие отменено", reply_markup=games_keyboard())
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
        text = f"{game['icon']} <b>{game['name']}</b>\n\n😕 Пока нет активных ордеров.\n\n🔥 <b>Будь первым!</b>"
        builder = InlineKeyboardBuilder()
        builder.button(text="➕ СОЗДАТЬ ОРДЕР", callback_data=f"create_game_{game_id}")
        builder.button(text="🔙 НАЗАД", callback_data="back")
        builder.adjust(2)
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
        await callback.answer()
        return
    
    text = f"{game['icon']} <b>{game['name']} - ОРДЕРА:</b>\n\n"
    for order in orders[:5]:
        emoji = "📈" if order['order_type'] == 'sell' else "📉"
        text += f"{emoji} {order['amount']:.0f} {game['currency']} × {order['price']}₽ = {order['total']:.0f}₽\n"
        text += f"   👤 {order['views']} просмотров\n\n"
    
    builder = InlineKeyboardBuilder()
    for order in orders[:4]:
        builder.button(text=f"{order['amount']:.0f} {game['currency']}", callback_data=f"view_order_{order['id']}")
    builder.adjust(2)
    builder.row(
        InlineKeyboardButton(text="➕ СОЗДАТЬ ОРДЕР", callback_data=f"create_game_{game_id}"),
        InlineKeyboardButton(text="🔙 НАЗАД", callback_data="back")
    )
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
        text = f"{crypto['icon']} <b>{crypto['name']}</b>\n\n😕 Пока нет активных ордеров.\n\n🔥 <b>Создай первый!</b>"
        builder = InlineKeyboardBuilder()
        builder.button(text="➕ СОЗДАТЬ ОРДЕР", callback_data=f"create_crypto_{crypto_id}")
        builder.button(text="🔙 НАЗАД", callback_data="back")
        builder.adjust(2)
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
        await callback.answer()
        return
    
    text = f"{crypto['icon']} <b>{crypto['name']} - ОРДЕРА:</b>\n\n"
    for order in orders[:5]:
        emoji = "📈" if order['order_type'] == 'sell' else "📉"
        text += f"{emoji} {order['amount']} {crypto_id.upper()} × {order['price']}₽ = {order['total']:.0f}₽\n\n"
    
    builder = InlineKeyboardBuilder()
    for order in orders[:4]:
        builder.button(text=f"{order['amount']} {crypto_id.upper()}", callback_data=f"view_order_{order['id']}")
    builder.adjust(2)
    builder.row(
        InlineKeyboardButton(text="➕ СОЗДАТЬ ОРДЕР", callback_data=f"create_crypto_{crypto_id}"),
        InlineKeyboardButton(text="🔙 НАЗАД", callback_data="back")
    )
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
        f"📦 <b>Мин. сделка:</b> {order['min_amount']:.0f}\n"
    )
    
    if order['comment']:
        text += f"\n📝 <b>Комментарий:</b>\n{order['comment']}\n"
    
    seller = db.get_user(order['user_id'])
    if seller:
        rating = seller['rating']
        stars = "⭐" * int(rating) + ("✨" if rating % 1 >= 0.5 else "")
        text += f"\n👤 <b>Продавец:</b> {seller['first_name']} {stars}\n"
    
    text += f"\n🕐 <b>Создан:</b> {order['created_at'][:16]}\n"
    text += f"👁 <b>Просмотров:</b> {order['views']}"
    
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
        await callback.message.edit_text("⭐ <b>ИЗБРАННОЕ</b>\n\nУ тебя пока нет избранных ордеров.", reply_markup=back_keyboard())
        await callback.answer()
        return
    
    text = "⭐ <b>ТВОИ ИЗБРАННЫЕ ОРДЕРА:</b>\n\n"
    builder = InlineKeyboardBuilder()
    for order_id in favorites[:5]:
        order = db.get_order(order_id)
        if order:
            text += f"{order['item_icon']} {order['item_name']} — {order['amount']} | {order['total']}₽\n\n"
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
async def create_game_order_start(callback: CallbackQuery, state: FSMContext):
    game_id = callback.data.replace('create_game_', '')
    game = next((g for g in GAMES if g['id'] == game_id), None)
    if not game:
        await callback.answer("❌ Игра не найдена")
        return
    
    await state.update_data(market_type='game', item=game, item_id=game_id, item_name=game['name'], item_icon=game['icon'])
    await state.set_state(OrderStates.choosing_type)
    await callback.message.edit_text(f"{game['icon']} <b>{game['name']}</b>\n\nТы хочешь купить или продать?", reply_markup=order_type_keyboard())
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith('create_crypto_'))
async def create_crypto_order_start(callback: CallbackQuery, state: FSMContext):
    crypto_id = callback.data.replace('create_crypto_', '')
    crypto = next((c for c in CRYPTO if c['id'] == crypto_id), None)
    if not crypto:
        await callback.answer("❌ Валюта не найдена")
        return
    
    await state.update_data(market_type='crypto', item=crypto, item_id=crypto_id, item_name=crypto['name'], item_icon=crypto['icon'])
    await state.set_state(OrderStates.choosing_type)
    await callback.message.edit_text(f"{crypto['icon']} <b>{crypto['name']}</b>\n\nТы хочешь купить или продать?", reply_markup=order_type_keyboard())
    await callback.answer()

@dp.callback_query(OrderStates.choosing_type, lambda c: c.data.startswith('type_'))
async def create_order_type(callback: CallbackQuery, state: FSMContext):
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
    await message.answer("💳 <b>ВЫБЕРИ СПОСОБ ОПЛАТЫ:</b>", reply_markup=payment_keyboard())

@dp.callback_query(OrderStates.choosing_payment, lambda c: c.data.startswith('payment_'))
async def choose_payment(callback: CallbackQuery, state: FSMContext):
    payment_id = callback.data.replace('payment_', '')
    payment = next((p for p in PAYMENT_METHODS if p['id'] == payment_id), None)
    if not payment:
        await callback.answer("❌ Способ оплаты не найден")
        return
    
    await state.update_data(payment_method=payment_id, payment_name=payment['name'])
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
        f"💳 <b>Оплата:</b> {payment['name']}\n"
    )
    if data['comment']:
        text += f"📝 <b>Комментарий:</b> {data['comment']}\n"
    text += f"\n✅ <b>Всё верно?</b>"
    
    await callback.message.edit_text(text, reply_markup=confirm_keyboard())
    await callback.answer()

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
        payment_method=data['payment_method']
    )
    await state.clear()
    
    text = f"✅ <b>ОРДЕР УСПЕШНО СОЗДАН!</b>\n\n📋 <b>ID ордера:</b> #{order_id}\n\n🔍 <b>Что дальше?</b>\n• Ордер появится в общем списке\n• Покупатели смогут его найти\n• Ты получишь уведомление о сделке"
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 ПЕРЕЙТИ К ОРДЕРУ", callback_data=f"view_order_{order_id}")
    builder.button(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu")
    builder.adjust(2)
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

# ============================================
# ПОКУПКА
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
    
    await state.update_data(order_id=order_id)
    await state.set_state(TradeStates.entering_amount)
    await callback.message.edit_text(
        f"💰 <b>ВВЕДИ КОЛИЧЕСТВО:</b>\n\nДоступно: {order['amount']}\nЦена: {order['price']} ₽\nМин. сделка: {order['min_amount']:.0f}",
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
    trade_id = db.create_trade(data['order_id'], message.from_user.id, amount)
    
    if not trade_id:
        await message.answer("❌ Ошибка создания сделки")
        await state.clear()
        return
    
    await state.clear()
    
    buyer_keyboard = InlineKeyboardBuilder()
    buyer_keyboard.button(text="💳 Я ОПЛАТИЛ", callback_data=f"trade_paid_{trade_id}")
    buyer_keyboard.button(text="⚠️ ОТКРЫТЬ СПОР", callback_data=f"trade_dispute_{trade_id}")
    buyer_keyboard.adjust(1)
    buyer_keyboard.row(InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu"))
    
    await message.answer(
        f"✅ <b>СДЕЛКА СОЗДАНА!</b>\n\n📋 <b>ID сделки:</b> #{trade_id}\n💰 <b>Сумма к оплате:</b> {total:.0f} ₽\n\n⏱ <b>Время на оплату:</b> {ESCROW_TIME} минут\n\n✅ <b>После оплаты нажми кнопку ниже:</b>",
        reply_markup=buyer_keyboard.as_markup()
    )
    
    seller_keyboard = InlineKeyboardBuilder()
    seller_keyboard.button(text="✅ ПОДТВЕРДИТЬ", callback_data=f"trade_confirm_{trade_id}")
    seller_keyboard.button(text="⚠️ ОТКРЫТЬ СПОР", callback_data=f"trade_dispute_{trade_id}")
    seller_keyboard.adjust(1)
    seller_keyboard.row(InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu"))
    
    await bot.send_message(
        order['user_id'],
        f"🔄 <b>НОВАЯ СДЕЛКА!</b>\n\nПокупатель хочет купить {amount} {order['item_name']}\nна сумму {total:.0f} ₽\n\n⏱ Ожидай оплаты в течение {ESCROW_TIME} минут",
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
        f"💰 <b>ПОКУПАТЕЛЬ ОПЛАТИЛ!</b>\n\nСделка #{trade_id}\nСумма: {trade['total']} ₽\n\nПроверь поступление денег и подтверди:",
        reply_markup=seller_keyboard.as_markup()
    )
    
    await callback.message.edit_text(
        f"✅ <b>ТЫ ПОДТВЕРДИЛ ОПЛАТУ!</b>\n\nТеперь ожидай, пока продавец проверит поступление денег.",
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
    
    db.complete_trade(trade_id)
    
    await bot.send_message(
        trade['buyer_id'],
        f"✅ <b>СДЕЛКА ЗАВЕРШЕНА!</b>\n\nПродавец подтвердил получение денег.\nТовар переведён на твой счёт!\n\nСпасибо за покупку! 🌟"
    )
    
    await callback.message.edit_text(
        f"✅ <b>СДЕЛКА ЗАВЕРШЕНА!</b>\n\nТы подтвердил получение денег.\nТовар передан покупателю.\n\nКомиссия платформы: {trade['commission']} ₽",
        reply_markup=back_keyboard()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith('trade_dispute_'))
async def trade_dispute(callback: CallbackQuery):
    trade_id = int(callback.data.replace('trade_dispute_', ''))
    
    await bot.send_message(
        ADMIN_ID,
        f"⚠️ <b>ОТКРЫТ СПОР ПО СДЕЛКЕ!</b>\n\nСделка #{trade_id}\nПользователь: {callback.from_user.id}\nUsername: @{callback.from_user.username}\n\nТребуется вмешательство!"
    )
    
    await callback.message.edit_text(
        f"⚠️ <b>СПОР ОТКРЫТ!</b>\n\nАдминистратор уже уведомлен.\nОжидай решения в ближайшее время.",
        reply_markup=back_keyboard()
    )
    await callback.answer()

# ============================================
# ПРОФИЛЬНЫЕ РАЗДЕЛЫ
# ============================================

@dp.callback_query(lambda c: c.data == "my_trades")
async def my_trades(callback: CallbackQuery):
    trades = db.get_user_trades(callback.from_user.id)
    pending_seller = db.get_pending_trades_for_seller(callback.from_user.id)
    pending_buyer = db.get_pending_trades_for_buyer(callback.from_user.id)
    
    if not trades:
        await callback.message.edit_text("📊 <b>МОИ СДЕЛКИ</b>\n\nУ тебя пока нет сделок.", reply_markup=back_keyboard())
        await callback.answer()
        return
    
    text = "📊 <b>МОИ СДЕЛКИ:</b>\n\n"
    
    if pending_seller:
        text += "⏳ <b>Ожидают твоего подтверждения:</b>\n"
        for trade in pending_seller[:3]:
            text += f"  • #{trade['id']} - {trade['total']} ₽\n"
        text += "\n"
    
    if pending_buyer:
        text += "⏳ <b>Ты ещё не подтвердил оплату:</b>\n"
        for trade in pending_buyer[:3]:
            text += f"  • #{trade['id']} - {trade['total']} ₽\n"
        text += "\n"
    
    text += "📋 <b>Все сделки:</b>\n"
    for trade in trades[:10]:
        status_emoji = "✅" if trade['status'] == 'completed' else "⏳"
        role = "📤" if trade['seller_id'] == callback.from_user.id else "📥"
        text += f"{status_emoji} {role} #{trade['id']} - {trade['total']} ₽\n"
    
    builder = InlineKeyboardBuilder()
    if pending_seller:
        builder.button(text="✅ ПОДТВЕРДИТЬ", callback_data="show_pending_seller")
    if pending_buyer:
        builder.button(text="💳 ПОДТВЕРДИТЬ ОПЛАТУ", callback_data="show_pending_buyer")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="🔙 НАЗАД", callback_data="back"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(lambda c: c.data == "my_orders")
async def my_orders(callback: CallbackQuery):
    orders = db.get_user_orders(callback.from_user.id)
    if not orders:
        await callback.message.edit_text("📋 <b>МОИ ОРДЕРА</b>\n\nУ тебя пока нет активных ордеров.", reply_markup=back_keyboard())
        await callback.answer()
        return
    
    text = "📋 <b>МОИ ОРДЕРА:</b>\n\n"
    for order in orders[:10]:
        status_emoji = "🟢" if order['status'] == 'active' else "🔴"
        text += f"{status_emoji} {order['item_name']}: {order['amount']} | {order['total']}₽\n"
    
    await callback.message.edit_text(text, reply_markup=back_keyboard())
    await callback.answer()

@dp.callback_query(lambda c: c.data == "my_notifications")
async def my_notifications(callback: CallbackQuery):
    notifications = db.get_unread_notifications(callback.from_user.id)
    if not notifications:
        await callback.message.edit_text("🔔 <b>УВЕДОМЛЕНИЯ</b>\n\nУ тебя нет новых уведомлений.", reply_markup=back_keyboard())
        await callback.answer()
        return
    
    text = "🔔 <b>ТВОИ УВЕДОМЛЕНИЯ:</b>\n\n"
    for notif in notifications[:5]:
        text += f"• {notif['title']}\n  {notif['message']}\n\n"
        db.mark_notification_read(notif['id'])
    
    await callback.message.edit_text(text, reply_markup=back_keyboard())
    await callback.answer()

@dp.callback_query(lambda c: c.data == "show_pending_seller")
async def show_pending_seller(callback: CallbackQuery):
    trades = db.get_pending_trades_for_seller(callback.from_user.id)
    if not trades:
        await callback.answer("Нет ожидающих сделок", show_alert=True)
        return
    
    text = "✅ <b>СДЕЛКИ, ОЖИДАЮЩИЕ ПОДТВЕРЖДЕНИЯ:</b>\n\n"
    builder = InlineKeyboardBuilder()
    for trade in trades[:5]:
        text += f"#{trade['id']} - {trade['total']} ₽\n"
        builder.button(text=f"✅ #{trade['id']}", callback_data=f"trade_confirm_{trade['id']}")
    builder.adjust(3)
    builder.row(InlineKeyboardButton(text="🔙 НАЗАД", callback_data="my_trades"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(lambda c: c.data == "show_pending_buyer")
async def show_pending_buyer(callback: CallbackQuery):
    trades = db.get_pending_trades_for_buyer(callback.from_user.id)
    if not trades:
        await callback.answer("Нет ожидающих сделок", show_alert=True)
        return
    
    text = "💳 <b>СДЕЛКИ, ОЖИДАЮЩИЕ ТВОЕЙ ОПЛАТЫ:</b>\n\n"
    builder = InlineKeyboardBuilder()
    for trade in trades[:5]:
        text += f"#{trade['id']} - {trade['total']} ₽\n"
        builder.button(text=f"💳 #{trade['id']}", callback_data=f"trade_paid_{trade['id']}")
    builder.adjust(3)
    builder.row(InlineKeyboardButton(text="🔙 НАЗАД", callback_data="my_trades"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

# ============================================
# ЗАПУСК БОТА
# ============================================

async def on_startup():
    print("\n" + "="*60)
    print("🔥 P2P ГЕЙМИНГ МАРКЕТПЛЕЙС ЗАПУЩЕН!")
    print("="*60)
    print(f"🤖 Бот: @{(await bot.get_me()).username}")
    print(f"👑 Админ ID: {ADMIN_ID}")
    print(f"🎮 Игр в базе: {len(GAMES)}")
    print(f"💰 Криптовалют: {len(CRYPTO)}")
    print(f"⚡ Комиссия: {COMMISSION}%")
    print("="*60 + "\n")
    
    await bot.send_message(
        ADMIN_ID,
        f"🚀 <b>P2P МАРКЕТПЛЕЙС ЗАПУЩЕН!</b>\n\n"
        f"🎮 Игр: {len(GAMES)}\n"
        f"💰 Криптовалют: {len(CRYPTO)}\n"
        f"⚡ Комиссия: {COMMISSION}%\n"
        f"⏱ Время эскроу: {ESCROW_TIME} мин\n\n"
        f"✅ Все системы работают!"
    )

async def main():
    await on_startup()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
