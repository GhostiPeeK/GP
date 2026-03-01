#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                    P2P ГЕЙМИНГ МАРКЕТПЛЕЙС + КРИПТО-БИРЖА                          ║
║                         ПОЛНОСТЬЮ РАБОЧАЯ ВЕРСИЯ                                      ║
║                         ПОДДЕРЖКА: @GhostiPeeK_2                                      ║
║                         ЧАТ ПОДДЕРЖКИ: -1003664296821                                 ║
║                                    🔥                                                   ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
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

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.client.bot import DefaultBotProperties
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode

# ============================================
# 🔥 ТВОИ ДАННЫЕ (ВСТАВЛЕНЫ)
# ============================================

BOT_TOKEN = "8339352233:AAGixj9izEbOVKHvhpKeTd_4_Y2CP-f-ZhE"
ADMIN_ID = 2091630272
SUPPORT_CHAT_ID = -1003664296821  # ID чата поддержки

# ============================================
# ⚡ НАСТРОЙКИ ПЛАТФОРМЫ
# ============================================

COMMISSION = 1.0  # Комиссия бота (%)
ESCROW_TIME = 60  # Время на оплату (минут)
MIN_AMOUNT = 100  # Минимальная сумма сделки (руб)
MAX_AMOUNT = 1000000  # Максимальная сумма сделки (руб)
WELCOME_BONUS = 100  # Приветственный бонус (руб)
REFERRAL_BONUS = 10  # Бонус рефереру (%)
SUPPORT_USERNAME = "GhostiPeeK_2"  # Юзернейм саппорта

# ============================================
# 🎮 ИГРЫ
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
    {"id": "dota2", "name": "Dota 2", "currency": "уровни", "icon": "⚔️", "popular": True},
    {"id": "csgo", "name": "CS:GO", "currency": "скины", "icon": "🔫", "popular": True},
]

# ============================================
# 💰 КРИПТОВАЛЮТЫ
# ============================================

CRYPTO = [
    {"id": "usdt", "name": "USDT", "network": "TRC20", "icon": "💵", "popular": True},
    {"id": "ton", "name": "TON", "network": "TON", "icon": "💎", "popular": True},
    {"id": "btc", "name": "Bitcoin", "network": "BTC", "icon": "₿", "popular": True},
]

# ============================================
# 🎨 FSM СОСТОЯНИЯ
# ============================================

class OrderStates(StatesGroup):
    choosing_market = State()
    choosing_item = State()
    choosing_type = State()
    entering_amount = State()
    entering_price = State()
    entering_comment = State()
    confirming = State()

class TradeStates(StatesGroup):
    entering_amount = State()
    waiting_payment = State()
    waiting_confirmation = State()
    waiting_review = State()

class SupportStates(StatesGroup):
    waiting_message = State()

