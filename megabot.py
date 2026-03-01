#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                        ║
║    ██████╗ ██████╗ ██████╗     ███╗   ███╗███████╗ ██████╗  █████╗ ██████╗  ██████╗  ║
║    ██╔══██╗╚════██╗╚════██╗    ████╗ ████║██╔════╝██╔════╝ ██╔══██╗██╔══██╗██╔════╝  ║
║    ██████╔╝ █████╔╝ █████╔╝    ██╔████╔██║█████╗  ██║  ███╗███████║██████╔╝██║  ███╗ ║
║    ██╔═══╝  ╚═══██╗ ╚═══██╗    ██║╚██╔╝██║██╔══╝  ██║   ██║██╔══██║██╔══██╗██║   ██║ ║
║    ██║     ██████╔╝██████╔╝    ██║ ╚═╝ ██║███████╗╚██████╔╝██║  ██║██║  ██║╚██████╔╝ ║
║    ╚═╝     ╚═════╝ ╚═════╝     ╚═╝     ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝  ║
║                                                                                        ║
║    ███████╗██╗███╗   ██╗ █████╗ ██╗         ██████╗  ██████╗ ████████╗               ║
║    ██╔════╝██║████╗  ██║██╔══██╗██║         ██╔══██╗██╔═══██╗╚══██╔══╝               ║
║    █████╗  ██║██╔██╗ ██║███████║██║         ██████╔╝██║   ██║   ██║                  ║
║    ██╔══╝  ██║██║╚██╗██║██╔══██║██║         ██╔══██╗██║   ██║   ██║                  ║
║    ██║     ██║██║ ╚████║██║  ██║███████╗    ██████╔╝╚██████╔╝   ██║                  ║
║    ╚═╝     ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝    ╚═════╝  ╚═════╝    ╚═╝                  ║
║                                                                                        ║
║                      🎮 P2P ГЕЙМИНГ МАРКЕТПЛЕЙС + КРИПТО-БИРЖА 🎮                    ║
║                           👑 VER 6.0 - АБСОЛЮТНЫЙ РАЗЪЕБ 👑                           ║
║                                                                                        ║
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
import hashlib
import hmac
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from collections import defaultdict
from decimal import Decimal, ROUND_DOWN

# Aiogram 3.x
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message, CallbackQuery, LabeledPrice,
    PreCheckoutQuery, InlineKeyboardMarkup, 
    InlineKeyboardButton, ReplyKeyboardMarkup,
    KeyboardButton, FSInputFile, ChatMemberUpdated
)
from aiogram.client.bot import DefaultBotProperties
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode, ChatMemberStatus

# ============================================
# 🔥 ТВОИ ДАННЫЕ (ВСТАВЬ СВОИ) 🔥
# ============================================

BOT_TOKEN = "8339352233:AAGixj9izEbOVKHvhpKeTd_4_Y2CP-f-ZhE"
ADMIN_ID = 2091630272
CHANNEL_ID = -1001234567890  # ID твоего канала

# ============================================
# ⚡ НАСТРОЙКИ ПЛАТФОРМЫ ⚡
# ============================================

COMMISSION = 1.0  # Комиссия бота (%)
ESCROW_TIME = 60  # Время на оплату (минут)
MIN_AMOUNT = 100  # Минимальная сумма сделки (руб)
MAX_AMOUNT = 1000000  # Максимальная сумма сделки (руб)
REFERRAL_BONUS = 10  # Бонус рефереру (%)
SUPPORT_USERNAME = "p2p_support"
BOT_VERSION = "6.0 - АБСОЛЮТНЫЙ РАЗЪЕБ"
WELCOME_BONUS = 100  # Приветственный бонус (руб)
DAILY_BONUS = 10  # Ежедневный бонус (руб)
VIP_LEVELS = {
    'bronze': {'deals': 5, 'commission': 0.9, 'name': '🥉 Бронза'},
    'silver': {'deals': 20, 'commission': 0.8, 'name': '🥈 Серебро'},
    'gold': {'deals': 50, 'commission': 0.7, 'name': '🥇 Золото'},
    'platinum': {'deals': 100, 'commission': 0.6, 'name': '💎 Платина'},
    'diamond': {'deals': 200, 'commission': 0.5, 'name': '💎💎 Бриллиант'}
}

# ============================================
# 🎮 ИГРЫ (ПОЛНЫЙ СПИСОК) 🎮
# ============================================

GAMES = [
    {"id": "pubg", "name": "PUBG Mobile", "currency": "UC", "icon": "🪖", "popular": True, "color": "#FF6B6B"},
    {"id": "brawl", "name": "Brawl Stars", "currency": "гемы", "icon": "🥊", "popular": True, "color": "#4ECDC4"},
    {"id": "freefire", "name": "Free Fire", "currency": "алмазы", "icon": "🔥", "popular": True, "color": "#FF8C42"},
    {"id": "steam", "name": "Steam", "currency": "руб", "icon": "🎮", "popular": True, "color": "#1E3C72"},
    {"id": "genshin", "name": "Genshin Impact", "currency": "кристаллы", "icon": "✨", "popular": True, "color": "#A78BFA"},
    {"id": "cod", "name": "Call of Duty", "currency": "CP", "icon": "🔫", "popular": True, "color": "#2C3E50"},
    {"id": "roblox", "name": "Roblox", "currency": "Robux", "icon": "🎲", "popular": True, "color": "#FFD93D"},
    {"id": "fortnite", "name": "Fortnite", "currency": "V-bucks", "icon": "🛡️", "popular": True, "color": "#9B59B6"},
    {"id": "standoff", "name": "Standoff 2", "currency": "голда", "icon": "🔫", "popular": False, "color": "#34495E"},
    {"id": "warface", "name": "Warface", "currency": "кредиты", "icon": "💣", "popular": False, "color": "#7F8C8D"},
    {"id": "apex", "name": "Apex Legends", "currency": "монеты", "icon": "🔺", "popular": False, "color": "#E74C3C"},
    {"id": "valorant", "name": "Valorant", "currency": "VP", "icon": "🔫", "popular": False, "color": "#FD1D1D"},
    {"id": "dota2", "name": "Dota 2", "currency": "уровни", "icon": "⚔️", "popular": True, "color": "#E34C26"},
    {"id": "csgo", "name": "CS:GO", "currency": "скины", "icon": "🔫", "popular": True, "color": "#F9A825"},
    {"id": "wot", "name": "World of Tanks", "currency": "золото", "icon": "💥", "popular": False, "color": "#B71C1C"},
]

# ============================================
# 💰 КРИПТОВАЛЮТЫ
# ============================================

CRYPTO = [
    {"id": "usdt", "name": "USDT", "network": "TRC20", "icon": "💵", "color": "🟢", "popular": True},
    {"id": "ton", "name": "TON", "network": "TON", "icon": "💎", "color": "🔵", "popular": True},
    {"id": "btc", "name": "Bitcoin", "network": "BTC", "icon": "₿", "color": "🟠", "popular": True},
    {"id": "eth", "name": "Ethereum", "network": "ERC20", "icon": "♦️", "color": "🔵", "popular": True},
    {"id": "bnb", "name": "BNB", "network": "BSC", "icon": "🟡", "color": "🟡", "popular": False},
    {"id": "sol", "name": "Solana", "network": "SOL", "icon": "◎", "color": "🟣", "popular": False},
]

# ============================================
# 💳 ПЛАТЁЖНЫЕ МЕТОДЫ
# ============================================

