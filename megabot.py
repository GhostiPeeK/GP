#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
██████╗ ██████╗ ██████╗     ███╗   ███╗███████╗ ██████╗  █████╗ 
██╔══██╗╚════██╗╚════██╗    ████╗ ████║██╔════╝██╔════╝ ██╔══██╗
██████╔╝ █████╔╝ █████╔╝    ██╔████╔██║█████╗  ██║  ███╗███████║
██╔═══╝  ╚═══██╗ ╚═══██╗    ██║╚██╔╝██║██╔══╝  ██║   ██║██╔══██║
██║     ██████╔╝██████╔╝    ██║ ╚═╝ ██║███████╗╚██████╔╝██║  ██║
╚═╝     ╚═════╝ ╚═════╝     ╚═╝     ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝
                                                                 
       ██████╗  █████╗ ███╗   ███╗██╗███╗   ██╗ ██████╗          
      ██╔════╝ ██╔══██╗████╗ ████║██║████╗  ██║██╔════╝          
      ██║  ███╗███████║██╔████╔██║██║██╔██╗ ██║██║  ███╗         
      ██║   ██║██╔══██║██║╚██╔╝██║██║██║╚██╗██║██║   ██║         
      ╚██████╔╝██║  ██║██║ ╚═╝ ██║██║██║ ╚████║╚██████╔╝         
       ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝ ╚═════╝          
                                                                 
              🎮 ИГРОВАЯ P2P БИРЖА + КРИПТО 💰               
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
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
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
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ============================================
# ТВОИ ДАННЫЕ (ВСТАВЬ СВОИ)
# ============================================

BOT_TOKEN = "8339352233:AAGixj9izEbOVKHvhpKeTd_4_Y2CP-f-ZhE"
ADMIN_ID = 2091630272
CRYPTO_API_KEY = "540261:AAzd4sQW2mo4I8UdxardSygAc3H3CSZbZBs"  # Для крипты

# ============================================
# НАСТРОЙКИ ПЛАТФОРМЫ
# ============================================

# Комиссия бота (%)
COMMISSION = 1.0

# Время на оплату (минут)
ESCROW_TIME = 60

# Минимальная сумма сделки (в рублях)
MIN_DEAL_AMOUNT = 100
MAX_DEAL_AMOUNT = 1000000

# Реферальная система
REFERRAL_BONUS = 10  # % от комиссии

# Telegram Stars (оставим для совместимости)
STARS_ENABLED = True
STARS_TO_RUB = 1.79

# ============================================
# ИГРЫ И ИХ ВАЛЮТЫ (РАЗДЕЛ 1)
# ============================================

GAMES = {
    'pubg': {
        'name': 'PUBG Mobile',
        'currency': 'UC',
        'icon': '🪖',
        'color': '🟡',
        'min_amount': 60,
        'max_amount': 50000,
        'popular': True,
        'category': 'shooter'
    },
    'brawl': {
        'name': 'Brawl Stars',
        'currency': 'гемы',
        'icon': '🥊',
        'color': '🔵',
        'min_amount': 30,
        'max_amount': 20000,
        'popular': True,
        'category': 'action'
    },
    'freefire': {
        'name': 'Free Fire',
        'currency': 'алмазы',
        'icon': '🔥',
        'color': '🔴',
        'min_amount': 100,
        'max_amount': 50000,
        'popular': True,
        'category': 'shooter'
    },
    'steam': {
        'name': 'Steam',
        'currency': 'руб',
        'icon': '🎮',
        'color': '⚫',
        'min_amount': 50,
        'max_amount': 15000,
        'popular': True,
        'category': 'platform'
    },
    'genshin': {
        'name': 'Genshin Impact',
        'currency': 'кристаллы',
        'icon': '✨',
        'color': '🟣',
        'min_amount': 60,
        'max_amount': 30000,
        'popular': True,
        'category': 'rpg'
    },
    'cod': {
        'name': 'Call of Duty',
        'currency': 'CP',
        'icon': '🔫',
        'color': '⚪',
        'min_amount': 80,
        'max_amount': 40000,
        'popular': True,
        'category': 'shooter'
    },
    'roblox': {
        'name': 'Roblox',
        'currency': 'Robux',
        'icon': '🎲',
        'color': '🟠',
        'min_amount': 100,
        'max_amount': 50000,
        'popular': True,
        'category': 'platform'
    },
    'fortnite': {
        'name': 'Fortnite',
        'currency': 'V-bucks',
        'icon': '🛡️',
        'color': '🟣',
        'min_amount': 1000,
        'max_amount': 50000,
        'popular': True,
        'category': 'shooter'
    },
    'standoff': {
        'name': 'Standoff 2',
        'currency': 'голда',
        'icon': '🔫',
        'color': '⚪',
        'min_amount': 50,
        'max_amount': 30000,
        'popular': False,
        'category': 'shooter'
    },
    'warface': {
        'name': 'Warface',
        'currency': 'кредиты',
        'icon': '💣',
        'color': '⚫',
        'min_amount': 100,
        'max_amount': 40000,
        'popular': False,
        'category': 'shooter'
    }
}

# ============================================
# КРИПТОВАЛЮТЫ (РАЗДЕЛ 2)
# ============================================

CRYPTO_CURRENCIES = {
    'USDT': {
        'name': 'Tether USDT',
        'icon': '💵',
        'network': 'TRC20',
        'min': 10,
        'max': 10000,
        'decimals': 2,
        'popular': True
    },
    'TON': {
        'name': 'Toncoin',
        'icon': '💎',
        'network': 'TON',
        'min': 5,
        'max': 5000,
        'decimals': 2,
        'popular': True
    },
    'BTC': {
        'name': 'Bitcoin',
        'icon': '₿',
        'network': 'BTC',
        'min': 0.001,
        'max': 1,
        'decimals': 6,
        'popular': True
    },
    'ETH': {
        'name': 'Ethereum',
        'icon': '♦️',
        'network': 'ERC20',
        'min': 0.01,
        'max': 50,
        'decimals': 4,
        'popular': False
    }
}

# ============================================
# ФИАТНЫЕ ВАЛЮТЫ
# ============================================