# ============================================
# 💾 БАЗА ДАННЫХ
# ============================================

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('p2p_megabot.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()
    
    def create_tables(self):
        # Пользователи
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                registered_at TIMESTAMP,
                referrer_id INTEGER DEFAULT NULL,
                referral_code TEXT UNIQUE,
                referral_balance REAL DEFAULT 0,
                referral_count INTEGER DEFAULT 0,
                rating REAL DEFAULT 5.0,
                deals_count INTEGER DEFAULT 0,
                successful_deals INTEGER DEFAULT 0,
                deals_volume REAL DEFAULT 0,
                balance REAL DEFAULT 100,
                locked_balance REAL DEFAULT 0,
                is_verified BOOLEAN DEFAULT 0,
                is_banned BOOLEAN DEFAULT 0,
                last_activity TIMESTAMP,
                last_daily_bonus TIMESTAMP,
                FOREIGN KEY (referrer_id) REFERENCES users(user_id)
            )
        ''')
        
        # Игровые ордера
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                game_id TEXT,
                game_name TEXT,
                game_icon TEXT,
                game_currency TEXT,
                order_type TEXT,
                amount REAL,
                price REAL,
                total REAL,
                min_amount REAL,
                comment TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP,
                expires_at TIMESTAMP,
                views INTEGER DEFAULT 0,
                favorites INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Крипто ордера
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS crypto_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                currency_id TEXT,
                currency_name TEXT,
                currency_icon TEXT,
                order_type TEXT,
                amount REAL,
                price REAL,
                total_fiat REAL,
                min_amount REAL,
                comment TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP,
                expires_at TIMESTAMP,
                views INTEGER DEFAULT 0,
                favorites INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Сделки
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_type TEXT,
                order_id INTEGER,
                seller_id INTEGER,
                buyer_id INTEGER,
                item_name TEXT,
                item_icon TEXT,
                amount REAL,
                price REAL,
                total REAL,
                commission REAL,
                status TEXT DEFAULT 'pending',
                payment_status TEXT DEFAULT 'waiting',
                created_at TIMESTAMP,
                expires_at TIMESTAMP,
                completed_at TIMESTAMP,
                dispute_reason TEXT,
                FOREIGN KEY (seller_id) REFERENCES users(user_id),
                FOREIGN KEY (buyer_id) REFERENCES users(user_id)
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
                created_at TIMESTAMP,
                FOREIGN KEY (trade_id) REFERENCES trades(id)
            )
        ''')
        
        # Избранное
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS favorites (
                user_id INTEGER,
                order_type TEXT,
                order_id INTEGER,
                created_at TIMESTAMP,
                PRIMARY KEY (user_id, order_type, order_id)
            )
        ''')
        
        self.conn.commit()
        logging.info("✅ База данных готова")
    
    # ========== ПОЛЬЗОВАТЕЛИ ==========
    
    def add_user(self, user_id, username, first_name, last_name=None, referrer_code=None):
        # Проверяем существование
        self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        if self.cursor.fetchone():
            return self.get_user(user_id)['referral_code']
        
        ref_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        
        referrer_id = None
        if referrer_code:
            self.cursor.execute('SELECT user_id FROM users WHERE referral_code = ?', (referrer_code,))
            res = self.cursor.fetchone()
            if res:
                referrer_id = res[0]
                # Начисляем бонус рефереру
                self.cursor.execute('''
                    UPDATE users SET referral_balance = referral_balance + ?
                    WHERE user_id = ?
                ''', (WELCOME_BONUS * (REFERRAL_BONUS/100), referrer_id))
        
        self.cursor.execute('''
            INSERT INTO users 
            (user_id, username, first_name, last_name, registered_at, referrer_id, referral_code, last_activity, balance)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, username, first_name, last_name,
            datetime.now(), referrer_id, ref_code,
            datetime.now(), WELCOME_BONUS
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
                'last_name': row[3],
                'registered_at': row[4],
                'referrer_id': row[5],
                'referral_code': row[6],
                'referral_balance': row[7],
                'referral_count': row[8],
                'rating': row[9],
                'deals_count': row[10],
                'successful_deals': row[11],
                'deals_volume': row[12],
                'balance': row[13],
                'locked_balance': row[14],
                'is_verified': row[15],
                'is_banned': row[16],
                'last_activity': row[17],
                'last_daily_bonus': row[18]
            }
        return None
    
    def get_balance(self, user_id):
        self.cursor.execute('SELECT balance, locked_balance FROM users WHERE user_id = ?', (user_id,))
        row = self.cursor.fetchone()
        return {'available': row[0] or 0, 'locked': row[1] or 0} if row else {'available': 0, 'locked': 0}
    
    # ========== ИГРОВЫЕ ОРДЕРА ==========
    
    def create_game_order(self, user_id, game_id, order_type, amount, price, comment):
        game = next((g for g in GAMES if g['id'] == game_id), None)
        if not game:
            return None
        
        total = amount * price
        min_amount = MIN_AMOUNT / price
        
        self.cursor.execute('''
            INSERT INTO game_orders 
            (user_id, game_id, game_name, game_icon, game_currency, order_type, amount, price, total, 
             min_amount, comment, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, game_id, game['name'], game['icon'], game['currency'], order_type, amount, price, total,
            min_amount, comment, datetime.now(),
            datetime.now() + timedelta(hours=24)
        ))
        
        order_id = self.cursor.lastrowid
        self.conn.commit()
        return order_id
    
    def get_game_orders(self, game_id=None, status='active'):
        query = 'SELECT * FROM game_orders WHERE status = ?'
        params = [status]
        
        if game_id:
            query += ' AND game_id = ?'
            params.append(game_id)
        
        query += ' ORDER BY created_at DESC'
        
        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()
        
        orders = []
        for row in rows:
            orders.append({
                'id': row[0],
                'user_id': row[1],
                'game_id': row[2],
                'game_name': row[3],
                'game_icon': row[4],
                'game_currency': row[5],
                'order_type': row[6],
                'amount': row[7],
                'price': row[8],
                'total': row[9],
                'min_amount': row[10],
                'comment': row[11],
                'status': row[12],
                'created_at': row[13],
                'expires_at': row[14],
                'views': row[15],
                'favorites': row[16]
            })
        return orders
    
    def get_game_order(self, order_id):
        self.cursor.execute('SELECT * FROM game_orders WHERE id = ?', (order_id,))
        row = self.cursor.fetchone()
        if row:
            self.cursor.execute('UPDATE game_orders SET views = views + 1 WHERE id = ?', (order_id,))
            self.conn.commit()
            
            return {
                'id': row[0],
                'user_id': row[1],
                'game_id': row[2],
                'game_name': row[3],
                'game_icon': row[4],
                'game_currency': row[5],
                'order_type': row[6],
                'amount': row[7],
                'price': row[8],
                'total': row[9],
                'min_amount': row[10],
                'comment': row[11],
                'status': row[12],
                'created_at': row[13],
                'expires_at': row[14],
                'views': row[15],
                'favorites': row[16]
            }
        return None
    
    def update_game_order_amount(self, order_id, new_amount):
        if new_amount <= 0:
            self.cursor.execute('UPDATE game_orders SET status = "completed" WHERE id = ?', (order_id,))
        else:
            self.cursor.execute('UPDATE game_orders SET amount = ? WHERE id = ?', (new_amount, order_id))
        self.conn.commit()
    
    # ========== КРИПТО ОРДЕРА ==========
    
    def create_crypto_order(self, user_id, currency_id, order_type, amount, price, comment):
        currency = next((c for c in CRYPTO if c['id'] == currency_id), None)
        if not currency:
            return None
        
        total = amount * price
        min_amount = MIN_AMOUNT / price
        
        self.cursor.execute('''
            INSERT INTO crypto_orders 
            (user_id, currency_id, currency_name, currency_icon, order_type, amount, price, 
             total_fiat, min_amount, comment, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, currency_id, currency['name'], currency['icon'], order_type, amount, price,
            total, min_amount, comment, datetime.now(),
            datetime.now() + timedelta(hours=24)
        ))
        
        order_id = self.cursor.lastrowid
        self.conn.commit()
        return order_id
    
    def get_crypto_orders(self, currency_id=None, status='active'):
        query = 'SELECT * FROM crypto_orders WHERE status = ?'
        params = [status]
        
        if currency_id:
            query += ' AND currency_id = ?'
            params.append(currency_id)
        
        query += ' ORDER BY created_at DESC'
        
        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()
        
        orders = []
        for row in rows:
            orders.append({
                'id': row[0],
                'user_id': row[1],
                'currency_id': row[2],
                'currency_name': row[3],
                'currency_icon': row[4],
                'order_type': row[5],
                'amount': row[6],
                'price': row[7],
                'total_fiat': row[8],
                'min_amount': row[9],
                'comment': row[10],
                'status': row[11],
                'created_at': row[12],
                'expires_at': row[13],
                'views': row[14],
                'favorites': row[15]
            })
        return orders
    
    def get_crypto_order(self, order_id):
        self.cursor.execute('SELECT * FROM crypto_orders WHERE id = ?', (order_id,))
        row = self.cursor.fetchone()
        if row:
            self.cursor.execute('UPDATE crypto_orders SET views = views + 1 WHERE id = ?', (order_id,))
            self.conn.commit()
            
            return {
                'id': row[0],
                'user_id': row[1],
                'currency_id': row[2],
                'currency_name': row[3],
                'currency_icon': row[4],
                'order_type': row[5],
                'amount': row[6],
                'price': row[7],
                'total_fiat': row[8],
                'min_amount': row[9],
                'comment': row[10],
                'status': row[11],
                'created_at': row[12],
                'expires_at': row[13],
                'views': row[14],
                'favorites': row[15]
            }
        return None
    
    def update_crypto_order_amount(self, order_id, new_amount):
        if new_amount <= 0:
            self.cursor.execute('UPDATE crypto_orders SET status = "completed" WHERE id = ?', (order_id,))
        else:
            self.cursor.execute('UPDATE crypto_orders SET amount = ? WHERE id = ?', (new_amount, order_id))
        self.conn.commit()
    
    # ========== СДЕЛКИ ==========
    
    def create_trade(self, order_type, order_id, buyer_id, amount):
        if order_type == 'game':
            order = self.get_game_order(order_id)
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
            
            # Замораживаем деньги
            self.cursor.execute('''
                UPDATE users 
                SET balance = balance - ?,
                    locked_balance = locked_balance + ?
                WHERE user_id = ? AND balance >= ?
            ''', (total, total, buyer_id, total))
            
            self.cursor.execute('''
                INSERT INTO trades 
                (order_type, order_id, seller_id, buyer_id, item_name, item_icon, amount, price, total, commission,
                 created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                'game', order_id, order['user_id'], buyer_id, order['game_name'], order['game_icon'],
                amount, order['price'], total, commission, datetime.now(),
                datetime.now() + timedelta(minutes=ESCROW_TIME)
            ))
            
            trade_id = self.cursor.lastrowid
            
            # Обновляем ордер
            new_amount = order['amount'] - amount
            self.update_game_order_amount(order_id, new_amount)
            
        else:  # crypto
            order = self.get_crypto_order(order_id)
            if not order or order['status'] != 'active':
                return None
            
            if amount < order['min_amount'] or amount > order['amount']:
                return None
            
            total = amount * order['price']
            commission = total * (COMMISSION / 100)
            
            buyer = self.get_user(buyer_id)
            if not buyer or buyer['balance'] < total:
                return None
            
            self.cursor.execute('''
                UPDATE users 
                SET balance = balance - ?,
                    locked_balance = locked_balance + ?
                WHERE user_id = ? AND balance >= ?
            ''', (total, total, buyer_id, total))
            
            self.cursor.execute('''
                INSERT INTO trades 
                (order_type, order_id, seller_id, buyer_id, item_name, item_icon, amount, price, total, commission,
                 created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                'crypto', order_id, order['user_id'], buyer_id, order['currency_name'], order['currency_icon'],
                amount, order['price'], total, commission, datetime.now(),
                datetime.now() + timedelta(minutes=ESCROW_TIME)
            ))
            
            trade_id = self.cursor.lastrowid
            
            new_amount = order['amount'] - amount
            self.update_crypto_order_amount(order_id, new_amount)
        
        self.conn.commit()
        return trade_id
    
    def get_trade(self, trade_id):
        self.cursor.execute('SELECT * FROM trades WHERE id = ?', (trade_id,))
        row = self.cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'order_type': row[1],
                'order_id': row[2],
                'seller_id': row[3],
                'buyer_id': row[4],
                'item_name': row[5],
                'item_icon': row[6],
                'amount': row[7],
                'price': row[8],
                'total': row[9],
                'commission': row[10],
                'status': row[11],
                'payment_status': row[12],
                'created_at': row[13],
                'expires_at': row[14],
                'completed_at': row[15],
                'dispute_reason': row[16]
            }
        return None
    
    def confirm_payment(self, trade_id):
        self.cursor.execute('UPDATE trades SET payment_status = "paid" WHERE id = ?', (trade_id,))
        self.conn.commit()
    
    def complete_trade(self, trade_id):
        trade = self.get_trade(trade_id)
        if not trade:
            return False
        
        # Переводим деньги продавцу
        self.cursor.execute('''
            UPDATE users 
            SET locked_balance = locked_balance - ?,
                balance = balance + ?,
                deals_count = deals_count + 1,
                successful_deals = successful_deals + 1,
                deals_volume = deals_volume + ?
            WHERE user_id = ?
        ''', (trade['total'], trade['total'] - trade['commission'], trade['total'], trade['seller_id']))
        
        # Обновляем статистику покупателя
        self.cursor.execute('''
            UPDATE users 
            SET deals_count = deals_count + 1,
                deals_volume = deals_volume + ?
            WHERE user_id = ?
        ''', (trade['total'], trade['buyer_id']))
        
        # Обновляем сделку
        self.cursor.execute('''
            UPDATE trades 
            SET status = 'completed', 
                payment_status = 'confirmed',
                completed_at = ? 
            WHERE id = ?
        ''', (datetime.now(), trade_id))
        
        self.conn.commit()
        return True
    
    # ========== ОТЗЫВЫ ==========
    
    def add_review(self, trade_id, from_id, to_id, rating, comment):
        self.cursor.execute('''
            INSERT INTO reviews (trade_id, from_user_id, to_user_id, rating, comment, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (trade_id, from_id, to_id, rating, comment, datetime.now()))
        
        # Пересчитываем рейтинг
        self.cursor.execute('''
            SELECT AVG(rating) as avg_rating FROM reviews WHERE to_user_id = ?
        ''', (to_id,))
        avg = self.cursor.fetchone()[0]
        
        self.cursor.execute('''
            UPDATE users SET rating = ? WHERE user_id = ?
        ''', (avg, to_id))
        
        self.conn.commit()
    
    # ========== ИЗБРАННОЕ ==========
    
    def add_favorite(self, user_id, order_type, order_id):
        self.cursor.execute('''
            INSERT OR IGNORE INTO favorites (user_id, order_type, order_id, created_at)
            VALUES (?, ?, ?, ?)
        ''', (user_id, order_type, order_id, datetime.now()))
        self.conn.commit()
    
    def remove_favorite(self, user_id, order_type, order_id):
        self.cursor.execute('''
            DELETE FROM favorites WHERE user_id = ? AND order_type = ? AND order_id = ?
        ''', (user_id, order_type, order_id))
        self.conn.commit()
    
    def get_favorites(self, user_id):
        self.cursor.execute('''
            SELECT order_type, order_id FROM favorites WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))
        rows = self.cursor.fetchall()
        favorites = []
        for row in rows:
            if row[0] == 'game':
                order = self.get_game_order(row[1])
                if order:
                    favorites.append({
                        'type': 'game',
                        'order': order
                    })
            else:
                order = self.get_crypto_order(row[1])
                if order:
                    favorites.append({
                        'type': 'crypto',
                        'order': order
                    })
        return favorites