PAYMENT_METHODS = [
    {"id": "sbp", "name": "СБП", "icon": "💳", "description": "Мгновенный перевод по номеру телефона"},
    {"id": "card", "name": "Карта РФ", "icon": "💳", "description": "Перевод на карту любого банка России"},
    {"id": "yoomoney", "name": "ЮMoney", "icon": "💰", "description": "Перевод на кошелёк ЮMoney"},
    {"id": "qiwi", "name": "Qiwi", "icon": "📱", "description": "Перевод на Qiwi кошелёк"},
    {"id": "cash", "name": "Наличные", "icon": "💵", "description": "При личной встрече"},
    {"id": "crypto", "name": "Крипта", "icon": "₿", "description": "Перевод USDT/TON/BTC"},
    {"id": "wise", "name": "Wise", "icon": "🌍", "description": "Международный перевод"},
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

class SupportStates(StatesGroup):
    waiting_message = State()

# ============================================
# 💾 БАЗА ДАННЫХ (ПРОДВИНУТАЯ)
# ============================================

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('p2p_megabot.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()
    
    def create_tables(self):
        # Пользователи (расширенная версия)
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
                balance REAL DEFAULT 1000,
                locked_balance REAL DEFAULT 0,
                crypto_balance TEXT DEFAULT '{}',
                vip_level TEXT DEFAULT 'bronze',
                achievements TEXT DEFAULT '[]',
                is_verified BOOLEAN DEFAULT 0,
                is_banned BOOLEAN DEFAULT 0,
                last_activity TIMESTAMP,
                last_daily_bonus TIMESTAMP,
                daily_bonus_streak INTEGER DEFAULT 0,
                settings TEXT DEFAULT '{"notifications": true, "language": "ru"}',
                FOREIGN KEY (referrer_id) REFERENCES users(user_id)
            )
        ''')
        
        # Ордера (игровые)
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
                payment_method TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP,
                expires_at TIMESTAMP,
                views INTEGER DEFAULT 0,
                favorites INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Ордера (крипто)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS crypto_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                currency_id TEXT,
                currency_name TEXT,
                currency_icon TEXT,
                fiat_currency TEXT DEFAULT 'RUB',
                order_type TEXT,
                amount REAL,
                price REAL,
                total_fiat REAL,
                min_amount REAL,
                comment TEXT,
                payment_method TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP,
                expires_at TIMESTAMP,
                views INTEGER DEFAULT 0,
                favorites INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Сделки (универсальные)
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
                escrow_status TEXT DEFAULT 'pending',
                payment_status TEXT DEFAULT 'waiting',
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
        
        # Отзывы
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id INTEGER,
                from_user_id INTEGER,
                to_user_id INTEGER,
                rating INTEGER CHECK(rating >= 1 AND rating <= 5),
                comment TEXT,
                created_at TIMESTAMP,
                FOREIGN KEY (trade_id) REFERENCES trades(id),
                FOREIGN KEY (from_user_id) REFERENCES users(user_id),
                FOREIGN KEY (to_user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Избранное
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS favorites (
                user_id INTEGER,
                order_type TEXT,
                order_id INTEGER,
                created_at TIMESTAMP,
                PRIMARY KEY (user_id, order_type, order_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Платежи (пополнения/выводы)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT,
                amount REAL,
                currency TEXT,
                method TEXT,
                status TEXT DEFAULT 'pending',
                payment_id TEXT UNIQUE,
                created_at TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
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
                created_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Статистика
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE UNIQUE,
                new_users INTEGER DEFAULT 0,
                new_orders INTEGER DEFAULT 0,
                completed_trades INTEGER DEFAULT 0,
                total_volume REAL DEFAULT 0,
                commission_earned REAL DEFAULT 0
            )
        ''')
        
        # Чаты поддержки
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS support_chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message TEXT,
                admin_reply TEXT,
                created_at TIMESTAMP,
                replied_at TIMESTAMP,
                is_closed BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        self.conn.commit()
        logging.info("✅ MEGA БАЗА ДАННЫХ ГОТОВА")
    
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
                    UPDATE users SET referral_balance = referral_balance + ?,
                                    referral_count = referral_count + 1
                    WHERE user_id = ?
                ''', (WELCOME_BONUS * (REFERRAL_BONUS/100), referrer_id))
        
        self.cursor.execute('''
            INSERT INTO users 
            (user_id, username, first_name, last_name, registered_at, referrer_id, referral_code, last_activity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, username, first_name, last_name,
            datetime.now(), referrer_id, ref_code,
            datetime.now()
        ))
        
        # Обновляем статистику
        today = datetime.now().date()
        self.cursor.execute('''
            INSERT INTO stats (date, new_users) VALUES (?, 1)
            ON CONFLICT(date) DO UPDATE SET new_users = new_users + 1
        ''', (today,))
        
        self.conn.commit()
        
        # Создаём приветственное уведомление
        self.add_notification(
            user_id,
            'welcome',
            '🌟 Добро пожаловать!',
            f'Твой баланс: {WELCOME_BONUS} ₽. Удачных сделок!'
        )
        
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
                'crypto_balance': json.loads(row[15]) if row[15] else {},
                'vip_level': row[16],
                'achievements': json.loads(row[17]) if row[17] else [],
                'is_verified': row[18],
                'is_banned': row[19],
                'last_activity': row[20],
                'last_daily_bonus': row[21],
                'daily_bonus_streak': row[22],
                'settings': json.loads(row[23]) if row[23] else {"notifications": True, "language": "ru"}
            }
        return None
    
    def update_user_activity(self, user_id):
        self.cursor.execute('UPDATE users SET last_activity = ? WHERE user_id = ?', (datetime.now(), user_id))
        self.conn.commit()
    
    def get_user_rating(self, user_id):
        self.cursor.execute('SELECT rating, rating_count, deals_completed FROM users WHERE user_id = ?', (user_id,))
        res = self.cursor.fetchone()
        return {'rating': res[0], 'count': res[1], 'deals': res[2]} if res else None
    
    def get_vip_level(self, deals_count):
        for level, data in VIP_LEVELS.items():
            if deals_count >= data['deals']:
                return level, data
        return 'bronze', VIP_LEVELS['bronze']
    
    def get_user_stats(self, user_id):
        self.cursor.execute('''
            SELECT COUNT(*) as total_trades,
                   SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_trades,
                   SUM(total) as total_volume
            FROM trades 
            WHERE seller_id = ? OR buyer_id = ?
        ''', (user_id, user_id))
        row = self.cursor.fetchone()
        
        self.cursor.execute('''
            SELECT AVG(rating) as avg_rating, COUNT(*) as reviews_count
            FROM reviews WHERE to_user_id = ?
        ''', (user_id,))
        rev = self.cursor.fetchone()
        
        return {
            'total_trades': row[0] or 0,
            'completed_trades': row[1] or 0,
            'total_volume': row[2] or 0,
            'avg_rating': rev[0] or 5.0,
            'reviews_count': rev[1] or 0
        }
    
    # ========== БАЛАНСЫ ==========
    
    def get_balance(self, user_id):
        self.cursor.execute('SELECT balance, locked_balance FROM users WHERE user_id = ?', (user_id,))
        row = self.cursor.fetchone()
        return {'available': row[0] or 0, 'locked': row[1] or 0} if row else {'available': 0, 'locked': 0}
    
    def add_balance(self, user_id, amount):
        self.cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def lock_balance(self, user_id, amount):
        self.cursor.execute('''
            UPDATE users 
            SET balance = balance - ?,
                locked_balance = locked_balance + ?
            WHERE user_id = ? AND balance >= ?
        ''', (amount, amount, user_id, amount))
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def unlock_balance(self, user_id, amount):
        self.cursor.execute('''
            UPDATE users 
            SET locked_balance = locked_balance - ?,
                balance = balance + ?
            WHERE user_id = ? AND locked_balance >= ?
        ''', (amount, amount, user_id, amount))
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def transfer_balance(self, from_id, to_id, amount, commission):
        # Разблокируем у покупателя
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
        return True
    
    def get_daily_bonus(self, user_id):
        self.cursor.execute('SELECT last_daily_bonus, daily_bonus_streak FROM users WHERE user_id = ?', (user_id,))
        row = self.cursor.fetchone()
        
        now = datetime.now()
        last_bonus = datetime.fromisoformat(row[0]) if row[0] else None
        streak = row[1] or 0
        
        if last_bonus and last_bonus.date() == now.date():
            return False, streak
        
        # Проверяем streak
        if last_bonus and (now - last_bonus).days == 1:
            streak += 1
        else:
            streak = 1
        
        bonus_amount = DAILY_BONUS * streak
        
        self.cursor.execute('''
            UPDATE users 
            SET balance = balance + ?,
                last_daily_bonus = ?,
                daily_bonus_streak = ?
            WHERE user_id = ?
        ''', (bonus_amount, now, streak, user_id))
        
        self.conn.commit()
        return True, streak, bonus_amount
    
    # ========== ОРДЕРА (ИГРЫ) ==========
    
    def create_game_order(self, user_id, game_id, order_type, amount, price, comment, payment_method):
        game = next((g for g in GAMES if g['id'] == game_id), None)
        if not game:
            return None
        
        total = amount * price
        min_amount = MIN_AMOUNT / price
        
        self.cursor.execute('''
            INSERT INTO game_orders 
            (user_id, game_id, game_name, game_icon, game_currency, order_type, amount, price, total, 
             min_amount, comment, payment_method, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, game_id, game['name'], game['icon'], game['currency'], order_type, amount, price, total,
            min_amount, comment, payment_method, datetime.now(),
            datetime.now() + timedelta(hours=24)
        ))
        
        order_id = self.cursor.lastrowid
        
        # Обновляем статистику
        today = datetime.now().date()
        self.cursor.execute('''
            INSERT INTO stats (date, new_orders) VALUES (?, 1)
            ON CONFLICT(date) DO UPDATE SET new_orders = new_orders + 1
        ''', (today,))
        
        self.conn.commit()
        return order_id
    
    def get_game_orders(self, game_id=None, order_type=None, status='active', limit=20):
        query = 'SELECT * FROM game_orders WHERE status = ?'
        params = [status]
        
        if game_id:
            query += ' AND game_id = ?'
            params.append(game_id)
        
        if order_type:
            query += ' AND order_type = ?'
            params.append(order_type)
        
        query += ' ORDER BY created_at DESC LIMIT ?'
        params.append(limit)
        
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
                'payment_method': row[12],
                'status': row[13],
                'created_at': row[14],
                'expires_at': row[15],
                'views': row[16],
                'favorites': row[17]
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
                'payment_method': row[12],
                'status': row[13],
                'created_at': row[14],
                'expires_at': row[15],
                'views': row[16],
                'favorites': row[17]
            }
        return None
    
    def update_game_order_amount(self, order_id, new_amount):
        if new_amount <= 0:
            self.cursor.execute('UPDATE game_orders SET status = "completed" WHERE id = ?', (order_id,))
        else:
            self.cursor.execute('UPDATE game_orders SET amount = ? WHERE id = ?', (new_amount, order_id))
        self.conn.commit()
    
    # ========== ОРДЕРА (КРИПТА) ==========
    
    def create_crypto_order(self, user_id, currency_id, order_type, amount, price, comment, payment_method):
        currency = next((c for c in CRYPTO if c['id'] == currency_id), None)
        if not currency:
            return None
        
        total = amount * price
        min_amount = MIN_AMOUNT / price
        
        self.cursor.execute('''
            INSERT INTO crypto_orders 
            (user_id, currency_id, currency_name, currency_icon, order_type, amount, price, 
             total_fiat, min_amount, comment, payment_method, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, currency_id, currency['name'], currency['icon'], order_type, amount, price,
            total, min_amount, comment, payment_method, datetime.now(),
            datetime.now() + timedelta(hours=24)
        ))
        
        order_id = self.cursor.lastrowid
        
        # Обновляем статистику
        today = datetime.now().date()
        self.cursor.execute('''
            INSERT INTO stats (date, new_orders) VALUES (?, 1)
            ON CONFLICT(date) DO UPDATE SET new_orders = new_orders + 1
        ''', (today,))
        
        self.conn.commit()
        return order_id
    
    def get_crypto_orders(self, currency_id=None, order_type=None, status='active', limit=20):
        query = 'SELECT * FROM crypto_orders WHERE status = ?'
        params = [status]
        
        if currency_id:
            query += ' AND currency_id = ?'
            params.append(currency_id)
        
        if order_type:
            query += ' AND order_type = ?'
            params.append(order_type)
        
        query += ' ORDER BY created_at DESC LIMIT ?'
        params.append(limit)
        
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
                'fiat_currency': row[5],
                'order_type': row[6],
                'amount': row[7],
                'price': row[8],
                'total_fiat': row[9],
                'min_amount': row[10],
                'comment': row[11],
                'payment_method': row[12],
                'status': row[13],
                'created_at': row[14],
                'expires_at': row[15],
                'views': row[16],
                'favorites': row[17]
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
                'fiat_currency': row[5],
                'order_type': row[6],
                'amount': row[7],
                'price': row[8],
                'total_fiat': row[9],
                'min_amount': row[10],
                'comment': row[11],
                'payment_method': row[12],
                'status': row[13],
                'created_at': row[14],
                'expires_at': row[15],
                'views': row[16],
                'favorites': row[17]
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
            self.lock_balance(buyer_id, total)
            
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
            
            self.lock_balance(buyer_id, total)
            
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
        
        # Уведомления
        self.add_notification(
            order['user_id'],
            'new_trade',
            '🔄 Новая сделка!',
            f'Кто-то хочет купить {amount} {order["game_name"] if order_type=="game" else order["currency_name"]}'
        )
        
        # Обновляем статистику
        today = datetime.now().date()
        self.cursor.execute('''
            INSERT INTO stats (date, total_volume, commission_earned) VALUES (?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET 
                total_volume = total_volume + ?,
                commission_earned = commission_earned + ?
        ''', (today, total, commission, total, commission))
        
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
                'escrow_status': row[11],
                'payment_status': row[12],
                'created_at': row[13],
                'expires_at': row[14],
                'completed_at': row[15],
                'dispute_reason': row[16],
                'dispute_resolved_by': row[17],
                'seller_rating': row[18],
                'buyer_rating': row[19]
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
                'order_type': row[1],
                'item_name': row[5],
                'amount': row[7],
                'total': row[9],
                'status': row[11],
                'payment_status': row[12],
                'created_at': row[13],
                'role': 'seller' if row[3] == user_id else 'buyer'
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
                escrow_status = 'released', 
                payment_status = 'confirmed',
                completed_at = ? 
            WHERE id = ?
        ''', (datetime.now(), trade_id))
        
        self.conn.commit()
        
        # Добавляем уведомления
        self.add_notification(trade['seller_id'], 'trade_complete', '✅ Сделка завершена!', 
                             f'Ты получил {trade["total"] - trade["commission"]} ₽')
        self.add_notification(trade['buyer_id'], 'trade_complete', '✅ Сделка завершена!', 
                             f'Ты купил {trade["amount"]} {trade["item_name"]}')
        
        # Обновляем статистику
        today = datetime.now().date()
        self.cursor.execute('''
            UPDATE stats SET completed_trades = completed_trades + 1 WHERE date = ?
        ''', (today,))
        
        self.conn.commit()
        
        return True
    
    def cancel_trade(self, trade_id):
        trade = self.get_trade(trade_id)
        if not trade:
            return False
        
        # Возвращаем деньги покупателю
        self.unlock_balance(trade['buyer_id'], trade['total'])
        
        # Возвращаем товар продавцу
        if trade['order_type'] == 'game':
            order = self.get_game_order(trade['order_id'])
            if order:
                new_amount = order['amount'] + trade['amount']
                self.update_game_order_amount(trade['order_id'], new_amount)
            else:
                # Создаём новый ордер, если старого нет
                self.cursor.execute('''
                    INSERT INTO game_orders 
                    (user_id, game_id, game_name, game_icon, order_type, amount, price, total, min_amount, payment_method, created_at)
                    SELECT user_id, game_id, game_name, game_icon, order_type, ?, price, ?, min_amount, payment_method, ?
                    FROM game_orders WHERE id = ?
                ''', (trade['amount'], trade['total'], datetime.now(), trade['order_id']))
        else:
            order = self.get_crypto_order(trade['order_id'])
            if order:
                new_amount = order['amount'] + trade['amount']
                self.update_crypto_order_amount(trade['order_id'], new_amount)
        
        self.cursor.execute('''
            UPDATE trades SET status = 'cancelled' WHERE id = ?
        ''', (trade_id,))
        
        self.conn.commit()
        
        self.add_notification(trade['seller_id'], 'trade_cancelled', '❌ Сделка отменена', '')
        self.add_notification(trade['buyer_id'], 'trade_cancelled', '❌ Сделка отменена', '')
        
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
    
    def get_user_reviews(self, user_id, limit=10):
        self.cursor.execute('''
            SELECT r.*, u.first_name, u.username 
            FROM reviews r
            JOIN users u ON r.from_user_id = u.user_id
            WHERE r.to_user_id = ?
            ORDER BY r.created_at DESC
            LIMIT ?
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
                'created_at': row[6],
                'from_name': row[7],
                'from_username': row[8]
            })
        return reviews
    
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
    
    # ========== УВЕДОМЛЕНИЯ ==========
    
    def add_notification(self, user_id, type, title, message, data=None):
        self.cursor.execute('''
            INSERT INTO notifications (user_id, type, title, message, data, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, type, title, message, json.dumps(data) if data else None, datetime.now()))
        
        notification_id = self.cursor.lastrowid
        self.conn.commit()
        
        # Отправляем сразу, если включены
        user = self.get_user(user_id)
        if user and user['settings'].get('notifications', True):
            asyncio.create_task(send_notification(user_id, title, message))
        
        return notification_id
    
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
    
    # ========== СТАТИСТИКА ==========
    
    def get_stats(self, days=7):
        self.cursor.execute('''
            SELECT * FROM stats 
            WHERE date >= date('now', ?)
            ORDER BY date DESC
        ''', (f'-{days} days',))
        
        rows = self.cursor.fetchall()
        stats = []
        for row in rows:
            stats.append({
                'date': row[1],
                'new_users': row[2],
                'new_orders': row[3],
                'completed_trades': row[4],
                'total_volume': row[5],
                'commission_earned': row[6]
            })
        return stats
    
    def get_top_traders(self, limit=10):
        self.cursor.execute('''
            SELECT user_id, first_name, username, deals_count, successful_deals, deals_volume, rating
            FROM users 
            WHERE deals_count > 0
            ORDER BY deals_volume DESC, successful_deals DESC
            LIMIT ?
        ''', (limit,))
        
        rows = self.cursor.fetchall()
        traders = []
        for row in rows:
            traders.append({
                'user_id': row[0],
                'name': row[1],
                'username': row[2],
                'deals': row[3],
                'successful': row[4],
                'volume': row[5],
                'rating': row[6]
            })
        return traders
    
    # ========== ПОДДЕРЖКА ==========
    
    def add_support_message(self, user_id, message):
        self.cursor.execute('''
            INSERT INTO support_chats (user_id, message, created_at)
            VALUES (?, ?, ?)
        ''', (user_id, message, datetime.now()))
        
        chat_id = self.cursor.lastrowid
        self.conn.commit()
        return chat_id
    
    def reply_to_support(self, chat_id, admin_reply):
        self.cursor.execute('''
            UPDATE support_chats 
            SET admin_reply = ?, replied_at = ?, is_closed = 1
            WHERE id = ?
        ''', (admin_reply, datetime.now(), chat_id))
        
        self.cursor.execute('SELECT user_id FROM support_chats WHERE id = ?', (chat_id,))
        user_id = self.cursor.fetchone()[0]
        
        self.conn.commit()
        return user_id

db = Database()

# ============================================
# 📢 УВЕДОМЛЕНИЯ
# ============================================

async def send_notification(user_id, title, message):
    """Отправляет уведомление пользователю"""
    try:
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="📨 Посмотреть", callback_data="notifications")
        keyboard.button(text="⚙️ Настройки", callback_data="settings")
        keyboard.adjust(2)
        
        await bot.send_message(
            user_id,
            f"🔔 <b>{title}</b>\n\n{message}",
            reply_markup=keyboard.as_markup()
        )
    except:
        pass

async def notify_admin(text):
    """Уведомление админу"""
    try:
        await bot.send_message(ADMIN_ID, f"👑 <b>Админ:</b>\n\n{text}")
    except:
        pass

async def notify_referrer(referrer_id, referral_id):
    """Уведомление о новом реферале"""
    try:
        text = (
            f"👥 <b>Новый реферал!</b>\n\n"
            f"По вашей ссылке зарегистрировался новый пользователь!\n"
            f"Вы получили бонус {WELCOME_BONUS * (REFERRAL_BONUS/100)} ₽"
        )
        await bot.send_message(referrer_id, text)
    except:
        pass

# ============================================
# 🎨 КЛАВИАТУРЫ (МЕГА-ДИЗАЙН)
# ============================================

def main_keyboard():
    """Главное меню"""
    builder = ReplyKeyboardBuilder()
    
    buttons = [
        KeyboardButton(text="🎮 ИГРОВАЯ БИРЖА"),
        KeyboardButton(text="💰 КРИПТО-БИРЖА"),
        KeyboardButton(text="👤 МОЙ ПРОФИЛЬ"),
        KeyboardButton(text="💰 ПОПОЛНИТЬ"),
        KeyboardButton(text="📤 ВЫВЕСТИ"),
        KeyboardButton(text="👥 РЕФЕРАЛЫ"),
        KeyboardButton(text="⭐ ТОП ТРЕЙДЕРЫ"),
        KeyboardButton(text="📞 ПОМОЩЬ")
    ]
    
    builder.add(*buttons)
    builder.adjust(2, 2, 2, 2)
    
    return builder.as_markup(resize_keyboard=True)

def games_keyboard():
    """Меню игр"""
    builder = InlineKeyboardBuilder()
    
    # Популярные игры
    popular = [g for g in GAMES if g['popular']]
    for game in popular:
        builder.button(
            text=f"{game['icon']} {game['name']}",
            callback_data=f"game_{game['id']}"
        )
    
    builder.adjust(2)
    builder.row(
        InlineKeyboardButton(text="➕ СОЗДАТЬ ОРДЕР", callback_data="create_game"),
        InlineKeyboardButton(text="🎲 ВСЕ ИГРЫ", callback_data="all_games")
    )
    builder.row(
        InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu"),
        InlineKeyboardButton(text="❓ ПОМОЩЬ", callback_data="help_games")
    )
    
    return builder.as_markup()

def crypto_keyboard():
    """Меню крипты"""
    builder = InlineKeyboardBuilder()
    
    popular = [c for c in CRYPTO if c['popular']]
    for crypto in popular:
        builder.button(
            text=f"{crypto['icon']} {crypto['name']} ({crypto['network']})",
            callback_data=f"crypto_{crypto['id']}"
        )
    
    builder.adjust(2)
    builder.row(
        InlineKeyboardButton(text="➕ СОЗДАТЬ ОРДЕР", callback_data="create_crypto"),
        InlineKeyboardButton(text="🌍 ВСЕ ВАЛЮТЫ", callback_data="all_crypto")
    )
    builder.row(
        InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu"),
        InlineKeyboardButton(text="📊 КУРСЫ", callback_data="crypto_rates")
    )
    
    return builder.as_markup()

def deposit_keyboard():
    """Пополнение баланса"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="💳 Банковская карта", callback_data="deposit_card")
    builder.button(text="₿ Криптовалюта", callback_data="deposit_crypto")
    builder.button(text="⭐ Telegram Stars", callback_data="deposit_stars")
    builder.button(text="📱 СБП", callback_data="deposit_sbp")
    builder.button(text="💰 ЮMoney", callback_data="deposit_yoomoney")
    builder.button(text="📊 Другое", callback_data="deposit_other")
    
    builder.adjust(2, 2, 2)
    builder.row(InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu"))
    
    return builder.as_markup()

def amount_keyboard():
    """Выбор суммы"""
    builder = InlineKeyboardBuilder()
    
    for amount in [100, 500, 1000, 5000, 10000, 50000]:
        builder.button(text=f"{amount} ₽", callback_data=f"amount_{amount}")
    
    builder.adjust(3, 3)
    builder.row(
        InlineKeyboardButton(text="🔙 НАЗАД", callback_data="back"),
        InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu")
    )
    
    return builder.as_markup()

def order_type_keyboard():
    """Тип ордера"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📈 ПРОДАТЬ", callback_data="type_sell")
    builder.button(text="📉 КУПИТЬ", callback_data="type_buy")
    
    builder.adjust(2)
    builder.row(
        InlineKeyboardButton(text="❌ ОТМЕНА", callback_data="cancel_order"),
        InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu")
    )
    
    return builder.as_markup()

def payment_keyboard():
    """Способы оплаты"""
    builder = InlineKeyboardBuilder()
    
    for pm in PAYMENT_METHODS[:6]:  # Первые 6 способов
        builder.button(
            text=f"{pm['icon']} {pm['name']}",
            callback_data=f"payment_{pm['id']}"
        )
    
    builder.adjust(2, 2, 2)
    builder.row(
        InlineKeyboardButton(text="🔙 НАЗАД", callback_data="back"),
        InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu")
    )
    
    return builder.as_markup()

def confirm_keyboard():
    """Подтверждение"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="✅ ПОДТВЕРДИТЬ", callback_data="confirm_order")
    builder.button(text="❌ ОТМЕНА", callback_data="cancel_order")
    
    builder.adjust(2)
    
    return builder.as_markup()

def cancel_keyboard():
    """Отмена"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="❌ ОТМЕНИТЬ", callback_data="cancel_order")
    builder.button(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu")
    
    builder.adjust(2)
    
    return builder.as_markup()

def back_keyboard(target="back"):
    """Назад + главное меню"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🔙 НАЗАД", callback_data=target)
    builder.button(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu")
    
    builder.adjust(2)
    
    return builder.as_markup()

def order_actions_keyboard(order_id, order_type, is_owner=False, is_favorite=False):
    """Действия с ордером"""
    builder = InlineKeyboardBuilder()
    
    if not is_owner:
        builder.button(text="💎 КУПИТЬ", callback_data=f"buy_{order_type}_{order_id}")
    
    if is_favorite:
        builder.button(text="★ В ИЗБРАННОМ", callback_data=f"unfav_{order_type}_{order_id}")
    else:
        builder.button(text="☆ В ИЗБРАННОЕ", callback_data=f"fav_{order_type}_{order_id}")
    
    builder.adjust(2)
    builder.row(
        InlineKeyboardButton(text="🔙 НАЗАД", callback_data="back"),
        InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu")
    )
    
    return builder.as_markup()

def trade_actions_keyboard(trade_id, user_role):
    """Действия со сделкой"""
    builder = InlineKeyboardBuilder()
    
    if user_role == 'buyer':
        builder.button(text="💳 Я ОПЛАТИЛ", callback_data=f"trade_paid_{trade_id}")
    elif user_role == 'seller':
        builder.button(text="✅ ПОДТВЕРДИТЬ", callback_data=f"trade_confirm_{trade_id}")
    
    builder.button(text="⚠️ ОТКРЫТЬ СПОР", callback_data=f"trade_dispute_{trade_id}")
    
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu"),
        InlineKeyboardButton(text="📞 ПОДДЕРЖКА", callback_data="support")
    )
    
    return builder.as_markup()

def review_keyboard(trade_id, to_id):
    """Оценка сделки"""
    builder = InlineKeyboardBuilder()
    
    for i in range(1, 6):
        builder.button(text=f"{i}⭐", callback_data=f"rate_{trade_id}_{to_id}_{i}")
    
    builder.adjust(5)
    builder.row(InlineKeyboardButton(text="🔙 ПРОПУСТИТЬ", callback_data="skip_review"))
    
    return builder.as_markup()

def profile_keyboard(user_id):
    """Профиль пользователя"""
    builder = InlineKeyboardBuilder()
    
    user = db.get_user(user_id)
    if user:
        buttons = [
            InlineKeyboardButton(text="📊 МОИ СДЕЛКИ", callback_data="my_trades"),
            InlineKeyboardButton(text="📋 МОИ ОРДЕРА", callback_data="my_orders"),
            InlineKeyboardButton(text="🔔 УВЕДОМЛЕНИЯ", callback_data="my_notifications"),
            InlineKeyboardButton(text="⭐ ИЗБРАННОЕ", callback_data="my_favorites"),
            InlineKeyboardButton(text="📝 ОТЗЫВЫ", callback_data="my_reviews"),
            InlineKeyboardButton(text="⚙️ НАСТРОЙКИ", callback_data="settings"),
            InlineKeyboardButton(text="🎁 ЕЖЕДНЕВНЫЙ БОНУС", callback_data="daily_bonus"),
            InlineKeyboardButton(text="🏆 ДОСТИЖЕНИЯ", callback_data="achievements"),
        ]
        
        for btn in buttons:
            builder.row(btn)
        
        builder.row(InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu"))
    
    return builder.as_markup()

def admin_keyboard():
    """Админ-панель"""
    builder = InlineKeyboardBuilder()
    
    buttons = [
        InlineKeyboardButton(text="📊 ОБЩАЯ СТАТИСТИКА", callback_data="admin_stats"),
        InlineKeyboardButton(text="💳 ВСЕ ПЛАТЕЖИ", callback_data="admin_payments"),
        InlineKeyboardButton(text="👥 ПОЛЬЗОВАТЕЛИ", callback_data="admin_users"),
        InlineKeyboardButton(text="📈 ГРАФИКИ", callback_data="admin_charts"),
        InlineKeyboardButton(text="💰 КОМИССИЯ", callback_data="admin_commission"),
        InlineKeyboardButton(text="⚖️ АРБИТРАЖ", callback_data="admin_disputes"),
        InlineKeyboardButton(text="📢 РАССЫЛКА", callback_data="admin_broadcast"),
        InlineKeyboardButton(text="⚙️ НАСТРОЙКИ", callback_data="admin_settings"),
    ]
    
    builder.add(*buttons)
    builder.adjust(2, 2, 2, 2)
    builder.row(InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu"))
    
    return builder.as_markup()

# ============================================
# 🤖 ИНИЦИАЛИЗАЦИЯ БОТА
# ============================================

storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=storage)

# ============================================
# 🚀 КОМАНДА СТАРТ
# ============================================

@dp.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user
    args = message.text.split()
    ref_code = args[1] if len(args) > 1 else None
    
    # Регистрация
    referral_code = db.add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        referrer_code=ref_code
    )
    
    # Приветствие
    welcome_text = (
        f"╔══════════════════════════════════════════╗\n"
        f"║     🌟 ДОБРО ПОЖАЛОВАТЬ В MEGA P2P!    ║\n"
        f"╚══════════════════════════════════════════╝\n\n"
        
        f"👋 <b>Привет, {user.first_name}!</b>\n\n"
        
        f"<b>🔥 ЭТО АБСОЛЮТНЫЙ РАЗЪЕБ:</b>\n"
        f"├ 🎮 <b>15+ игр</b> (PUBG, Brawl, Free Fire, Steam, Genshin...)\n"
        f"├ 💰 <b>6+ криптовалют</b> (USDT, TON, BTC, ETH...)\n"
        f"├ 🔒 <b>Эскроу-гарант</b> — деньги замораживаются\n"
        f"├ ⭐ <b>Рейтинги и отзывы</b> — честные сделки\n"
        f"├ 💳 <b>8 способов оплаты</b> — карты, СБП, крипта, Stars\n"
        f"├ 👥 <b>Рефералы</b> — зарабатывай с друзьями\n"
        f"└ 🏆 <b>VIP уровни</b> — комиссия до 0.5%\n\n"
        
        f"💰 <b>Твой баланс:</b> {WELCOME_BONUS} ₽\n"
        f"🔗 <b>Реферальная ссылка:</b>\n"
        f"<code>https://t.me/{(await bot.get_me()).username}?start={referral_code}</code>\n\n"
        
        f"👇 <b>ВЫБИРАЙ ДЕЙСТВИЕ:</b>"
    )
    
    await message.answer(welcome_text, reply_markup=main_keyboard())
    
    # Уведомление админу
    await notify_admin(
        f"👤 <b>Новый пользователь!</b>\n"
        f"Имя: {user.first_name}\n"
        f"ID: <code>{user.id}</code>\n"
        f"Реф: @{user.username}"
    )

# ============================================
# 🎯 ОБРАБОТЧИКИ ГЛАВНОГО МЕНЮ
# ============================================

@dp.message(F.text == "🎮 ИГРОВАЯ БИРЖА")
async def games_section(message: Message):
    text = (
        "╔══════════════════════════════════════════╗\n"
        "║          🎮 ИГРОВАЯ БИРЖА               ║\n"
        "╚══════════════════════════════════════════╝\n\n"
        
        "<b>🔥 ПОПУЛЯРНЫЕ ИГРЫ:</b>\n"
    )
    
    for game in GAMES:
        if game['popular']:
            text += f"{game['icon']} {game['name']} — {game['currency']}\n"
    
    text += (
        f"\n<b>💰 КОМИССИЯ:</b> {COMMISSION}%\n"
        f"<b>⏱ ЭСКРОУ:</b> {ESCROW_TIME} мин\n"
        f"<b>📊 ВСЕГО ИГР:</b> {len(GAMES)}\n\n"
        f"👇 <b>ВЫБЕРИ ИГРУ:</b>"
    )
    
    await message.answer(text, reply_markup=games_keyboard())

@dp.message(F.text == "💰 КРИПТО-БИРЖА")
async def crypto_section(message: Message):
    text = (
        "╔══════════════════════════════════════════╗\n"
        "║          💰 КРИПТО-БИРЖА                ║\n"
        "╚══════════════════════════════════════════╝\n\n"
        
        "<b>💎 ДОСТУПНЫЕ ВАЛЮТЫ:</b>\n"
    )
    
    for crypto in CRYPTO:
        text += f"{crypto['icon']} {crypto['name']} ({crypto['network']})\n"
    
    text += (
        f"\n<b>💰 КОМИССИЯ:</b> {COMMISSION}%\n"
        f"<b>⏱ ЭСКРОУ:</b> {ESCROW_TIME} мин\n"
        f"<b>📊 ВСЕГО ВАЛЮТ:</b> {len(CRYPTO)}\n\n"
        f"👇 <b>ВЫБЕРИ ВАЛЮТУ:</b>"
    )
    
    await message.answer(text, reply_markup=crypto_keyboard())

@dp.message(F.text == "👤 МОЙ ПРОФИЛЬ")
async def profile_section(message: Message):
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message.answer("❌ Ошибка загрузки профиля")
        return
    
    balance = db.get_balance(user_id)
    stats = db.get_user_stats(user_id)
    
    # Рейтинг звёздами
    rating = user['rating']
    stars = "⭐" * int(rating) + ("✨" if rating % 1 >= 0.5 else "")
    
    # VIP уровень
    vip_level, vip_data = db.get_vip_level(user['deals_count'])
    vip_emoji = {
        'bronze': '🥉',
        'silver': '🥈',
        'gold': '🥇',
        'platinum': '💎',
        'diamond': '💎💎'
    }.get(vip_level, '🥉')
    
    text = (
        f"╔══════════════════════════════════════════╗\n"
        f"║            👤 ТВОЙ ПРОФИЛЬ              ║\n"
        f"╚══════════════════════════════════════════╝\n\n"
        
        f"<b>🆔 ID:</b> <code>{user_id}</code>\n"
        f"<b>📱 Username:</b> @{user['username'] if user['username'] else 'нет'}\n"
        f"<b>📅 С нами:</b> {user['registered_at'][:10]}\n\n"
        
        f"<b>⭐ РЕЙТИНГ:</b> {stars} ({rating:.1f})\n"
        f"<b>🏆 УРОВЕНЬ:</b> {vip_emoji} {vip_data['name']} (комиссия {vip_data['commission']}%)\n"
        f"<b>📊 СДЕЛОК:</b> {user['successful_deals']}/{user['deals_count']} (объём {stats['total_volume']:.0f} ₽)\n"
        f"<b>👥 РЕФЕРАЛОВ:</b> {user['referral_count']} (заработано {user['referral_balance']:.0f} ₽)\n\n"
        
        f"<b>💰 БАЛАНС:</b>\n"
        f"├ Доступно: {balance['available']:.0f} ₽\n"
        f"├ Заморожено: {balance['locked']:.0f} ₽\n"
        f"└ Всего: {balance['available'] + balance['locked']:.0f} ₽\n"
    )
    
    if user['is_verified']:
        text += f"\n✅ <b>ВЕРИФИЦИРОВАННЫЙ ТРЕЙДЕР</b>\n"
    
    await message.answer(text, reply_markup=profile_keyboard(user_id))

@dp.message(F.text == "💰 ПОПОЛНИТЬ")
async def deposit_section(message: Message):
    text = (
        "╔══════════════════════════════════════════╗\n"
        "║         💰 ПОПОЛНЕНИЕ БАЛАНСА           ║\n"
        "╚══════════════════════════════════════════╝\n\n"
        
        "<b>💳 ДОСТУПНЫЕ МЕТОДЫ:</b>\n"
        "├ 💳 Банковская карта (мгновенно)\n"
        "├ ₿ Криптовалюта (USDT, TON, BTC)\n"
        "├ ⭐ Telegram Stars\n"
        "├ 📱 СБП\n"
        "├ 💰 ЮMoney\n"
        "└ 🔄 Другие способы\n\n"
        
        f"<b>⚡ МИН. СУММА:</b> {MIN_AMOUNT} ₽\n"
        f"<b>💎 МАКС. СУММА:</b> {MAX_AMOUNT} ₽\n"
        f"<b>⏱ ВРЕМЯ:</b> до 5 минут\n\n"
        
        f"👇 <b>ВЫБЕРИ СПОСОБ:</b>"
    )
    
    await message.answer(text, reply_markup=deposit_keyboard())

@dp.message(F.text == "📤 ВЫВЕСТИ")
async def withdraw_section(message: Message):
    balance = db.get_balance(message.from_user.id)
    
    text = (
        "╔══════════════════════════════════════════╗\n"
        "║            📤 ВЫВОД СРЕДСТВ             ║\n"
        "╚══════════════════════════════════════════╝\n\n"
        
        f"<b>💰 ДОСТУПНО:</b> {balance['available']:.0f} ₽\n"
        f"<b>💎 МИН. ВЫВОД:</b> {MIN_AMOUNT} ₽\n"
        f"<b>⚡ КОМИССИЯ:</b> 2%\n\n"
        
        f"<b>💳 ДОСТУПНЫЕ МЕТОДЫ:</b>\n"
        f"├ Банковская карта\n"
        f"├ СБП\n"
        f"├ ЮMoney\n"
        f"├ Криптокошелёк\n"
        f"└ Другие\n\n"
        
        f"📝 <b>Напиши сумму для вывода:</b>"
    )
    
    await message.answer(text, reply_markup=cancel_keyboard())

@dp.message(F.text == "👥 РЕФЕРАЛЫ")
async def referrals_section(message: Message):
    user = db.get_user(message.from_user.id)
    
    ref_link = f"https://t.me/{(await bot.get_me()).username}?start={user['referral_code']}"
    
    text = (
        "╔══════════════════════════════════════════╗\n"
        "║           👥 РЕФЕРАЛЬНАЯ                ║\n"
        "║              ПРОГРАММА                   ║\n"
        "╚══════════════════════════════════════════╝\n\n"
        
        f"<b>🔗 ТВОЯ ССЫЛКА:</b>\n"
        f"<code>{ref_link}</code>\n\n"
        
        f"<b>🎁 УСЛОВИЯ:</b>\n"
        f"├ {REFERRAL_BONUS}% от комиссии с каждой сделки\n"
        f"├ +{WELCOME_BONUS * (REFERRAL_BONUS/100)} ₽ за регистрацию\n"
        f"└ Выплаты на баланс автоматически\n\n"
        
        f"<b>📊 СТАТИСТИКА:</b>\n"
        f"├ Приглашено: {user['referral_count']} чел\n"
        f"└ Заработано: {user['referral_balance']:.0f} ₽\n\n"
        
        f"👇 <b>ДЕЛИСЬ ССЫЛКОЙ И ЗАРАБАТЫВАЙ!</b>"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📤 ПОДЕЛИТЬСЯ", switch_inline_query=f"🔥 Зарабатывай со мной! {ref_link}")
    builder.button(text="👥 МОИ РЕФЕРАЛЫ", callback_data="my_referrals")
    builder.row(InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu"))
    
    await message.answer(text, reply_markup=builder.as_markup())

@dp.message(F.text == "⭐ ТОП ТРЕЙДЕРЫ")
async def top_traders_section(message: Message):
    top = db.get_top_traders(10)
    
    text = (
        "╔══════════════════════════════════════════╗\n"
        "║        ⭐ ТОП-10 ТРЕЙДЕРОВ              ║\n"
        "╚══════════════════════════════════════════╝\n\n"
    )
    
    if not top:
        text += "😕 Пока нет данных. Будь первым!"
    else:
        for i, trader in enumerate(top, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            name = trader['name'][:15]
            text += f"{medal} {name} — {trader['volume']:.0f} ₽ ({trader['deals']} сделок)\n"
    
    text += "\n👇 <b>ПОКУПАЙ БОЛЬШЕ И ПОПАДИ В ТОП!</b>"
    
    await message.answer(text, reply_markup=back_keyboard())

@dp.message(F.text == "📞 ПОМОЩЬ")
async def help_section(message: Message):
    text = (
        "╔══════════════════════════════════════════╗\n"
        "║           📞 ЦЕНТР ПОМОЩИ               ║\n"
        "╚══════════════════════════════════════════╝\n\n"
        
        "<b>❓ ЧАСТЫЕ ВОПРОСЫ:</b>\n\n"
        
        "<b>1️⃣ КАК КУПИТЬ?</b>\n"
        "• Выбери игру/валюту\n"
        "• Найди подходящий ордер\n"
        "• Нажми «Купить» и введи количество\n"
        "• Деньги заморозятся на твоём счету\n"
        "• Свяжись с продавцом и оплати\n"
        "• Нажми «Я оплатил»\n"
        "• Продавец подтвердит — товар твой!\n\n"
        
        "<b>2️⃣ КАК ПРОДАТЬ?</b>\n"
        "• Создай ордер (количество, цена)\n"
        "• Жди покупателя\n"
        "• Получи уведомление о сделке\n"
        "• Дождись оплаты от покупателя\n"
        "• Нажми «Подтвердить» — деньги твои!\n\n"
        
        f"<b>3️⃣ КОМИССИЯ?</b>\n"
        f"• Базовая: {COMMISSION}%\n"
        f"• VIP уровни: до 0.5%\n"
        f"• Выводится автоматически\n\n"
        
        f"<b>4️⃣ ЭСКРОУ?</b>\n"
        f"• Деньги замораживаются на время сделки\n"
        f"• Никто не может их украсть\n"
        f"• Время на оплату: {ESCROW_TIME} минут\n"
        f"• При споре — решает администратор\n\n"
        
        f"<b>5️⃣ ПОДДЕРЖКА?</b>\n"
        f"• Напиши @{SUPPORT_USERNAME}\n"
        f"• Открой спор в сделке\n"
        f"• Ответ в течение часа\n\n"
        
        f"👇 <b>ЧЕМ МЫ МОЖЕМ ПОМОЧЬ?</b>"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📨 НАПИСАТЬ В ПОДДЕРЖКУ", callback_data="support")
    builder.button(text="📚 ИНСТРУКЦИЯ", callback_data="instruction")
    builder.row(InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu"))
    
    await message.answer(text, reply_markup=builder.as_markup())

# ============================================
# 🔄 НАВИГАЦИЯ
# ============================================

@dp.callback_query(lambda c: c.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        "🏠 <b>ГЛАВНОЕ МЕНЮ</b>\n\nВыбери действие:",
        reply_markup=main_keyboard()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "back")
async def back_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🎮 <b>ИГРОВАЯ БИРЖА</b>",
        reply_markup=games_keyboard()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "cancel_order")
async def cancel_order_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ Действие отменено",
        reply_markup=games_keyboard()
    )
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
        text = (
            f"{game['icon']} <b>{game['name']}</b>\n\n"
            f"😕 Пока нет активных ордеров для этой игры.\n\n"
            f"🔥 <b>БУДЬ ПЕРВЫМ!</b>\n"
            f"Создай ордер и начни зарабатывать!"
        )
        
        builder = InlineKeyboardBuilder()
        builder.button(text="➕ СОЗДАТЬ ОРДЕР", callback_data=f"create_game_{game_id}")
        builder.row(InlineKeyboardButton(text="🔙 НАЗАД", callback_data="back"))
        
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
        await callback.answer()
        return
    
    text = f"{game['icon']} <b>{game['name']} — АКТИВНЫЕ ОРДЕРА:</b>\n\n"
    
    for order in orders[:5]:
        emoji = "📈" if order['order_type'] == 'sell' else "📉"
        type_text = "ПРОДАЖА" if order['order_type'] == 'sell' else "ПОКУПКА"
        
        text += f"{emoji} <b>{type_text}</b>\n"
        text += f"├ {order['amount']:.0f} {game['currency']} × {order['price']}₽ = {order['total']:.0f}₽\n"
        text += f"└ 👁 {order['views']} просмотров\n\n"
    
    builder = InlineKeyboardBuilder()
    for order in orders[:4]:
        emoji = "📈" if order['order_type'] == 'sell' else "📉"
        builder.button(
            text=f"{emoji} {order['amount']:.0f} {game['currency']}",
            callback_data=f"view_game_order_{order['id']}"
        )
    
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
        f"📦 <b>Мин. сделка:</b> {order['min_amount']:.0f} {order['game_currency']}\n"
    )
    
    if order['comment']:
        text += f"\n📝 <b>Комментарий:</b>\n{order['comment']}\n"
    
    seller = db.get_user(order['user_id'])
    if seller:
        stars = "⭐" * int(seller['rating']) + ("✨" if seller['rating'] % 1 >= 0.5 else "")
        vip_emoji = '🥉' if seller['deals_count'] < 5 else '🥈' if seller['deals_count'] < 20 else '🥇' if seller['deals_count'] < 50 else '💎'
        
        text += (
            f"\n👤 <b>Продавец:</b> {seller['first_name']} {vip_emoji}\n"
            f"├ ⭐ Рейтинг: {stars} ({seller['rating']:.1f})\n"
            f"└ 📊 Сделок: {seller['successful_deals']}/{seller['deals_count']}\n"
        )
    
    text += f"\n🕐 <b>Создан:</b> {order['created_at'][:16]}\n"
    text += f"👁 <b>Просмотров:</b> {order['views']}"
    
    await callback.message.edit_text(
        text,
        reply_markup=order_actions_keyboard(order_id, 'game', is_owner, is_favorite)
    )
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
        text = (
            f"{crypto['icon']} <b>{crypto['name']}</b>\n\n"
            f"😕 Пока нет активных ордеров.\n\n"
            f"🔥 <b>СОЗДАЙ ПЕРВЫЙ!</b>"
        )
        
        builder = InlineKeyboardBuilder()
        builder.button(text="➕ СОЗДАТЬ ОРДЕР", callback_data=f"create_crypto_{crypto_id}")
        builder.row(InlineKeyboardButton(text="🔙 НАЗАД", callback_data="back"))
        
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
        await callback.answer()
        return
    
    text = f"{crypto['icon']} <b>{crypto['name']} — АКТИВНЫЕ ОРДЕРА:</b>\n\n"
    
    for order in orders[:5]:
        emoji = "📈" if order['order_type'] == 'sell' else "📉"
        type_text = "ПРОДАЖА" if order['order_type'] == 'sell' else "ПОКУПКА"
        
        text += f"{emoji} <b>{type_text}</b>\n"
        text += f"├ {order['amount']} {crypto_id.upper()} × {order['price']}₽ = {order['total_fiat']:.0f}₽\n"
        text += f"└ 👁 {order['views']} просмотров\n\n"
    
    builder = InlineKeyboardBuilder()
    for order in orders[:4]:
        emoji = "📈" if order['order_type'] == 'sell' else "📉"
        builder.button(
            text=f"{emoji} {order['amount']} {crypto_id.upper()}",
            callback_data=f"view_crypto_order_{order['id']}"
        )
    
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
        f"📦 <b>Мин. сделка:</b> {order['min_amount']:.2f} {order['currency_id'].upper()}\n"
    )
    
    if order['comment']:
        text += f"\n📝 <b>Комментарий:</b>\n{order['comment']}\n"
    
    seller = db.get_user(order['user_id'])
    if seller:
        stars = "⭐" * int(seller['rating']) + ("✨" if seller['rating'] % 1 >= 0.5 else "")
        vip_emoji = '🥉' if seller['deals_count'] < 5 else '🥈' if seller['deals_count'] < 20 else '🥇' if seller['deals_count'] < 50 else '💎'
        
        text += (
            f"\n👤 <b>Продавец:</b> {seller['first_name']} {vip_emoji}\n"
            f"├ ⭐ Рейтинг: {stars} ({seller['rating']:.1f})\n"
            f"└ 📊 Сделок: {seller['successful_deals']}/{seller['deals_count']}\n"
        )
    
    text += f"\n🕐 <b>Создан:</b> {order['created_at'][:16]}\n"
    text += f"👁 <b>Просмотров:</b> {order['views']}"
    
    await callback.message.edit_text(
        text,
        reply_markup=order_actions_keyboard(order_id, 'crypto', is_owner, is_favorite)
    )
    await callback.answer()

# ============================================
# 🚀 СОЗДАНИЕ ОРДЕРА
# ============================================

@dp.callback_query(lambda c: c.data == "create_game")
async def create_game_start(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    
    for game in GAMES:
        builder.button(
            text=f"{game['icon']} {game['name']}",
            callback_data=f"create_game_{game['id']}"
        )
    
    builder.adjust(2)
    builder.row(
        InlineKeyboardButton(text="❌ ОТМЕНА", callback_data="cancel_order"),
        InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu")
    )
    
    await callback.message.edit_text(
        "🎮 <b>СОЗДАНИЕ ОРДЕРА</b>\n\nВыбери игру:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "create_crypto")
async def create_crypto_start(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    
    for crypto in CRYPTO:
        builder.button(
            text=f"{crypto['icon']} {crypto['name']} ({crypto['network']})",
            callback_data=f"create_crypto_{crypto['id']}"
        )
    
    builder.adjust(2)
    builder.row(
        InlineKeyboardButton(text="❌ ОТМЕНА", callback_data="cancel_order"),
        InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu")
    )
    
    await callback.message.edit_text(
        "💰 <b>СОЗДАНИЕ ОРДЕРА</b>\n\nВыбери валюту:",
        reply_markup=builder.as_markup()
    )
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
        item=game,
        item_id=game_id,
        item_name=game['name'],
        item_icon=game['icon'],
        item_currency=game['currency']
    )
    await state.set_state(OrderStates.choosing_type)
    
    await callback.message.edit_text(
        f"{game['icon']} <b>{game['name']}</b>\n\n"
        f"Ты хочешь продать или купить?",
        reply_markup=order_type_keyboard()
    )
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
        item=crypto,
        item_id=crypto_id,
        item_name=crypto['name'],
        item_icon=crypto['icon'],
        item_currency=crypto_id.upper()
    )
    await state.set_state(OrderStates.choosing_type)
    
    await callback.message.edit_text(
        f"{crypto['icon']} <b>{crypto['name']}</b>\n\n"
        f"Ты хочешь продать или купить?",
        reply_markup=order_type_keyboard()
    )
    await callback.answer()

@dp.callback_query(OrderStates.choosing_type, lambda c: c.data.startswith('type_'))
async def process_order_type(callback: CallbackQuery, state: FSMContext):
    order_type = callback.data.replace('type_', '')
    await state.update_data(order_type=order_type)
    await state.set_state(OrderStates.entering_amount)
    
    await callback.message.edit_text(
        f"💰 <b>ВВЕДИ КОЛИЧЕСТВО:</b>\n\n"
        f"Отправь число (например: 100)",
        reply_markup=cancel_keyboard()
    )
    await callback.answer()

@dp.message(OrderStates.entering_amount)
async def enter_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError
    except:
        await message.answer(
            "❌ Введи положительное число",
            reply_markup=cancel_keyboard()
        )
        return
    
    await state.update_data(amount=amount)
    await state.set_state(OrderStates.entering_price)
    
    await message.answer(
        f"💵 <b>ВВЕДИ ЦЕНУ ЗА ЕДИНИЦУ (В ₽):</b>\n\n"
        f"Например: 1.5",
        reply_markup=cancel_keyboard()
    )

@dp.message(OrderStates.entering_price)
async def enter_price(message: Message, state: FSMContext):
    try:
        price = float(message.text)
        if price <= 0:
            raise ValueError
    except:
        await message.answer(
            "❌ Введи положительное число",
            reply_markup=cancel_keyboard()
        )
        return
    
    data = await state.get_data()
    total = data['amount'] * price
    
    if total < MIN_AMOUNT:
        await message.answer(
            f"❌ Минимальная сумма {MIN_AMOUNT} ₽.\n"
            f"Твоя сумма: {total:.0f} ₽.",
            reply_markup=cancel_keyboard()
        )
        return
    
    if total > MAX_AMOUNT:
        await message.answer(
            f"❌ Максимальная сумма {MAX_AMOUNT} ₽.\n"
            f"Твоя сумма: {total:.0f} ₽.",
            reply_markup=cancel_keyboard()
        )
        return
    
    await state.update_data(price=price)
    await state.set_state(OrderStates.entering_comment)
    
    await message.answer(
        f"📝 <b>КОММЕНТАРИЙ:</b>\n\n"
        f"Напиши комментарий к ордеру\n"
        f"Или отправь «-» чтобы пропустить",
        reply_markup=cancel_keyboard()
    )

@dp.message(OrderStates.entering_comment)
async def enter_comment(message: Message, state: FSMContext):
    comment = message.text if message.text != '-' else ''
    await state.update_data(comment=comment)
    await state.set_state(OrderStates.choosing_payment)
    
    await message.answer(
        f"💳 <b>ВЫБЕРИ СПОСОБ ОПЛАТЫ:</b>",
        reply_markup=payment_keyboard()
    )

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
        f"<b>✅ ПРОВЕРЬ ДАННЫЕ:</b>\n\n"
        f"📌 <b>Тип:</b> {'📈 ПРОДАЖА' if data['order_type'] == 'sell' else '📉 ПОКУПКА'}\n"
        f"🎮 <b>Товар:</b> {data['item_name']}\n"
        f"💰 <b>Количество:</b> {data['amount']} {data['item_currency']}\n"
        f"💵 <b>Цена:</b> {data['price']} ₽\n"
        f"💎 <b>Сумма:</b> {total:.0f} ₽\n"
        f"💳 <b>Оплата:</b> {payment['name']}\n"
    )
    
    if data['comment']:
        text += f"\n📝 <b>Комментарий:</b> {data['comment']}\n"
    
    text += f"\n<b>Всё верно?</b>"
    
    await callback.message.edit_text(text, reply_markup=confirm_keyboard())
    await callback.answer()

@dp.callback_query(OrderStates.confirming, lambda c: c.data == "confirm_order")
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    if data['market_type'] == 'game':
        order_id = db.create_game_order(
            user_id=callback.from_user.id,
            game_id=data['item_id'],
            order_type=data['order_type'],
            amount=data['amount'],
            price=data['price'],
            comment=data['comment'],
            payment_method=data['payment_method']
        )
    else:
        order_id = db.create_crypto_order(
            user_id=callback.from_user.id,
            currency_id=data['item_id'],
            order_type=data['order_type'],
            amount=data['amount'],
            price=data['price'],
            comment=data['comment'],
            payment_method=data['payment_method']
        )
    
    await state.clear()
    
    text = (
        f"✅ <b>ОРДЕР УСПЕШНО СОЗДАН!</b>\n\n"
        f"📋 <b>ID ордера:</b> #{order_id}\n\n"
        f"🔍 <b>ЧТО ДАЛЬШЕ?</b>\n"
        f"• Ордер появится в общем списке\n"
        f"• Покупатели смогут его найти\n"
        f"• Ты получишь уведомление о сделке\n"
        f"• Деньги будут заморожены на время сделки\n\n"
        f"💰 <b>Удачных продаж!</b>"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(
        text="📋 ПЕРЕЙТИ К ОРДЕРУ",
        callback_data=f"view_{data['market_type']}_order_{order_id}"
    )
    builder.row(InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

# ============================================
# 🛒 ПОКУПКА (С ЗАМОРОЗКОЙ)
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
        await callback.answer(
            f"❌ Недостаточно средств.\nНужно минимум {min_total:.0f} ₽",
            show_alert=True
        )
        return
    
    await state.update_data(
        order_type=order_type,
        order_id=order_id,
        item_name=order['game_name'] if order_type == 'game' else order['currency_name'],
        item_icon=order['game_icon'] if order_type == 'game' else order['currency_icon'],
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
        await message.answer(
            "❌ Введи положительное число",
            reply_markup=cancel_keyboard()
        )
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
        await message.answer(
            f"❌ Минимальное количество: {order['min_amount']:.0f}",
            reply_markup=cancel_keyboard()
        )
        return
    
    if amount > order['amount']:
        await message.answer(
            f"❌ Максимальное количество: {order['amount']:.0f}",
            reply_markup=cancel_keyboard()
        )
        return
    
    total = amount * order['price']
    balance = db.get_balance(message.from_user.id)
    
    if balance['available'] < total:
        await message.answer(
            f"❌ Недостаточно средств. Нужно {total:.0f} ₽",
            reply_markup=cancel_keyboard()
        )
        return
    
    # Создаём сделку с заморозкой
    trade_id = db.create_trade(data['order_type'], data['order_id'], message.from_user.id, amount)
    
    if not trade_id:
        await message.answer("❌ Ошибка создания сделки")
        await state.clear()
        return
    
    await state.clear()
    
    # Уведомление покупателю
    buyer_keyboard = InlineKeyboardBuilder()
    buyer_keyboard.button(text="💳 Я ОПЛАТИЛ", callback_data=f"trade_paid_{trade_id}")
    buyer_keyboard.button(text="⚠️ ОТКРЫТЬ СПОР", callback_data=f"trade_dispute_{trade_id}")
    buyer_keyboard.row(InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu"))
    
    await message.answer(
        f"✅ <b>СДЕЛКА СОЗДАНА С ЗАМОРОЗКОЙ ДЕНЕГ!</b>\n\n"
        f"📋 <b>ID сделки:</b> #{trade_id}\n"
        f"💰 <b>Сумма:</b> {total:.0f} ₽\n\n"
        f"🔒 <b>Деньги заморожены</b> на твоём счету\n"
        f"⏱ <b>Время на оплату:</b> {ESCROW_TIME} минут\n\n"
        f"📞 <b>Свяжись с продавцом</b> и переведи деньги.\n\n"
        f"✅ <b>После оплаты нажми кнопку ниже:</b>",
        reply_markup=buyer_keyboard.as_markup()
    )
    
    # Уведомление продавцу
    seller_keyboard = InlineKeyboardBuilder()
    seller_keyboard.button(text="✅ ПОДТВЕРДИТЬ", callback_data=f"trade_confirm_{trade_id}")
    seller_keyboard.button(text="⚠️ ОТКРЫТЬ СПОР", callback_data=f"trade_dispute_{trade_id}")
    seller_keyboard.row(InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu"))
    
    await bot.send_message(
        order['user_id'],
        f"🔄 <b>НОВАЯ СДЕЛКА С ЗАМОРОЗКОЙ!</b>\n\n"
        f"Покупатель хочет купить {amount} {data['item_name']}\n"
        f"на сумму {total:.0f} ₽\n\n"
        f"🔒 Деньги покупателя уже заморожены\n"
        f"⏱ Ожидай оплаты в течение {ESCROW_TIME} минут",
        reply_markup=seller_keyboard.as_markup()
    )

# ============================================
# 🤝 ОБРАБОТЧИКИ СДЕЛОК
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
    
    db.complete_trade(trade_id)
    
    await bot.send_message(
        trade['buyer_id'],
        f"✅ <b>СДЕЛКА ЗАВЕРШЕНА!</b>\n\n"
        f"Продавец подтвердил получение денег.\n"
        f"🔒 Деньги разморожены.\n\n"
        f"Оцени продавца:",
        reply_markup=review_keyboard(trade_id, trade['seller_id'])
    )
    
    await callback.message.edit_text(
        f"✅ <b>СДЕЛКА ЗАВЕРШЕНА!</b>\n\n"
        f"Ты подтвердил получение денег.\n"
        f"🔒 Деньги разморожены и переведены на твой счёт.\n\n"
        f"💰 Комиссия: {trade['commission']} ₽\n"
        f"📊 Объём: {trade['total']} ₽",
        reply_markup=back_keyboard()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith('trade_dispute_'))
async def trade_dispute(callback: CallbackQuery):
    trade_id = int(callback.data.replace('trade_dispute_', ''))
    
    await bot.send_message(
        ADMIN_ID,
        f"⚠️ <b>⚠️ ОТКРЫТ СПОР ПО СДЕЛКЕ! ⚠️</b>\n\n"
        f"📋 <b>Сделка #{trade_id}</b>\n"
        f"👤 Пользователь: {callback.from_user.id}\n"
        f"📱 Username: @{callback.from_user.username}\n\n"
        f"⚡ Требуется вмешательство!"
    )
    
    await callback.message.edit_text(
        f"⚠️ <b>СПОР ОТКРЫТ!</b>\n\n"
        f"Администратор уже уведомлен.\n"
        f"Деньги остаются замороженными.\n"
        f"Ожидай решения в ближайшее время.\n\n"
        f"⏱ Обычно это занимает до 24 часов.",
        reply_markup=back_keyboard()
    )
    await callback.answer()

# ============================================
# ⭐ ОТЗЫВЫ
# ============================================

@dp.callback_query(lambda c: c.data.startswith('rate_'))
async def add_review(callback: CallbackQuery, state: FSMContext):
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
    
    await state.update_data(
        trade_id=trade_id,
        to_id=to_id,
        rating=rating
    )
    await state.set_state(TradeStates.waiting_review)
    await callback.answer()

@dp.message(TradeStates.waiting_review)
async def process_review(message: Message, state: FSMContext):
    data = await state.get_data()
    comment = message.text if message.text != '-' else ''
    
    db.add_review(data['trade_id'], message.from_user.id, data['to_id'], data['rating'], comment)
    
    await state.clear()
    await message.answer(
        f"✅ <b>СПАСИБО ЗА ОТЗЫВ!</b>\n\n"
        f"Твой отзыв поможет другим пользователям.",
        reply_markup=main_keyboard()
    )

@dp.callback_query(lambda c: c.data == "skip_review")
async def skip_review(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "✅ <b>СДЕЛКА ЗАВЕРШЕНА!</b>\n\n"
        f"Спасибо за использование платформы!",
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
    
    for review in reviews[:5]:
        text += (
            f"{'⭐' * review['rating']} от {review['from_name']}\n"
            f"«{review['comment']}»\n"
            f"🕐 {review['created_at'][:16]}\n\n"
        )
    
    await callback.message.edit_text(text, reply_markup=back_keyboard())
    await callback.answer()

# ============================================
# ⭐ ИЗБРАННОЕ
# ============================================

@dp.callback_query(lambda c: c.data.startswith('fav_'))
async def add_favorite(callback: CallbackQuery):
    parts = callback.data.split('_')
    order_type = parts[1]
    order_id = int(parts[2])
    
    db.add_favorite(callback.from_user.id, order_type, order_id)
    await callback.answer("⭐ Добавлено в избранное!", show_alert=True)
    
    # Обновляем просмотр
    if order_type == 'game':
        await view_game_order(callback)
    else:
        await view_crypto_order(callback)

@dp.callback_query(lambda c: c.data.startswith('unfav_'))
async def remove_favorite(callback: CallbackQuery):
    parts = callback.data.split('_')
    order_type = parts[1]
    order_id = int(parts[2])
    
    db.remove_favorite(callback.from_user.id, order_type, order_id)
    await callback.answer("☆ Убрано из избранного", show_alert=True)
    
    # Обновляем просмотр
    if order_type == 'game':
        await view_game_order(callback)
    else:
        await view_crypto_order(callback)

@dp.callback_query(lambda c: c.data == "my_favorites")
async def my_favorites(callback: CallbackQuery):
    favorites = db.get_favorites(callback.from_user.id)
    
    if not favorites:
        await callback.message.edit_text(
            "⭐ <b>ИЗБРАННОЕ</b>\n\n"
            "У тебя пока нет избранных ордеров.\n"
            "Добавляй их звездочкой в объявлениях!",
            reply_markup=back_keyboard()
        )
        await callback.answer()
        return
    
    text = "⭐ <b>ТВОИ ИЗБРАННЫЕ ОРДЕРА:</b>\n\n"
    builder = InlineKeyboardBuilder()
    
    for fav in favorites[:5]:
        order = fav['order']
        text += f"{order['game_icon'] if fav['type'] == 'game' else order['currency_icon']} "
        text += f"{order['game_name'] if fav['type'] == 'game' else order['currency_name']} — "
        text += f"{order['amount']} | {order['total'] if fav['type'] == 'game' else order['total_fiat']:.0f}₽\n\n"
        
        builder.button(
            text=f"📋 Ордер #{order['id']}",
            callback_data=f"view_{fav['type']}_order_{order['id']}"
        )
    
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="🔙 НАЗАД", callback_data="back"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

# ============================================
# 📊 ПРОФИЛЬНЫЕ РАЗДЕЛЫ
# ============================================

@dp.callback_query(lambda c: c.data == "my_trades")
async def my_trades(callback: CallbackQuery):
    trades = db.get_user_trades(callback.from_user.id)
    
    if not trades:
        await callback.message.edit_text(
            "📊 <b>МОИ СДЕЛКИ</b>\n\n"
            "У тебя пока нет сделок.\n"
            "Найди интересный ордер и купи!",
            reply_markup=back_keyboard()
        )
        await callback.answer()
        return
    
    text = "📊 <b>МОИ СДЕЛКИ:</b>\n\n"
    
    for trade in trades[:10]:
        status_emoji = "✅" if trade['status'] == 'completed' else "⏳"
        role_emoji = "📤" if trade['role'] == 'seller' else "📥"
        text += f"{status_emoji} {role_emoji} #{trade['id']} — {trade['total']:.0f} ₽\n"
        text += f"   🎮 {trade['item_name']} — {trade['amount']}\n"
        text += f"   🕐 {trade['created_at'][:16]}\n\n"
    
    await callback.message.edit_text(text, reply_markup=back_keyboard())
    await callback.answer()

@dp.callback_query(lambda c: c.data == "my_orders")
async def my_orders(callback: CallbackQuery):
    # Заглушка - можно реализовать позже
    await callback.message.edit_text(
        "📋 <b>МОИ ОРДЕРА</b>\n\n"
        "Функция в разработке.",
        reply_markup=back_keyboard()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "my_referrals")
async def my_referrals(callback: CallbackQuery):
    # Заглушка - можно реализовать позже
    await callback.message.edit_text(
        "👥 <b>МОИ РЕФЕРАЛЫ</b>\n\n"
        "Функция в разработке.",
        reply_markup=back_keyboard()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "daily_bonus")
async def daily_bonus(callback: CallbackQuery):
    success, streak, amount = db.get_daily_bonus(callback.from_user.id)
    
    if success:
        await callback.message.edit_text(
            f"🎁 <b>ЕЖЕДНЕВНЫЙ БОНУС ПОЛУЧЕН!</b>\n\n"
            f"🔥 Сумма: {amount} ₽\n"
            f"⚡ Стрик: {streak} дней\n\n"
            f"Заходи завтра за новым бонусом!",
            reply_markup=back_keyboard()
        )
    else:
        await callback.message.edit_text(
            f"🎁 <b>ЕЖЕДНЕВНЫЙ БОНУС</b>\n\n"
            f"Ты уже получал бонус сегодня.\n"
            f"Возвращайся завтра!",
            reply_markup=back_keyboard()
        )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "my_notifications")
async def my_notifications(callback: CallbackQuery):
    notifs = db.get_unread_notifications(callback.from_user.id)
    
    if not notifs:
        await callback.message.edit_text(
            "🔔 <b>УВЕДОМЛЕНИЯ</b>\n\n"
            "У тебя нет новых уведомлений.",
            reply_markup=back_keyboard()
        )
        await callback.answer()
        return
    
    text = "🔔 <b>ТВОИ УВЕДОМЛЕНИЯ:</b>\n\n"
    
    for notif in notifs[:5]:
        text += f"• <b>{notif['title']}</b>\n"
        text += f"  {notif['message']}\n"
        text += f"  🕐 {notif['created_at'][:16]}\n\n"
        db.mark_notification_read(notif['id'])
    
    await callback.message.edit_text(text, reply_markup=back_keyboard())
    await callback.answer()

@dp.callback_query(lambda c: c.data == "achievements")
async def achievements(callback: CallbackQuery):
    user = db.get_user(callback.from_user.id)
    
    text = (
        "🏆 <b>ТВОИ ДОСТИЖЕНИЯ:</b>\n\n"
        f"{'✅' if user['deals_count'] >= 1 else '⬜'} НОВИЧОК — первая сделка\n"
        f"{'✅' if user['deals_count'] >= 5 else '⬜'} ТРЕЙДЕР — 5 сделок\n"
        f"{'✅' if user['deals_count'] >= 20 else '⬜'} ПРОФИ — 20 сделок\n"
        f"{'✅' if user['deals_count'] >= 50 else '⬜'} ЭКСПЕРТ — 50 сделок\n"
        f"{'✅' if user['deals_count'] >= 100 else '⬜'} ЛЕГЕНДА — 100 сделок\n"
        f"{'✅' if user['deals_volume'] >= 10000 else '⬜'} БИЗНЕСМЕН — объём 10k₽\n"
        f"{'✅' if user['deals_volume'] >= 100000 else '⬜'} МАГНАТ — объём 100k₽\n"
        f"{'✅' if user['referral_count'] >= 5 else '⬜'} ЛИДЕР — 5 рефералов\n"
    )
    
    await callback.message.edit_text(text, reply_markup=back_keyboard())
    await callback.answer()

# ============================================
# 👑 АДМИН-ПАНЕЛЬ
# ============================================

@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ ДОСТУП ЗАПРЕЩЁН")
        return
    
    text = (
        "👑 <b>АДМИН-ПАНЕЛЬ</b>\n\n"
        "Выбери раздел для управления:"
    )
    
    await message.answer(text, reply_markup=admin_keyboard())

@dp.callback_query(lambda c: c.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    
    stats = db.get_stats(7)
    users = db.cursor.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    trades = db.cursor.execute('SELECT COUNT(*) FROM trades WHERE status = "completed"').fetchone()[0]
    volume = db.cursor.execute('SELECT SUM(total) FROM trades WHERE status = "completed"').fetchone()[0] or 0
    commission = db.cursor.execute('SELECT SUM(commission) FROM trades WHERE status = "completed"').fetchone()[0] or 0
    
    text = (
        f"👑 <b>ОБЩАЯ СТАТИСТИКА</b>\n\n"
        f"👥 <b>Пользователей:</b> {users}\n"
        f"📊 <b>Всего сделок:</b> {trades}\n"
        f"💰 <b>Общий объём:</b> {volume:.0f} ₽\n"
        f"💎 <b>Комиссия:</b> {commission:.0f} ₽\n\n"
        
        f"📈 <b>СТАТИСТИКА ЗА 7 ДНЕЙ:</b>\n"
    )
    
    for day in stats:
        text += f"• {day['date'][5:]}: +{day['new_users']} юз, {day['completed_trades']} сд, {day['commission_earned']:.0f}₽\n"
    
    await callback.message.edit_text(text, reply_markup=admin_keyboard())
    await callback.answer()

@dp.callback_query(lambda c: c.data == "admin_payments")
async def admin_payments(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    
    await callback.message.edit_text(
        "💳 <b>ПЛАТЕЖИ</b>\n\n"
        "Функция в разработке.",
        reply_markup=admin_keyboard()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "admin_users")
async def admin_users(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    
    await callback.message.edit_text(
        "👥 <b>ПОЛЬЗОВАТЕЛИ</b>\n\n"
        "Функция в разработке.",
        reply_markup=admin_keyboard()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "admin_charts")
async def admin_charts(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    
    stats = db.get_stats(14)
    
    text = "📈 <b>ГРАФИК ЗА 14 ДНЕЙ:</b>\n\n"
    
    for day in stats:
        bars = "█" * min(int(day['commission_earned'] / 50), 20) or "▏"
        text += f"{day['date'][5:]}: {bars} {day['commission_earned']:.0f}₽\n"
    
    await callback.message.edit_text(text, reply_markup=admin_keyboard())
    await callback.answer()

@dp.callback_query(lambda c: c.data == "admin_commission")
async def admin_commission(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    
    text = (
        f"💰 <b>ИНФОРМАЦИЯ О КОМИССИИ</b>\n\n"
        f"⚡ <b>Базовая комиссия:</b> {COMMISSION}%\n\n"
        f"<b>VIP УРОВНИ:</b>\n"
    )
    
    for level, data in VIP_LEVELS.items():
        text += f"• {data['name']}: {data['deals']}+ сделок, комиссия {data['commission']}%\n"
    
    await callback.message.edit_text(text, reply_markup=admin_keyboard())
    await callback.answer()

@dp.callback_query(lambda c: c.data == "admin_disputes")
async def admin_disputes(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    
    await callback.message.edit_text(
        "⚖️ <b>АРБИТРАЖ</b>\n\n"
        "Функция в разработке.",
        reply_markup=admin_keyboard()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "admin_broadcast")
async def admin_broadcast(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    
    await callback.message.edit_text(
        "📢 <b>РАССЫЛКА</b>\n\n"
        "Функция в разработке.",
        reply_markup=admin_keyboard()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "admin_settings")
async def admin_settings(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    
    await callback.message.edit_text(
        "⚙️ <b>НАСТРОЙКИ</b>\n\n"
        "Функция в разработке.",
        reply_markup=admin_keyboard()
    )
    await callback.answer()

# ============================================
# 📞 ПОДДЕРЖКА
# ============================================

@dp.callback_query(lambda c: c.data == "support")
async def support_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📞 <b>ПОДДЕРЖКА</b>\n\n"
        "Опиши свою проблему или вопрос.\n"
        "Администратор ответит в ближайшее время.",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(SupportStates.waiting_message)
    await callback.answer()

@dp.message(SupportStates.waiting_message)
async def support_message(message: Message, state: FSMContext):
    chat_id = db.add_support_message(message.from_user.id, message.text)
    
    await state.clear()
    await message.answer(
        "✅ <b>СООБЩЕНИЕ ОТПРАВЛЕНО!</b>\n\n"
        "Администратор ответит в ближайшее время.",
        reply_markup=main_keyboard()
    )
    
    # Уведомление админу
    await bot.send_message(
        ADMIN_ID,
        f"📞 <b>НОВОЕ СООБЩЕНИЕ В ПОДДЕРЖКУ</b>\n\n"
        f"👤 Пользователь: {message.from_user.first_name}\n"
        f"🆔 ID: <code>{message.from_user.id}</code>\n"
        f"📱 Username: @{message.from_user.username}\n\n"
        f"📝 Сообщение: {message.text}\n\n"
        f"Ответить: /reply_{chat_id} текст"
    )

@dp.message(Command("reply"))
async def admin_reply(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    parts = message.text.split(' ', 2)
    if len(parts) < 3:
        await message.answer("Формат: /reply_123 текст ответа")
        return
    
    chat_id = int(parts[0].replace('/reply_', ''))
    reply_text = parts[2]
    
    user_id = db.reply_to_support(chat_id, reply_text)
    
    await bot.send_message(
        user_id,
        f"📬 <b>ОТВЕТ ОТ ПОДДЕРЖКИ:</b>\n\n{reply_text}\n\n"
        f"Если остались вопросы, можешь написать снова!",
        reply_markup=back_keyboard()
    )
    
    await message.answer("✅ Ответ отправлен пользователю!")

@dp.callback_query(lambda c: c.data == "instruction")
async def instruction(callback: CallbackQuery):
    text = (
        "📚 <b>ИНСТРУКЦИЯ ПОЛЬЗОВАТЕЛЯ</b>\n\n"
        
        "<b>🔹 КАК КУПИТЬ:</b>\n"
        "1. Выбери «🎮 ИГРОВАЯ БИРЖА» или «💰 КРИПТО-БИРЖА»\n"
        "2. Нажми на нужную игру/валюту\n"
        "3. Выбери ордер и нажми «💎 КУПИТЬ»\n"
        "4. Введи количество\n"
        "5. Деньги заморозятся на твоём счету\n"
        "6. Свяжись с продавцом и переведи деньги\n"
        "7. Нажми «💳 Я ОПЛАТИЛ»\n"
        "8. Продавец подтвердит — товар твой!\n\n"
        
        "<b>🔹 КАК ПРОДАТЬ:</b>\n"
        "1. Нажми «➕ СОЗДАТЬ ОРДЕР»\n"
        "2. Выбери игру/валюту, тип «ПРОДАЖА»\n"
        "3. Укажи количество, цену, комментарий\n"
        "4. Жди покупателя\n"
        "5. Получи уведомление о сделке\n"
        "6. Дождись оплаты\n"
        "7. Нажми «✅ ПОДТВЕРДИТЬ» — деньги твои!\n\n"
        
        f"<b>🔹 КОМИССИЯ:</b> {COMMISSION}%\n"
        f"<b>🔹 ВРЕМЯ НА ОПЛАТУ:</b> {ESCROW_TIME} минут\n"
        f"<b>🔹 ПОДДЕРЖКА:</b> @{SUPPORT_USERNAME}\n\n"
        
        f"👇 <b>УДАЧНЫХ СДЕЛОК!</b>"
    )
    
    await callback.message.edit_text(text, reply_markup=back_keyboard())
    await callback.answer()

# ============================================
# 🚀 ЗАПУСК БОТА
# ============================================

async def on_startup():
    print("\n" + "="*80)
    print("🔥 P2P MEGA БОТ - АБСОЛЮТНЫЙ РАЗЪЕБ 🔥")
    print("="*80)
    print(f"🤖 Бот: @{(await bot.get_me()).username}")
    print(f"👑 Админ ID: {ADMIN_ID}")
    print(f"🎮 Игр в базе: {len(GAMES)}")
    print(f"💰 Криптовалют: {len(CRYPTO)}")
    print(f"🔒 Система эскроу: АКТИВНА")
    print(f"⚡ Комиссия: {COMMISSION}%")
    print(f"💳 Способов оплаты: {len(PAYMENT_METHODS)}")
    print("="*80)
    print(f"📅 Запуск: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print("="*80 + "\n")
    
    await bot.send_message(
        ADMIN_ID,
        f"🚀 <b>MEGA P2P БОТ ЗАПУЩЕН!</b>\n\n"
        f"<b>⚡ СТАТИСТИКА:</b>\n"
        f"├ 🎮 Игр: {len(GAMES)}\n"
        f"├ 💰 Криптовалют: {len(CRYPTO)}\n"
        f"├ 🔒 Эскроу: {ESCROW_TIME} мин\n"
        f"├ 💳 Комиссия: {COMMISSION}%\n"
        f"└ 👑 Версия: {BOT_VERSION}\n\n"
        f"✅ <b>ВСЕ СИСТЕМЫ ГОТОВЫ К РАЗЪЕБУ!</b>"
    )

async def main():
    await on_startup()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