FIAT_CURRENCIES = {
    'RUB': {
        'name': 'Российский рубль',
        'icon': '🇷🇺',
        'symbol': '₽',
        'min': 100,
        'max': 1000000
    },
    'USD': {
        'name': 'Доллар США',
        'icon': '🇺🇸',
        'symbol': '$',
        'min': 10,
        'max': 10000
    },
    'EUR': {
        'name': 'Евро',
        'icon': '🇪🇺',
        'symbol': '€',
        'min': 10,
        'max': 10000
    }
}

# ============================================
# ПЛАТЁЖНЫЕ МЕТОДЫ
# ============================================

PAYMENT_METHODS = [
    {'id': 'sbp', 'name': 'СБП', 'icon': '💳', 'fiat': ['RUB']},
    {'id': 'card_rub', 'name': 'Карта РФ', 'icon': '💳', 'fiat': ['RUB']},
    {'id': 'yoomoney', 'name': 'ЮMoney', 'icon': '💰', 'fiat': ['RUB']},
    {'id': 'qiwi', 'name': 'Qiwi', 'icon': '📱', 'fiat': ['RUB']},
    {'id': 'cash_rub', 'name': 'Наличные', 'icon': '💵', 'fiat': ['RUB']},
    {'id': 'wise', 'name': 'Wise', 'icon': '🌍', 'fiat': ['USD', 'EUR']},
    {'id': 'paypal', 'name': 'PayPal', 'icon': '💎', 'fiat': ['USD', 'EUR']},
    {'id': 'cash_usd', 'name': 'Cash USD', 'icon': '💵', 'fiat': ['USD']},
    {'id': 'crypto', 'name': 'Крипта', 'icon': '₿', 'fiat': ['USD', 'EUR']}
]

# ============================================
# СОСТОЯНИЯ ДЛЯ FSM
# ============================================

class CreateGameOrder(StatesGroup):
    choosing_game = State()
    choosing_type = State()
    entering_amount = State()
    entering_price = State()
    entering_comment = State()
    choosing_payment = State()
    confirm = State()

class CreateCryptoOrder(StatesGroup):
    choosing_currency = State()
    choosing_fiat = State()
    choosing_type = State()
    entering_amount = State()
    entering_price = State()
    choosing_payment = State()
    confirm = State()

class TradeStates(StatesGroup):
    waiting_payment = State()
    waiting_confirmation = State()
    waiting_review = State()

class SupportStates(StatesGroup):
    waiting_message = State()

# ============================================
# БАЗА ДАННЫХ (СУПЕР-МОЩНАЯ)
# ============================================