db = Database()

# ============================================
# 🤖 ИНИЦИАЛИЗАЦИЯ БОТА
# ============================================

storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=storage)

# ============================================
# 🎨 КЛАВИАТУРЫ
# ============================================

def main_keyboard():
    builder = ReplyKeyboardBuilder()
    buttons = [
        KeyboardButton(text="🎮 ИГРОВАЯ БИРЖА"),
        KeyboardButton(text="💰 КРИПТО-БИРЖА"),
        KeyboardButton(text="👤 МОЙ ПРОФИЛЬ"),
        KeyboardButton(text="👥 РЕФЕРАЛЫ"),
        KeyboardButton(text="📞 ПОДДЕРЖКА"),
        KeyboardButton(text="❓ ПОМОЩЬ")
    ]
    builder.add(*buttons)
    builder.adjust(2, 2, 2)
    return builder.as_markup(resize_keyboard=True)

def games_keyboard():
    builder = InlineKeyboardBuilder()
    popular = [g for g in GAMES if g['popular']][:6]
    for game in popular:
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

def back_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 НАЗАД", callback_data="back")
    builder.button(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu")
    builder.adjust(2)
    return builder.as_markup()

def order_actions_keyboard(order_id, order_type, is_owner=False, is_favorite=False):
    builder = InlineKeyboardBuilder()
    if not is_owner:
        builder.button(text="💎 КУПИТЬ", callback_data=f"buy_{order_type}_{order_id}")
    if is_favorite:
        builder.button(text="★ В ИЗБРАННОМ", callback_data=f"unfav_{order_type}_{order_id}")
    else:
        builder.button(text="☆ В ИЗБРАННОЕ", callback_data=f"fav_{order_type}_{order_id}")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="🔙 НАЗАД", callback_data="back"))
    return builder.as_markup()

def review_keyboard(trade_id, to_id):
    builder = InlineKeyboardBuilder()
    for i in range(1, 6):
        builder.button(text=f"{i}⭐", callback_data=f"rate_{trade_id}_{to_id}_{i}")
    builder.adjust(5)
    builder.row(InlineKeyboardButton(text="🔙 ПРОПУСТИТЬ", callback_data="skip_review"))
    return builder.as_markup()

# ============================================
# 🚀 КОМАНДА СТАРТ
# ============================================

@dp.message(CommandStart())
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
    
    welcome_text = (
        f"👋 <b>Привет, {user.first_name}!</b>\n\n"
        f"🎮 <b>P2P БИРЖА ИГРОВОЙ ВАЛЮТЫ И КРИПТЫ</b>\n\n"
        f"💰 <b>Твой баланс:</b> {WELCOME_BONUS} ₽\n"
        f"🔗 <b>Твоя реферальная ссылка:</b>\n"
        f"<code>https://t.me/{(await bot.get_me()).username}?start={referral_code}</code>\n\n"
        f"👇 <b>Выбери действие:</b>"
    )
    
    await message.answer(welcome_text, reply_markup=main_keyboard())

# ============================================
# 🎯 ОБРАБОТЧИКИ ГЛАВНОГО МЕНЮ
# ============================================