class Database:
    def __init__(self, db_name="p2p_megabot.db"):
        self.db_name = db_name
        self.init_db()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # ========== ПОЛЬЗОВАТЕЛИ ==========
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                registered_at TIMESTAMP,
                referrer_id INTEGER DEFAULT NULL,
                referral_code TEXT UNIQUE,
                referral_balance REAL DEFAULT 0,
                rating REAL DEFAULT 5.0,
                deals_completed INTEGER DEFAULT 0,
                deals_total INTEGER DEFAULT 0,
                rating_count INTEGER DEFAULT 1,
                balance_rub REAL DEFAULT 0,
                
                -- Балансы для крипты
                usdt_balance REAL DEFAULT 0,
                ton_balance REAL DEFAULT 0,
                btc_balance REAL DEFAULT 0,
                eth_balance REAL DEFAULT 0,
                
                -- Заблокированные средства (эскроу)
                locked_usdt REAL DEFAULT 0,
                locked_ton REAL DEFAULT 0,
                locked_btc REAL DEFAULT 0,
                locked_eth REAL DEFAULT 0,
                
                -- Статистика
                is_verified BOOLEAN DEFAULT 0,
                is_banned BOOLEAN DEFAULT 0,
                last_activity TIMESTAMP,
                settings TEXT DEFAULT '{}',
                
                -- Достижения
                achievements TEXT DEFAULT '[]',
                
                FOREIGN KEY (referrer_id) REFERENCES users(user_id)
            )
        ''')
        
        # ========== ОРДЕРА (ИГРЫ) ==========
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                game_id TEXT,
                game_name TEXT,
                game_currency TEXT,
                type TEXT,
                amount REAL,
                price_per_unit REAL,
                total_price REAL,
                min_amount REAL DEFAULT 0,
                comment TEXT,
                payment_method TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP,
                expires_at TIMESTAMP,
                completed_at TIMESTAMP,
                views INTEGER DEFAULT 0,
                favorites INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # ========== ОРДЕРА (КРИПТА) ==========
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crypto_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                currency TEXT,
                fiat_currency TEXT,
                type TEXT,
                amount REAL,
                price_per_unit REAL,
                total_fiat REAL,
                min_amount REAL DEFAULT 0,
                comment TEXT,
                payment_method TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP,
                expires_at TIMESTAMP,
                completed_at TIMESTAMP,
                views INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # ========== СДЕЛКИ (ОБЩИЕ) ==========
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_type TEXT, -- 'game' или 'crypto'
                order_id INTEGER,
                seller_id INTEGER,
                buyer_id INTEGER,
                item_name TEXT,
                amount REAL,
                price_per_unit REAL,
                total_price REAL,
                commission REAL,
                commission_taken BOOLEAN DEFAULT 0,
                payment_method TEXT,
                payment_details TEXT,
                game_account TEXT,
                status TEXT DEFAULT 'pending',
                escrow_status TEXT DEFAULT 'pending',
                created_at TIMESTAMP,
                expires_at TIMESTAMP,
                completed_at TIMESTAMP,
                dispute_reason TEXT,
                dispute_resolved_by INTEGER,
                seller_rating INTEGER DEFAULT 0,
                buyer_rating INTEGER DEFAULT 0,
                FOREIGN KEY (seller_id) REFERENCES users(user_id),
                FOREIGN KEY (buyer_id) REFERENCES users(user_id)
            )
        ''')
        
        # ========== ОТЗЫВЫ ==========
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id INTEGER,
                from_user_id INTEGER,
                to_user_id INTEGER,
                rating INTEGER CHECK(rating >= 1 AND rating <= 5),
                comment TEXT,
                created_at TIMESTAMP,
                FOREIGN KEY (trade_id) REFERENCES trades(id)
            )
        ''')
        
        # ========== ИЗБРАННОЕ ==========
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS favorites (
                user_id INTEGER,
                order_type TEXT,
                order_id INTEGER,
                created_at TIMESTAMP,
                PRIMARY KEY (user_id, order_type, order_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # ========== УВЕДОМЛЕНИЯ ==========
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT,
                title TEXT,
                message TEXT,
                data TEXT,
                is_read BOOLEAN DEFAULT 0,
                created_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # ========== СТАТИСТИКА ==========
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE UNIQUE,
                new_users INTEGER DEFAULT 0,
                new_game_orders INTEGER DEFAULT 0,
                new_crypto_orders INTEGER DEFAULT 0,
                completed_trades INTEGER DEFAULT 0,
                total_volume_game REAL DEFAULT 0,
                total_volume_crypto REAL DEFAULT 0,
                commission_earned REAL DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
        logging.info("✅ MEGA P2P База данных готова")
    
    # ========== ПОЛЬЗОВАТЕЛИ ==========
    
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
        
        # Обновляем статистику
        today = datetime.now().date()
        cursor.execute('''
            INSERT INTO stats (date, new_users) VALUES (?, 1)
            ON CONFLICT(date) DO UPDATE SET new_users = new_users + 1
        ''', (today,))
        
        conn.commit()
        conn.close()
        
        if referrer_id:
            asyncio.create_task(notify_referrer(referrer_id, user_id))
        
        return ref_code
    
    def get_user(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        res = cursor.fetchone()
        conn.close()
        return dict(res) if res else None
    
    def update_user_activity(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET last_activity = ? WHERE user_id = ?', (datetime.now(), user_id))
        conn.commit()
        conn.close()
    
    def get_user_rating(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT rating, rating_count, deals_completed FROM users WHERE user_id = ?', (user_id,))
        res = cursor.fetchone()
        conn.close()
        return dict(res) if res else {'rating': 5.0, 'rating_count': 1, 'deals_completed': 0}
    
    # ========== БАЛАНСЫ ==========
    
    def get_balance(self, user_id, currency):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        currency = currency.lower()
        cursor.execute(f'SELECT {currency}_balance FROM users WHERE user_id = ?', (user_id,))
        res = cursor.fetchone()
        conn.close()
        return res[0] if res else 0
    
    def update_balance(self, user_id, currency, amount, operation='add', lock=False):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        currency = currency.lower()
        
        if lock:
            cursor.execute(f'''
                UPDATE users 
                SET locked_{currency} = locked_{currency} + ?,
                    {currency}_balance = {currency}_balance - ?
                WHERE user_id = ? AND {currency}_balance >= ?
            ''', (amount, amount, user_id, amount))
        else:
            if operation == 'add':
                cursor.execute(f'''
                    UPDATE users 
                    SET {currency}_balance = {currency}_balance + ?
                    WHERE user_id = ?
                ''', (amount, user_id))
            elif operation == 'subtract':
                cursor.execute(f'''
                    UPDATE users 
                    SET {currency}_balance = {currency}_balance - ?
                    WHERE user_id = ? AND {currency}_balance >= ?
                ''', (amount, user_id, amount))
            elif operation == 'unlock':
                cursor.execute(f'''
                    UPDATE users 
                    SET locked_{currency} = locked_{currency} - ?,
                        {currency}_balance = {currency}_balance + ?
                    WHERE user_id = ?
                ''', (amount, amount, user_id))
        
        conn.commit()
        conn.close()
    
    # ========== ИГРОВЫЕ ОРДЕРА ==========
    
    def create_game_order(self, user_id, game_id, order_type, amount, price, payment_method, comment=""):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        game = GAMES[game_id]
        total_price = amount * price
        
        min_amount = MIN_DEAL_AMOUNT / price
        
        cursor.execute('''
            INSERT INTO game_orders 
            (user_id, game_id, game_name, game_currency, type, amount, price_per_unit, total_price, 
             min_amount, comment, payment_method, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, game_id, game['name'], game['currency'], order_type, amount, price, total_price,
            min_amount, comment, payment_method, datetime.now(),
            datetime.now() + timedelta(hours=24)
        ))
        
        order_id = cursor.lastrowid
        
        today = datetime.now().date()
        cursor.execute('''
            INSERT INTO stats (date, new_game_orders) VALUES (?, 1)
            ON CONFLICT(date) DO UPDATE SET new_game_orders = new_game_orders + 1
        ''', (today,))
        
        conn.commit()
        conn.close()
        
        return order_id
    
    def get_game_orders(self, game_id=None, order_type=None, limit=20):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT o.*, u.username, u.first_name, u.rating, u.deals_completed, u.is_verified 
            FROM game_orders o 
            JOIN users u ON o.user_id = u.user_id 
            WHERE o.status = 'active'
        '''
        params = []
        
        if game_id:
            query += ' AND o.game_id = ?'
            params.append(game_id)
        
        if order_type:
            query += ' AND o.type = ?'
            params.append(order_type)
        
        query += ' ORDER BY o.created_at DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        res = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return res
    
    def get_game_order(self, order_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT o.*, u.username, u.first_name, u.rating, u.deals_completed, u.is_verified 
            FROM game_orders o 
            JOIN users u ON o.user_id = u.user_id 
            WHERE o.id = ?
        ''', (order_id,))
        
        res = cursor.fetchone()
        
        if res:
            cursor.execute('UPDATE game_orders SET views = views + 1 WHERE id = ?', (order_id,))
            conn.commit()
        
        conn.close()
        return dict(res) if res else None
    
    # ========== КРИПТО-ОРДЕРА ==========
    
    def create_crypto_order(self, user_id, currency, fiat_currency, order_type, amount, price, payment_method, comment=""):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        total_fiat = amount * price
        
        cursor.execute('''
            INSERT INTO crypto_orders 
            (user_id, currency, fiat_currency, type, amount, price_per_unit, total_fiat, 
             comment, payment_method, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, currency, fiat_currency, order_type, amount, price, total_fiat,
            comment, payment_method, datetime.now(),
            datetime.now() + timedelta(hours=24)
        ))
        
        order_id = cursor.lastrowid
        
        today = datetime.now().date()
        cursor.execute('''
            INSERT INTO stats (date, new_crypto_orders) VALUES (?, 1)
            ON CONFLICT(date) DO UPDATE SET new_crypto_orders = new_crypto_orders + 1
        ''', (today,))
        
        conn.commit()
        conn.close()
        
        return order_id
    
    def get_crypto_orders(self, currency=None, fiat_currency=None, order_type=None, limit=20):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT o.*, u.username, u.first_name, u.rating, u.deals_completed, u.is_verified 
            FROM crypto_orders o 
            JOIN users u ON o.user_id = u.user_id 
            WHERE o.status = 'active'
        '''
        params = []
        
        if currency:
            query += ' AND o.currency = ?'
            params.append(currency)
        
        if fiat_currency:
            query += ' AND o.fiat_currency = ?'
            params.append(fiat_currency)
        
        if order_type:
            query += ' AND o.type = ?'
            params.append(order_type)
        
        query += ' ORDER BY o.created_at DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        res = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return res
    
    def get_crypto_order(self, order_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT o.*, u.username, u.first_name, u.rating, u.deals_completed, u.is_verified 
            FROM crypto_orders o 
            JOIN users u ON o.user_id = u.user_id 
            WHERE o.id = ?
        ''', (order_id,))
        
        res = cursor.fetchone()
        
        if res:
            cursor.execute('UPDATE crypto_orders SET views = views + 1 WHERE id = ?', (order_id,))
            conn.commit()
        
        conn.close()
        return dict(res) if res else None
    
    # ========== СДЕЛКИ ==========
    
    def create_trade(self, order_type, order_id, buyer_id, amount):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if order_type == 'game':
            cursor.execute('SELECT * FROM game_orders WHERE id = ? AND status = "active"', (order_id,))
            order = cursor.fetchone()
            if not order:
                conn.close()
                return None
            
            order = dict(order)
            
            if amount < order['min_amount'] or amount > order['amount']:
                conn.close()
                return None
            
            total_price = amount * order['price_per_unit']
            commission = total_price * (COMMISSION / 100)
            
            cursor.execute('''
                INSERT INTO trades 
                (order_type, order_id, seller_id, buyer_id, item_name, amount, price_per_unit, total_price, 
                 commission, payment_method, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                'game', order_id, order['user_id'], buyer_id, 
                f"{order['game_name']} {order['game_currency']}",
                amount, order['price_per_unit'], total_price, commission,
                order['payment_method'], datetime.now(),
                datetime.now() + timedelta(minutes=ESCROW_TIME)
            ))
            
            new_amount = order['amount'] - amount
            if new_amount <= 0:
                cursor.execute('UPDATE game_orders SET status = "completed", completed_at = ? WHERE id = ?', 
                              (datetime.now(), order_id))
            else:
                cursor.execute('UPDATE game_orders SET amount = ? WHERE id = ?', (new_amount, order_id))
        
        else:  # crypto
            cursor.execute('SELECT * FROM crypto_orders WHERE id = ? AND status = "active"', (order_id,))
            order = cursor.fetchone()
            if not order:
                conn.close()
                return None
            
            order = dict(order)
            
            if amount < order['min_amount'] or amount > order['amount']:
                conn.close()
                return None
            
            total_fiat = amount * order['price_per_unit']
            commission = total_fiat * (COMMISSION / 100)
            
            cursor.execute('''
                INSERT INTO trades 
                (order_type, order_id, seller_id, buyer_id, item_name, amount, price_per_unit, total_price, 
                 commission, payment_method, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                'crypto', order_id, order['user_id'], buyer_id,
                f"{order['currency']} ({order['fiat_currency']})",
                amount, order['price_per_unit'], total_fiat, commission,
                order['payment_method'], datetime.now(),
                datetime.now() + timedelta(minutes=ESCROW_TIME)
            ))
            
            new_amount = order['amount'] - amount
            if new_amount <= 0:
                cursor.execute('UPDATE crypto_orders SET status = "completed", completed_at = ? WHERE id = ?', 
                              (datetime.now(), order_id))
            else:
                cursor.execute('UPDATE crypto_orders SET amount = ? WHERE id = ?', (new_amount, order_id))
        
        trade_id = cursor.lastrowid
        
        # Обновляем статистику пользователей
        cursor.execute('''
            UPDATE users SET deals_total = deals_total + 1
            WHERE user_id IN (?, ?)
        ''', (order['user_id'], buyer_id))
        
        conn.commit()
        conn.close()
        
        return trade_id
    
    def get_trade(self, trade_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT t.*, 
                   s.username as seller_username, s.first_name as seller_name,
                   b.username as buyer_username, b.first_name as buyer_name
            FROM trades t
            JOIN users s ON t.seller_id = s.user_id
            JOIN users b ON t.buyer_id = b.user_id
            WHERE t.id = ?
        ''', (trade_id,))
        
        res = cursor.fetchone()
        conn.close()
        return dict(res) if res else None
    
    def get_user_trades(self, user_id, limit=10):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM trades 
            WHERE seller_id = ? OR buyer_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, user_id, limit))
        
        res = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return res
    
    def lock_funds_for_trade(self, trade_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM trades WHERE id = ?', (trade_id,))
        trade = cursor.fetchone()
        
        if not trade:
            conn.close()
            return False
        
        trade = dict(trade)
        
        if trade['order_type'] == 'crypto':
            currency = trade['item_name'].split()[0].lower()
            cursor.execute(f'''
                UPDATE users 
                SET locked_{currency} = locked_{currency} + ?,
                    {currency}_balance = {currency}_balance - ?
                WHERE user_id = ? AND {currency}_balance >= ?
            ''', (trade['amount'], trade['amount'], trade['seller_id'], trade['amount']))
            
            if cursor.rowcount == 0:
                conn.close()
                return False
        
        cursor.execute('UPDATE trades SET escrow_status = "locked" WHERE id = ?', (trade_id,))
        
        conn.commit()
        conn.close()
        return True
    
    def release_funds_to_buyer(self, trade_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM trades WHERE id = ?', (trade_id,))
        trade = cursor.fetchone()
        
        if not trade:
            conn.close()
            return False
        
        trade = dict(trade)
        
        if trade['order_type'] == 'crypto':
            currency = trade['item_name'].split()[0].lower()
            
            cursor.execute(f'''
                UPDATE users 
                SET locked_{currency} = locked_{currency} - ?,
                    {currency}_balance = {currency}_balance + ?
                WHERE user_id = ?
            ''', (trade['amount'], trade['amount'], trade['buyer_id']))
        
        if not trade['commission_taken']:
            cursor.execute('''
                UPDATE users 
                SET balance_rub = balance_rub + ?
                WHERE user_id = ?
            ''', (trade['commission'], ADMIN_ID))
            
            cursor.execute('UPDATE trades SET commission_taken = 1 WHERE id = ?', (trade_id,))
        
        cursor.execute('''
            UPDATE trades 
            SET status = 'completed', 
                escrow_status = 'released', 
                completed_at = ? 
            WHERE id = ?
        ''', (datetime.now(), trade_id))
        
        cursor.execute('''
            UPDATE users 
            SET deals_completed = deals_completed + 1
            WHERE user_id = ?
        ''', (trade['seller_id'],))
        
        conn.commit()
        conn.close()
        return True
    
    # ========== ОТЗЫВЫ ==========
    
    def add_review(self, trade_id, from_user_id, to_user_id, rating, comment):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO reviews (trade_id, from_user_id, to_user_id, rating, comment, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (trade_id, from_user_id, to_user_id, rating, comment, datetime.now()))
        
        cursor.execute('''
            SELECT AVG(rating) as avg_rating, COUNT(*) as count
            FROM reviews 
            WHERE to_user_id = ?
        ''', (to_user_id,))
        
        stats = cursor.fetchone()
        
        cursor.execute('''
            UPDATE users 
            SET rating = ?, rating_count = ?
            WHERE user_id = ?
        ''', (stats['avg_rating'] or 5.0, stats['count'] or 1, to_user_id))
        
        conn.commit()
        conn.close()
    
    # ========== ИЗБРАННОЕ ==========
    
    def add_favorite(self, user_id, order_type, order_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO favorites (user_id, order_type, order_id, created_at)
            VALUES (?, ?, ?, ?)
        ''', (user_id, order_type, order_id, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def remove_favorite(self, user_id, order_type, order_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM favorites 
            WHERE user_id = ? AND order_type = ? AND order_id = ?
        ''', (user_id, order_type, order_id))
        
        conn.commit()
        conn.close()
    
    def get_favorites(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM favorites WHERE user_id = ?', (user_id,))
        res = cursor.fetchall()
        conn.close()
        return [dict(r) for r in res]
    
    # ========== УВЕДОМЛЕНИЯ ==========
    
    def add_notification(self, user_id, type, title, message, data=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO notifications (user_id, type, title, message, data, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, type, title, message, json.dumps(data) if data else None, datetime.now()))
        
        notification_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        asyncio.create_task(send_notification(user_id, title, message))
        
        return notification_id
    
    def get_unread_notifications(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM notifications 
            WHERE user_id = ? AND is_read = 0
            ORDER BY created_at DESC
        ''', (user_id,))
        
        res = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return res
    
    def mark_notification_read(self, notification_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE notifications SET is_read = 1 WHERE id = ?', (notification_id,))
        conn.commit()
        conn.close()
    
    # ========== СТАТИСТИКА ==========
    
    def get_stats(self, days=7):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        result = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            cursor.execute('SELECT * FROM stats WHERE date = ?', (date,))
            row = cursor.fetchone()
            if row:
                result.append(dict(row))
            else:
                result.append({
                    'date': date,
                    'new_users': 0,
                    'new_game_orders': 0,
                    'new_crypto_orders': 0,
                    'completed_trades': 0,
                    'total_volume_game': 0,
                    'total_volume_crypto': 0,
                    'commission_earned': 0
                })
        
        conn.close()
        return result

db = Database()

# ============================================
# УВЕДОМЛЕНИЯ
# ============================================

async def send_notification(user_id, title, message):
    try:
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="📨 Посмотреть", callback_data="notifications")
        keyboard.button(text="🔕 Не беспокоить", callback_data="notifications_off")
        keyboard.adjust(2)
        
        await bot.send_message(
            user_id,
            f"🔔 <b>{title}</b>\n\n{message}",
            reply_markup=keyboard.as_markup()
        )
    except:
        pass

async def notify_admin(text):
    try:
        await bot.send_message(ADMIN_ID, f"👑 <b>Админ:</b>\n\n{text}")
    except:
        pass

async def notify_referrer(referrer_id, referral_id):
    try:
        text = (
            f"👥 <b>Новый реферал!</b>\n\n"
            f"По вашей ссылке зарегистрировался новый пользователь!\n"
            f"После его первой сделки вы получите бонус {REFERRAL_BONUS}% от комиссии."
        )
        await bot.send_message(referrer_id, text)
    except:
        pass

# ============================================
# КЛАВИАТУРЫ (БОМБИЧЕСКИЙ ДИЗАЙН)
# ============================================

def get_main_menu():
    """Главное меню (шедевр)"""
    builder = ReplyKeyboardBuilder()
    
    buttons = [
        KeyboardButton(text="🎮 ИГРОВАЯ БИРЖА"),
        KeyboardButton(text="💰 КРИПТО-БИРЖА"),
        KeyboardButton(text="📊 МОЙ ПРОФИЛЬ"),
        KeyboardButton(text="👥 РЕФЕРАЛЫ"),
        KeyboardButton(text="⭐ ИЗБРАННОЕ"),
        KeyboardButton(text="📞 ПОМОЩЬ")
    ]
    
    builder.add(*buttons)
    builder.adjust(2, 2, 2)
    
    return builder.as_markup(resize_keyboard=True)

def get_game_menu():
    """Меню игровой биржи"""
    builder = InlineKeyboardBuilder()
    
    # Популярные игры (первые 4)
    popular = [(k, v) for k, v in GAMES.items() if v['popular']][:4]
    for game_id, game in popular:
        builder.button(
            text=f"{game['icon']} {game['name']}",
            callback_data=f"game_{game_id}"
        )
    
    builder.adjust(2)
    
    # Кнопки действий
    builder.row(
        InlineKeyboardButton(text="📋 Все игры", callback_data="games_all"),
        InlineKeyboardButton(text="➕ Создать ордер", callback_data="create_game_order"),
        width=2
    )
    
    builder.row(
        InlineKeyboardButton(text="📊 Мои ордера", callback_data="my_game_orders"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main"),
        width=2
    )
    
    return builder.as_markup()

def get_crypto_menu():
    """Меню крипто-биржи"""
    builder = InlineKeyboardBuilder()
    
    # Популярные криптовалюты
    popular = [(k, v) for k, v in CRYPTO_CURRENCIES.items() if v['popular']]
    for curr_id, curr in popular:
        builder.button(
            text=f"{curr['icon']} {curr_id} ({curr['network']})",
            callback_data=f"crypto_{curr_id}"
        )
    
    builder.adjust(2)
    
    # Кнопки действий
    builder.row(
        InlineKeyboardButton(text="📋 Все валюты", callback_data="crypto_all"),
        InlineKeyboardButton(text="➕ Создать ордер", callback_data="create_crypto_order"),
        width=2
    )
    
    builder.row(
        InlineKeyboardButton(text="📊 Мои ордера", callback_data="my_crypto_orders"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main"),
        width=2
    )
    
    return builder.as_markup()

def get_order_type_keyboard():
    """Выбор типа ордера (покупка/продажа)"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📈 КУПИТЬ", callback_data="order_type_buy")
    builder.button(text="📉 ПРОДАТЬ", callback_data="order_type_sell")
    builder.adjust(2)
    
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back"))
    
    return builder.as_markup()

def get_payment_methods_keyboard(fiat_currency='RUB'):
    """Выбор платёжного метода"""
    builder = InlineKeyboardBuilder()
    
    for method in PAYMENT_METHODS:
        if fiat_currency in method['fiat']:
            builder.button(
                text=f"{method['icon']} {method['name']}",
                callback_data=f"payment_{method['id']}"
            )
    
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back"))
    
    return builder.as_markup()

def get_fiat_keyboard():
    """Выбор фиатной валюты"""
    builder = InlineKeyboardBuilder()
    
    for code, fiat in FIAT_CURRENCIES.items():
        builder.button(
            text=f"{fiat['icon']} {code} ({fiat['symbol']})",
            callback_data=f"fiat_{code}"
        )
    
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back"))
    
    return builder.as_markup()

def get_profile_keyboard(user_id):
    """Профиль пользователя"""
    builder = InlineKeyboardBuilder()
    
    user = db.get_user(user_id)
    if user:
        buttons = [
            InlineKeyboardButton(text="📊 Мои сделки", callback_data="my_trades"),
            InlineKeyboardButton(text="💰 Баланс", callback_data="my_balance"),
            InlineKeyboardButton(text="⭐ Мой рейтинг", callback_data="my_rating"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"),
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")
        ]
        
        for btn in buttons:
            builder.row(btn)
    
    return builder.as_markup()

def get_trade_keyboard(trade_id, user_role):
    """Клавиатура для сделки"""
    builder = InlineKeyboardBuilder()
    
    if user_role == 'buyer':
        builder.button(text="💳 Я оплатил", callback_data=f"trade_paid_{trade_id}")
    elif user_role == 'seller':
        builder.button(text="✅ Подтвердить получение", callback_data=f"trade_confirm_{trade_id}")
    
    builder.button(text="⚠️ Открыть спор", callback_data=f"trade_dispute_{trade_id}")
    builder.button(text="🔄 Обновить", callback_data=f"trade_refresh_{trade_id}")
    builder.adjust(1)
    
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main"))
    
    return builder.as_markup()

def get_order_card(order, order_type):
    """Создаёт красивую карточку ордера"""
    if order_type == 'game':
        game = GAMES.get(order['game_id'], {})
        icon = game.get('icon', '🎮')
        
        card = (
            f"{icon} <b>{order['game_name']}</b>\n"
            f"└ {'📈 ПРОДАЖА' if order['type'] == 'sell' else '📉 ПОКУПКА'}\n\n"
            
            f"💰 <b>Количество:</b> {order['amount']:.0f} {order['game_currency']}\n"
            f"💵 <b>Цена:</b> {order['price_per_unit']:.2f} ₽ за единицу\n"
            f"💎 <b>Общая сумма:</b> {order['total_price']:.0f} ₽\n"
            f"📦 <b>Мин. сделка:</b> {order['min_amount']:.0f} {order['game_currency']}\n\n"
            
            f"👤 <b>Продавец:</b> {order.get('first_name', 'User')}"
        )
        
        if order.get('is_verified'):
            card += " ✅"
        
        card += f"\n⭐ <b>Рейтинг:</b> {order.get('rating', 5.0):.1f} ({order.get('deals_completed', 0)} сделок)"
        
        if order.get('comment'):
            card += f"\n📝 <b>Комментарий:</b> {order['comment']}"
        
        card += f"\n🕐 <b>Создан:</b> {order['created_at'][:16]}"
        
    else:  # crypto
        currency = CRYPTO_CURRENCIES.get(order['currency'], {})
        fiat = FIAT_CURRENCIES.get(order['fiat_currency'], {})
        
        card = (
            f"{currency.get('icon', '💰')} <b>{order['currency']}</b>\n"
            f"└ {'📈 ПРОДАЖА' if order['type'] == 'sell' else '📉 ПОКУПКА'}\n\n"
            
            f"💰 <b>Количество:</b> {order['amount']:.2f} {order['currency']}\n"
            f"💵 <b>Цена:</b> {order['price_per_unit']:.2f} {fiat.get('symbol', '₽')}\n"
            f"💎 <b>Общая сумма:</b> {order['total_fiat']:.0f} {fiat.get('symbol', '₽')}\n\n"
            
            f"👤 <b>Продавец:</b> {order.get('first_name', 'User')}"
        )
        
        if order.get('is_verified'):
            card += " ✅"
        
        card += f"\n⭐ <b>Рейтинг:</b> {order.get('rating', 5.0):.1f} ({order.get('deals_completed', 0)} сделок)"
        
        if order.get('comment'):
            card += f"\n📝 <b>Комментарий:</b> {order['comment']}"
        
        card += f"\n🕐 <b>Создан:</b> {order['created_at'][:16]}"
    
    return card

# ============================================
# БОТ И ДИСПЕТЧЕР
# ============================================

storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=storage)

# Временное хранилище
user_data = {}

# ============================================
# ОБРАБОТЧИК КОМАНДЫ START
# ============================================

@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    user = message.from_user
    args = message.text.split()
    ref_code = args[1] if len(args) > 1 else None
    
    # Регистрируем пользователя
    referral_code = db.add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        referrer_code=ref_code
    )
    
    # Приветствие (БОМБИЧЕСКОЕ)
    welcome_text = (
        f"🌟 <b>ДОБРО ПОЖАЛОВАТЬ В MEGA P2P!</b> 🌟\n\n"
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
    
    await message.answer(welcome_text, reply_markup=get_main_menu())
    
    # Отправляем уведомление админу
    await notify_admin(f"👤 Новый пользователь: {user.first_name} (@{user.username})\nID: {user.id}")

# ============================================
# ОБРАБОТЧИКИ ГЛАВНОГО МЕНЮ
# ============================================

@dp.message(lambda m: m.text == "🎮 ИГРОВАЯ БИРЖА")
async def game_market(message: Message):
    text = (
        "🎮 <b>ИГРОВАЯ P2P БИРЖА</b>\n\n"
        "🔥 <b>Популярные игры:</b>\n"
    )
    
    for game_id, game in GAMES.items():
        if game['popular']:
            text += f"{game['icon']} {game['name']} — {game['currency']}\n"
    
    text += "\n👇 <b>Выбери действие:</b>"
    
    await message.answer(text, reply_markup=get_game_menu())

@dp.message(lambda m: m.text == "💰 КРИПТО-БИРЖА")
async def crypto_market(message: Message):
    text = (
        "💰 <b>КРИПТО-БИРЖА P2P</b>\n\n"
        "💎 <b>Доступные валюты:</b>\n"
    )
    
    for curr_id, curr in CRYPTO_CURRENCIES.items():
        text += f"{curr['icon']} {curr_id} ({curr['network']}) — {curr['min']}-{curr['max']}\n"
    
    text += "\n👇 <b>Выбери действие:</b>"
    
    await message.answer(text, reply_markup=get_crypto_menu())

@dp.message(lambda m: m.text == "📊 МОЙ ПРОФИЛЬ")
async def my_profile(message: Message):
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message.answer("❌ Ошибка загрузки профиля")
        return
    
    rating = user['rating']
    stars = "⭐" * int(rating) + "✨" * (5 - int(rating))
    
    text = (
        f"👤 <b>ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ</b>\n\n"
        
        f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
        f"📱 <b>Username:</b> @{user['username'] if user['username'] else 'нет'}\n"
        f"📅 <b>С нами:</b> {user['registered_at'][:10]}\n\n"
        
        f"⭐ <b>Рейтинг:</b> {rating:.1f} {stars}\n"
        f"📊 <b>Сделок:</b> {user['deals_completed']} / {user['deals_total']}\n\n"
        
        f"💰 <b>Баланс (RUB):</b> {user['balance_rub']:.2f} ₽\n"
    )
    
    if user['is_verified']:
        text += f"\n✅ <b>Верифицированный продавец</b>\n"
    
    await message.answer(text, reply_markup=get_profile_keyboard(user_id))

@dp.message(lambda m: m.text == "👥 РЕФЕРАЛЫ")
async def referrals_section(message: Message):
    user = db.get_user(message.from_user.id)
    
    if not user:
        return
    
    ref_link = f"https://t.me/{(await bot.get_me()).username}?start={user['referral_code']}"
    
    text = (
        "👥 <b>РЕФЕРАЛЬНАЯ ПРОГРАММА</b>\n\n"
        f"🔗 <b>Твоя ссылка:</b>\n"
        f"<code>{ref_link}</code>\n\n"
        
        f"🎁 <b>Бонус:</b> {REFERRAL_BONUS}% от комиссии с каждой сделки реферала\n"
        f"💰 <b>Заработано:</b> {user['referral_balance']:.2f} ₽\n\n"
        
        f"📊 <b>Статистика:</b>\n"
        f"├ Приглашено: ...\n"
        f"└ Активных: ...\n\n"
        
        f"👇 <b>Делись ссылкой и зарабатывай!</b>"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📤 Поделиться", switch_inline_query=f"🔥 Зарабатывай со мной! {ref_link}")
    builder.button(text="🏠 Главное меню", callback_data="back_to_main")
    builder.adjust(1)
    
    await message.answer(text, reply_markup=builder.as_markup())

@dp.message(lambda m: m.text == "⭐ ИЗБРАННОЕ")
async def favorites_section(message: Message):
    user_id = message.from_user.id
    favorites = db.get_favorites(user_id)
    
    if not favorites:
        await message.answer(
            "⭐ <b>Избранное</b>\n\n"
            "У тебя пока нет избранных ордеров.\n"
            "Добавляй их звездочкой в объявлениях!",
            reply_markup=get_back_to_main()
        )
        return
    
    text = "⭐ <b>Твои избранные ордера:</b>\n\n"
    
    for fav in favorites[:5]:
        if fav['order_type'] == 'game':
            order = db.get_game_order(fav['order_id'])
            if order:
                text += f"🎮 {order['game_name']} — {order['amount']} {order['game_currency']}\n"
        else:
            order = db.get_crypto_order(fav['order_id'])
            if order:
                text += f"💰 {order['currency']} — {order['amount']}\n"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Все избранные", callback_data="favorites_all")
    builder.button(text="🏠 Главное меню", callback_data="back_to_main")
    builder.adjust(1)
    
    await message.answer(text, reply_markup=builder.as_markup())

@dp.message(lambda m: m.text == "📞 ПОМОЩЬ")
async def help_section(message: Message):
    text = (
        "📞 <b>ЦЕНТР ПОМОЩИ</b>\n\n"
        
        "❓ <b>Часто задаваемые вопросы:</b>\n\n"
        
        "1️⃣ <b>Как проходит сделка?</b>\n"
        "   • Находишь ордер\n"
        "   • Нажимаешь «Купить»\n"
        "   • Вводишь свои данные\n"
        "   • Бот блокирует средства\n"
        "   • Платишь продавцу\n"
        "   • Получаешь товар\n\n"
        
        "2️⃣ <b>Что такое эскроу?</b>\n"
        "   Бот выступает гарантом и блокирует\n"
        "   средства продавца до подтверждения\n\n"
        
        "3️⃣ <b>Как долго ждать?</b>\n"
        f"   На оплату даётся {ESCROW_TIME} минут\n\n"
        
        "4️⃣ <b>Спорные ситуации</b>\n"
        "   Если что-то пошло не так,\n"
        "   можно открыть спор и админ разберётся\n\n"
        
        "👨‍💻 <b>Связь с админом:</b>\n"
        "   @p2p_support_bot"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📨 Написать админу", callback_data="support")
    builder.button(text="🏠 Главное меню", callback_data="back_to_main")
    builder.adjust(1)
    
    await message.answer(text, reply_markup=builder.as_markup())

# ============================================
# ОБРАБОТЧИКИ НАВИГАЦИИ
# ============================================

@dp.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        "🏠 <b>Главное меню</b>\n\nВыбери раздел:",
        reply_markup=get_main_menu()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "back")
async def go_back(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    
    if current_state:
        await state.set_state(CreateGameOrder.choosing_game)
        await callback.message.edit_text(
            "🎮 <b>Выбери игру:</b>",
            reply_markup=get_game_menu()
        )
    
    await callback.answer()

# ============================================
# ОБРАБОТЧИКИ ИГРОВОЙ БИРЖИ
# ============================================

@dp.callback_query(lambda c: c.data.startswith('game_'))
async def show_game_orders(callback: CallbackQuery):
    game_id = callback.data.replace('game_', '')
    game = GAMES[game_id]
    
    orders = db.get_game_orders(game_id=game_id)
    
    if not orders:
        await callback.message.edit_text(
            f"{game['icon']} <b>{game['name']}</b>\n\n"
            f"Пока нет активных ордеров.\n"
            f"Создай первый! 🚀",
            reply_markup=get_game_menu()
        )
        await callback.answer()
        return
    
    text = f"{game['icon']} <b>{game['name']} — активные ордера:</b>\n\n"
    
    for order in orders[:5]:
        text += f"{'📈' if order['type'] == 'sell' else '📉'} "
        text += f"{order['amount']:.0f} {order['game_currency']} × {order['price_per_unit']:.2f}₽ = {order['total_price']:.0f}₽\n"
        text += f"👤 {order['first_name']} ⭐{order['rating']:.1f}\n\n"
    
    builder = InlineKeyboardBuilder()
    for order in orders[:3]:
        builder.button(
            text=f"{'📈' if order['type'] == 'sell' else '📉'} {order['amount']:.0f} {order['game_currency']}",
            callback_data=f"view_game_order_{order['id']}"
        )
    
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text="➕ Создать ордер", callback_data=f"create_game_order_{game_id}"),
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_games")
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
    
    card = get_order_card(order, 'game')
    
    builder = InlineKeyboardBuilder()
    
    # Кнопка покупки/продажи
    if order['type'] == 'sell':
        builder.button(text="💎 Купить", callback_data=f"buy_game_{order_id}")
    else:
        builder.button(text="💎 Продать", callback_data=f"sell_game_{order_id}")
    
    # Кнопка избранного
    builder.button(text="⭐ В избранное", callback_data=f"fav_game_{order_id}")
    
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=f"game_{order['game_id']}"))
    
    await callback.message.edit_text(card, reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith('buy_game_'))
async def buy_game_order(callback: CallbackQuery, state: FSMContext):
    order_id = int(callback.data.replace('buy_game_', ''))
    order = db.get_game_order(order_id)
    
    if not order or order['status'] != 'active':
        await callback.answer("❌ Ордер уже недоступен", show_alert=True)
        return
    
    await state.update_data(order_id=order_id, order_type='game')
    
    await callback.message.edit_text(
        f"🛒 <b>Покупка {order['game_name']}</b>\n\n"
        f"💰 Доступно: {order['amount']} {order['game_currency']}\n"
        f"💵 Цена: {order['price_per_unit']} ₽ за единицу\n\n"
        f"📝 <b>Введи количество, которое хочешь купить:</b>"
    )
    
    await state.set_state(CreateGameOrder.entering_amount)
    await callback.answer()

# ============================================
# FSM ДЛЯ СОЗДАНИЯ ОРДЕРА (ИГРЫ)
# ============================================

@dp.callback_query(lambda c: c.data == "create_game_order")
async def create_game_order_start(callback: CallbackQuery, state: FSMContext):
    # Показываем список игр
    builder = InlineKeyboardBuilder()
    
    for game_id, game in GAMES.items():
        if game['popular']:
            builder.button(
                text=f"{game['icon']} {game['name']}",
                callback_data=f"create_game_{game_id}"
            )
    
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_games"))
    
    await callback.message.edit_text(
        "🎮 <b>Выбери игру для создания ордера:</b>",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith('create_game_'))
async def create_game_order_type(callback: CallbackQuery, state: FSMContext):
    game_id = callback.data.replace('create_game_', '')
    
    await state.update_data(game_id=game_id)
    await state.set_state(CreateGameOrder.choosing_type)
    
    await callback.message.edit_text(
        f"{GAMES[game_id]['icon']} <b>{GAMES[game_id]['name']}</b>\n\n"
        f"Ты хочешь продать или купить?",
        reply_markup=get_order_type_keyboard()
    )
    await callback.answer()

@dp.callback_query(CreateGameOrder.choosing_type, lambda c: c.data.startswith('order_type_'))
async def create_game_order_amount(callback: CallbackQuery, state: FSMContext):
    order_type = callback.data.replace('order_type_', '')
    
    await state.update_data(order_type=order_type)
    await state.set_state(CreateGameOrder.entering_amount)
    
    await callback.message.edit_text(
        f"💰 <b>Введи количество:</b>\n\n"
        f"Минимум: {MIN_DEAL_AMOUNT} ₽ в эквиваленте"
    )
    await callback.answer()

# ============================================
# ЗАПУСК БОТА
# ============================================

async def main():
    logging.info("🚀 ЗАПУСК MEGA P2P БОТА...")
    
    print("\n" + "="*60)
    print("🔥 MEGA P2P БОТ С БОМБИЧЕСКИМ ДИЗАЙНОМ")
    print("="*60)
    print(f"🤖 Bot: @{(await bot.get_me()).username}")
    print(f"👑 Admin ID: {ADMIN_ID}")
    print(f"🎮 Игр: {len(GAMES)}")
    print(f"💰 Криптовалют: {len(CRYPTO_CURRENCIES)}")
    print("="*60 + "\n")
    
    await bot.send_message(
        ADMIN_ID,
        "🚀 <b>MEGA P2P БОТ ЗАПУЩЕН!</b>\n\n"
        f"🎮 Игр: {len(GAMES)}\n"
        f"💰 Криптовалют: {len(CRYPTO_CURRENCIES)}\n"
        f"⚡ Комиссия: {COMMISSION}%\n\n"
        f"📊 Всё работает!"
    )
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