@dp.message(F.text == "🎮 ИГРОВАЯ БИРЖА")
async def games_section(message: Message):
    await message.answer("🎮 <b>ИГРОВАЯ БИРЖА</b>\n\nВыбери игру:", reply_markup=games_keyboard())

@dp.message(F.text == "💰 КРИПТО-БИРЖА")
async def crypto_section(message: Message):
    await message.answer("💰 <b>КРИПТО-БИРЖА</b>\n\nВыбери валюту:", reply_markup=crypto_keyboard())

@dp.message(F.text == "👤 МОЙ ПРОФИЛЬ")
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
        f"├ Рейтинг: {stars} ({rating:.1f})\n\n"
        f"💰 <b>Баланс:</b>\n"
        f"├ Доступно: {balance['available']:.0f} ₽\n"
        f"└ Заморожено: {balance['locked']:.0f} ₽\n"
    )
    
    await message.answer(text, reply_markup=back_keyboard())

@dp.message(F.text == "👥 РЕФЕРАЛЫ")
async def referrals_section(message: Message):
    user = db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Ошибка загрузки")
        return
    
    ref_link = f"https://t.me/{(await bot.get_me()).username}?start={user['referral_code']}"
    
    text = (
        f"👥 <b>РЕФЕРАЛЬНАЯ ПРОГРАММА</b>\n\n"
        f"🔗 <b>Твоя ссылка:</b>\n"
        f"<code>{ref_link}</code>\n\n"
        f"🎁 <b>Бонус:</b> {REFERRAL_BONUS}% от комиссии\n"
        f"💰 <b>Заработано:</b> {user['referral_balance']:.0f} ₽\n"
        f"👥 <b>Приглашено:</b> {user['referral_count']} чел\n\n"
        f"👇 <b>Делись ссылкой и зарабатывай!</b>"
    )
    
    await message.answer(text, reply_markup=back_keyboard())

@dp.message(F.text == "📞 ПОДДЕРЖКА")
async def support_section(message: Message, state: FSMContext):
    await message.answer(
        "📞 <b>ПОДДЕРЖКА</b>\n\n"
        "Напиши свой вопрос или проблему.\n"
        "Мы ответим в ближайшее время!",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(SupportStates.waiting_message)

@dp.message(F.text == "❓ ПОМОЩЬ")
async def help_section(message: Message):
    text = (
        "❓ <b>ПОМОЩЬ</b>\n\n"
        "📌 <b>Как купить?</b>\n"
        "1. Выбери игру/валюту\n"
        "2. Найди ордер и нажми «Купить»\n"
        "3. Введи количество\n"
        "4. Деньги заморозятся\n"
        "5. Свяжись с продавцом и оплати\n"
        "6. Нажми «Я оплатил»\n\n"
        f"⏱ <b>Время на оплату:</b> {ESCROW_TIME} мин\n"
        f"💰 <b>Комиссия:</b> {COMMISSION}%\n\n"
        f"📞 <b>Связь с поддержкой:</b> @{SUPPORT_USERNAME}"
    )
    await message.answer(text, reply_markup=back_keyboard())

# ============================================
# 🔄 НАВИГАЦИЯ
# ============================================

@dp.callback_query(lambda c: c.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("🏠 <b>ГЛАВНОЕ МЕНЮ</b>", reply_markup=main_keyboard())
    await callback.answer()

@dp.callback_query(lambda c: c.data == "back")
async def back_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("🎮 <b>ИГРОВАЯ БИРЖА</b>", reply_markup=games_keyboard())
    await callback.answer()

@dp.callback_query(lambda c: c.data == "cancel_order")
async def cancel_order_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Действие отменено", reply_markup=games_keyboard())
    await callback.answer()

# ============================================
# 🎮 ОБРАБОТЧИКИ ИГР
# ============================================

@dp.callback_query(lambda c: c.data.startswith('game_'))
async def show_game_orders(callback: CallbackQuery):
    game_id = callback.data.replace('game_', '')
    game = next((g for g in GAMES if g['id'] == game_id), None)
    if not game:
        await callback.answer("❌ Игра не найдена")
        return
    
    orders = db.get_game_orders(game_id=game_id)
    
    if not orders:
        text = f"{game['icon']} <b>{game['name']}</b>\n\n😕 Пока нет активных ордеров."
        builder = InlineKeyboardBuilder()
        builder.button(text="➕ СОЗДАТЬ ОРДЕР", callback_data=f"create_game_{game_id}")
        builder.row(InlineKeyboardButton(text="🔙 НАЗАД", callback_data="back"))
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
        await callback.answer()
        return
    
    text = f"{game['icon']} <b>{game['name']} — ОРДЕРА:</b>\n\n"
    builder = InlineKeyboardBuilder()
    
    for order in orders[:5]:
        emoji = "📈" if order['order_type'] == 'sell' else "📉"
        text += f"{emoji} {order['amount']:.0f} {game['currency']} × {order['price']}₽ = {order['total']:.0f}₽\n"
        builder.button(text=f"{order['amount']:.0f} {game['currency']}", callback_data=f"view_game_order_{order['id']}")
    
    builder.adjust(2)
    builder.row(
        InlineKeyboardButton(text="➕ СОЗДАТЬ ОРДЕР", callback_data=f"create_game_{game_id}"),
        InlineKeyboardButton(text="🔙 НАЗАД", callback_data="back")
    )
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith('view_game_order_'))
async def view_game_order(callback: CallbackQuery):
    order_id = int(callback.data.replace('view_game_order_', ''))
    order = db.get_game_order(order_id)
    if not order:
        await callback.answer("❌ Ордер не найден", show_alert=True)
        return
    
    favorites = db.get_favorites(callback.from_user.id)
    is_owner = (order['user_id'] == callback.from_user.id)
    is_favorite = any(f['order']['id'] == order_id and f['type'] == 'game' for f in favorites)
    
    emoji = "📈" if order['order_type'] == 'sell' else "📉"
    type_text = "ПРОДАЖА" if order['order_type'] == 'sell' else "ПОКУПКА"
    
    text = (
        f"{order['game_icon']} <b>{order['game_name']}</b>\n"
        f"{emoji} <b>{type_text}</b>\n\n"
        f"💰 <b>Количество:</b> {order['amount']} {order['game_currency']}\n"
        f"💵 <b>Цена:</b> {order['price']} ₽\n"
        f"💎 <b>Сумма:</b> {order['total']} ₽\n"
    )
    
    if order['comment']:
        text += f"\n📝 <b>Комментарий:</b>\n{order['comment']}\n"
    
    seller = db.get_user(order['user_id'])
    if seller:
        stars = "⭐" * int(seller['rating']) + ("✨" if seller['rating'] % 1 >= 0.5 else "")
        text += f"\n👤 <b>Продавец:</b> {seller['first_name']} {stars}\n"
    
    text += f"\n🕐 <b>Создан:</b> {order['created_at'][:16]}"
    
    await callback.message.edit_text(text, reply_markup=order_actions_keyboard(order_id, 'game', is_owner, is_favorite))
    await callback.answer()

# ============================================
# 💰 ОБРАБОТЧИКИ КРИПТЫ
# ============================================

@dp.callback_query(lambda c: c.data.startswith('crypto_'))
async def show_crypto_orders(callback: CallbackQuery):
    crypto_id = callback.data.replace('crypto_', '')
    crypto = next((c for c in CRYPTO if c['id'] == crypto_id), None)
    if not crypto:
        await callback.answer("❌ Валюта не найдена")
        return
    
    orders = db.get_crypto_orders(currency_id=crypto_id)
    
    if not orders:
        text = f"{crypto['icon']} <b>{crypto['name']}</b>\n\n😕 Пока нет активных ордеров."
        builder = InlineKeyboardBuilder()
        builder.button(text="➕ СОЗДАТЬ ОРДЕР", callback_data=f"create_crypto_{crypto_id}")
        builder.row(InlineKeyboardButton(text="🔙 НАЗАД", callback_data="back"))
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
        await callback.answer()
        return
    
    text = f"{crypto['icon']} <b>{crypto['name']} — ОРДЕРА:</b>\n\n"
    builder = InlineKeyboardBuilder()
    
    for order in orders[:5]:
        emoji = "📈" if order['order_type'] == 'sell' else "📉"
        text += f"{emoji} {order['amount']} {crypto_id.upper()} × {order['price']}₽ = {order['total_fiat']:.0f}₽\n"
        builder.button(text=f"{order['amount']} {crypto_id.upper()}", callback_data=f"view_crypto_order_{order['id']}")
    
    builder.adjust(2)
    builder.row(
        InlineKeyboardButton(text="➕ СОЗДАТЬ ОРДЕР", callback_data=f"create_crypto_{crypto_id}"),
        InlineKeyboardButton(text="🔙 НАЗАД", callback_data="back")
    )
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith('view_crypto_order_'))
async def view_crypto_order(callback: CallbackQuery):
    order_id = int(callback.data.replace('view_crypto_order_', ''))
    order = db.get_crypto_order(order_id)
    if not order:
        await callback.answer("❌ Ордер не найден", show_alert=True)
        return
    
    favorites = db.get_favorites(callback.from_user.id)
    is_owner = (order['user_id'] == callback.from_user.id)
    is_favorite = any(f['order']['id'] == order_id and f['type'] == 'crypto' for f in favorites)
    
    emoji = "📈" if order['order_type'] == 'sell' else "📉"
    type_text = "ПРОДАЖА" if order['order_type'] == 'sell' else "ПОКУПКА"
    
    text = (
        f"{order['currency_icon']} <b>{order['currency_name']}</b>\n"
        f"{emoji} <b>{type_text}</b>\n\n"
        f"💰 <b>Количество:</b> {order['amount']} {order['currency_id'].upper()}\n"
        f"💵 <b>Цена:</b> {order['price']} ₽\n"
        f"💎 <b>Сумма:</b> {order['total_fiat']:.0f} ₽\n"
    )
    
    if order['comment']:
        text += f"\n📝 <b>Комментарий:</b>\n{order['comment']}\n"
    
    seller = db.get_user(order['user_id'])
    if seller:
        stars = "⭐" * int(seller['rating']) + ("✨" if seller['rating'] % 1 >= 0.5 else "")
        text += f"\n👤 <b>Продавец:</b> {seller['first_name']} {stars}\n"
    
    text += f"\n🕐 <b>Создан:</b> {order['created_at'][:16]}"
    
    await callback.message.edit_text(text, reply_markup=order_actions_keyboard(order_id, 'crypto', is_owner, is_favorite))
    await callback.answer()

# ============================================
# 🚀 СОЗДАНИЕ ОРДЕРА
# ============================================

@dp.callback_query(lambda c: c.data == "create_game")
async def create_game_start(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    for game in GAMES[:8]:
        builder.button(text=f"{game['icon']} {game['name']}", callback_data=f"create_game_{game['id']}")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="❌ ОТМЕНА", callback_data="cancel_order"))
    await callback.message.edit_text("🎮 <b>СОЗДАНИЕ ОРДЕРА</b>\n\nВыбери игру:", reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(lambda c: c.data == "create_crypto")
async def create_crypto_start(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    for crypto in CRYPTO:
        builder.button(text=f"{crypto['icon']} {crypto['name']}", callback_data=f"create_crypto_{crypto['id']}")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="❌ ОТМЕНА", callback_data="cancel_order"))
    await callback.message.edit_text("💰 <b>СОЗДАНИЕ ОРДЕРА</b>\n\nВыбери валюту:", reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith('create_game_'))
async def create_game_order(callback: CallbackQuery, state: FSMContext):
    game_id = callback.data.replace('create_game_', '')
    game = next((g for g in GAMES if g['id'] == game_id), None)
    if not game:
        await callback.answer("❌ Игра не найдена")
        return
    
    await state.update_data(
        market_type='game',
        item_id=game_id,
        item_name=game['name'],
        item_icon=game['icon'],
        item_currency=game['currency']
    )
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
    
    await state.update_data(
        market_type='crypto',
        item_id=crypto_id,
        item_name=crypto['name'],
        item_icon=crypto['icon'],
        item_currency=crypto_id.upper()
    )
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
    await state.set_state(OrderStates.confirming)
    
    data = await state.get_data()
    total = data['amount'] * data['price']
    
    text = (
        f"{data['item_icon']} <b>ПРОВЕРЬ ДАННЫЕ:</b>\n\n"
        f"📌 <b>Тип:</b> {'📈 ПРОДАЖА' if data['order_type'] == 'sell' else '📉 ПОКУПКА'}\n"
        f"🎮 <b>Товар:</b> {data['item_name']}\n"
        f"💰 <b>Количество:</b> {data['amount']} {data['item_currency']}\n"
        f"💵 <b>Цена:</b> {data['price']} ₽\n"
        f"💎 <b>Сумма:</b> {total:.0f} ₽\n"
    )
    
    if data['comment']:
        text += f"📝 <b>Комментарий:</b> {data['comment']}\n"
    
    text += f"\n✅ <b>Всё верно?</b>"
    
    await message.answer(text, reply_markup=confirm_keyboard())

@dp.callback_query(OrderStates.confirming, lambda c: c.data == "confirm_order")
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        
        if data['market_type'] == 'game':
            order_id = db.create_game_order(
                user_id=callback.from_user.id,
                game_id=data['item_id'],
                order_type=data['order_type'],
                amount=data['amount'],
                price=data['price'],
                comment=data['comment']
            )
        else:
            order_id = db.create_crypto_order(
                user_id=callback.from_user.id,
                currency_id=data['item_id'],
                order_type=data['order_type'],
                amount=data['amount'],
                price=data['price'],
                comment=data['comment']
            )
        
        await state.clear()
        
        text = (
            f"✅ <b>ОРДЕР УСПЕШНО СОЗДАН!</b>\n\n"
            f"📋 <b>ID ордера:</b> #{order_id}\n\n"
            f"🔍 <b>ЧТО ДАЛЬШЕ?</b>\n"
            f"• Ордер появится в общем списке\n"
            f"• Покупатели смогут его найти\n"
            f"• Ты получишь уведомление о сделке\n\n"
            f"💰 <b>Удачных продаж!</b>"
        )
        
        builder = InlineKeyboardBuilder()
        if data['market_type'] == 'game':
            builder.button(text="📋 ПЕРЕЙТИ К ОРДЕРУ", callback_data=f"view_game_order_{order_id}")
        else:
            builder.button(text="📋 ПЕРЕЙТИ К ОРДЕРУ", callback_data=f"view_crypto_order_{order_id}")
        builder.row(InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu"))
        
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка создания ордера: {e}")
        await callback.message.edit_text("❌ Произошла ошибка. Попробуй позже.", reply_markup=back_keyboard())
        await callback.answer()

# ============================================
# 🛒 ПОКУПКА
# ============================================

@dp.callback_query(lambda c: c.data.startswith('buy_'))
async def buy_order_start(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split('_')
    order_type = parts[1]
    order_id = int(parts[2])
    
    if order_type == 'game':
        order = db.get_game_order(order_id)
    else:
        order = db.get_crypto_order(order_id)
    
    if not order or order['status'] != 'active':
        await callback.answer("❌ Ордер уже недоступен", show_alert=True)
        return
    
    if order['user_id'] == callback.from_user.id:
        await callback.answer("❌ Нельзя купить свой ордер", show_alert=True)
        return
    
    balance = db.get_balance(callback.from_user.id)
    min_total = order['min_amount'] * order['price']
    
    if balance['available'] < min_total:
        await callback.answer(f"❌ Недостаточно средств. Нужно минимум {min_total:.0f} ₽", show_alert=True)
        return
    
    await state.update_data(
        order_type=order_type,
        order_id=order_id,
        price=order['price']
    )
    await state.set_state(TradeStates.entering_amount)
    
    await callback.message.edit_text(
        f"💰 <b>ВВЕДИ КОЛИЧЕСТВО:</b>\n\n"
        f"Доступно: {order['amount']}\n"
        f"Цена: {order['price']} ₽\n"
        f"Мин. сделка: {order['min_amount']:.0f}\n\n"
        f"Твой баланс: {balance['available']} ₽",
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
    
    if data['order_type'] == 'game':
        order = db.get_game_order(data['order_id'])
    else:
        order = db.get_crypto_order(data['order_id'])
    
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
    balance = db.get_balance(message.from_user.id)
    
    if balance['available'] < total:
        await message.answer(f"❌ Недостаточно средств. Нужно {total:.0f} ₽", reply_markup=cancel_keyboard())
        return
    
    # Создаём сделку
    trade_id = db.create_trade(data['order_type'], data['order_id'], message.from_user.id, amount)
    
    if not trade_id:
        await message.answer("❌ Ошибка создания сделки")
        await state.clear()
        return
    
    await state.clear()
    
    await message.answer(
        f"✅ <b>СДЕЛКА СОЗДАНА!</b>\n\n"
        f"📋 <b>ID сделки:</b> #{trade_id}\n"
        f"💰 <b>Сумма:</b> {total:.0f} ₽\n\n"
        f"Деньги заморожены на твоём счету.\n"
        f"Свяжись с продавцом и переведи оплату.\n\n"
        f"✅ После оплаты нажми /confirm_{trade_id}",
        reply_markup=back_keyboard()
    )
    
    await bot.send_message(
        order['user_id'],
        f"🔄 <b>НОВАЯ СДЕЛКА!</b>\n\n"
        f"Покупатель хочет купить {amount} {order['game_name'] if data['order_type'] == 'game' else order['currency_name']}\n"
        f"на сумму {total:.0f} ₽\n\n"
        f"Деньги покупателя заморожены.\n"
        f"Ожидай оплаты."
    )

# ============================================
# 📞 ПОДДЕРЖКА
# ============================================

@dp.message(SupportStates.waiting_message)
async def support_message(message: Message, state: FSMContext):
    user = message.from_user
    text = message.text
    
    # Отправляем в чат поддержки
    support_text = (
        f"📞 <b>НОВОЕ СООБЩЕНИЕ В ПОДДЕРЖКУ</b>\n\n"
        f"👤 <b>Пользователь:</b> {user.first_name}\n"
        f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
        f"📱 <b>Username:</b> @{user.username}\n\n"
        f"📝 <b>Сообщение:</b>\n{text}"
    )
    
    await bot.send_message(SUPPORT_CHAT_ID, support_text)
    
    await state.clear()
    await message.answer(
        "✅ <b>СООБЩЕНИЕ ОТПРАВЛЕНО!</b>\n\n"
        "Мы ответим вам в ближайшее время.",
        reply_markup=main_keyboard()
    )

# ============================================
# 🚀 ЗАПУСК БОТА
# ============================================

async def main():
    print("\n" + "="*50)
    print("🔥 P2P БОТ ЗАПУЩЕН!")
    print("="*50)
    print(f"🤖 Бот: @{(await bot.get_me()).username}")
    print(f"👑 Админ ID: {ADMIN_ID}")
    print(f"📞 Чат поддержки: {SUPPORT_CHAT_ID}")
    print("="*50 + "\n")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
