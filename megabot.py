#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════╗
║              P2P ГЕЙМИНГ МАРКЕТПЛЕЙС 4.0                       ║
║                    (ПОЛНОСТЬЮ РАБОЧАЯ ВЕРСИЯ)                  ║
║                    🎮 + 💰 = 🔥                                ║
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
    ReplyKeyboardMarkup, KeyboardButton
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
SUPPORT_USERNAME = "@GhostiPeeK_2"

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
# FSM СОСТОЯНИЯ
# ============================================

class OrderStates(StatesGroup):
    choosing_game = State()
    choosing_type = State()
    entering_amount = State()
    entering_price = State()
    entering_comment = State()
    confirming = State()

class TradeStates(StatesGroup):
    entering_amount = State()
    waiting_confirmation = State()
    waiting_review = State()

# ============================================
# БАЗА ДАННЫХ
# ============================================

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('p2p_bot.db', check_same_thread=False)
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
                referral_code TEXT UNIQUE,
                rating REAL DEFAULT 5.0,
                deals_count INTEGER DEFAULT 0,
                successful_deals INTEGER DEFAULT 0,
                balance REAL DEFAULT 10000
            )
        ''')
        
        # Ордера
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                game_id TEXT,
                game_name TEXT,
                game_icon TEXT,
                order_type TEXT,
                amount REAL,
                price REAL,
                total REAL,
                min_amount REAL,
                comment TEXT,
                status TEXT DEFAULT 'active',
                created_at TEXT,
                views INTEGER DEFAULT 0
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
                rating INTEGER,
                comment TEXT,
                created_at TEXT
            )
        ''')
        
        self.conn.commit()
    
    # ========== ПОЛЬЗОВАТЕЛИ ==========
    
    def add_user(self, user_id, username, first_name):
        self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        if self.cursor.fetchone():
            return
        
        ref_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        self.cursor.execute('''
            INSERT INTO users (user_id, username, first_name, registered_at, referral_code)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, datetime.now().isoformat(), ref_code))
        
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
                'referral_code': row[4],
                'rating': row[5],
                'deals_count': row[6],
                'successful_deals': row[7],
                'balance': row[8]
            }
        return None
    
    def update_balance(self, user_id, amount):
        self.cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
        self.conn.commit()
    
    def get_balance(self, user_id):
        self.cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
        row = self.cursor.fetchone()
        return row[0] if row else 0
    
    # ========== ОРДЕРА ==========
    
    def create_order(self, user_id, game_id, game_name, game_icon, order_type, amount, price, comment):
        total = amount * price
        min_amount = MIN_AMOUNT / price
        
        self.cursor.execute('''
            INSERT INTO orders 
            (user_id, game_id, game_name, game_icon, order_type, amount, price, total, min_amount, comment, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, game_id, game_name, game_icon, order_type, amount, price, total, min_amount, comment, datetime.now().isoformat()))
        
        order_id = self.cursor.lastrowid
        self.conn.commit()
        return order_id
    
    def get_orders(self, game_id=None, status='active'):
        query = 'SELECT * FROM orders WHERE status = ?'
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
                'order_type': row[5],
                'amount': row[6],
                'price': row[7],
                'total': row[8],
                'min_amount': row[9],
                'comment': row[10],
                'status': row[11],
                'created_at': row[12],
                'views': row[13]
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
                'game_id': row[2],
                'game_name': row[3],
                'game_icon': row[4],
                'order_type': row[5],
                'amount': row[6],
                'price': row[7],
                'total': row[8],
                'min_amount': row[9],
                'comment': row[10],
                'status': row[11],
                'created_at': row[12],
                'views': row[13]
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
            (order_id, seller_id, buyer_id, amount, price, total, commission, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (order_id, order['user_id'], buyer_id, amount, order['price'], total, commission, datetime.now().isoformat()))
        
        trade_id = self.cursor.lastrowid
        
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
                'status': row[8],
                'created_at': row[9],
                'completed_at': row[10]
            }
        return None
    
    def get_user_trades(self, user_id):
        self.cursor.execute('''
            SELECT * FROM trades 
            WHERE seller_id = ? OR buyer_id = ?
            ORDER BY created_at DESC
        ''', (user_id, user_id))
        
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
                'created_at': row[9]
            })
        return trades
    
    def complete_trade(self, trade_id):
        trade = self.get_trade(trade_id)
        if not trade:
            return False
        
        self.cursor.execute('UPDATE trades SET status = "completed", completed_at = ? WHERE id = ?', 
                           (datetime.now().isoformat(), trade_id))
        
        self.cursor.execute('''
            UPDATE users 
            SET deals_count = deals_count + 1,
                successful_deals = successful_deals + 1
            WHERE user_id IN (?, ?)
        ''', (trade['seller_id'], trade['buyer_id']))
        
        self.conn.commit()
        return True
    
    # ========== ОТЗЫВЫ ==========
    
    def add_review(self, trade_id, from_id, to_id, rating, comment):
        self.cursor.execute('''
            INSERT INTO reviews (trade_id, from_user_id, to_user_id, rating, comment, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (trade_id, from_id, to_id, rating, comment, datetime.now().isoformat()))
        
        self.cursor.execute('SELECT AVG(rating) as avg_rating FROM reviews WHERE to_user_id = ?', (to_id,))
        avg = self.cursor.fetchone()[0]
        
        self.cursor.execute('UPDATE users SET rating = ? WHERE user_id = ?', (avg, to_id))
        self.conn.commit()

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
    builder.button(text="💵 USDT (скоро)", callback_data="crypto_usdt")
    builder.button(text="💎 TON (скоро)", callback_data="crypto_ton")
    builder.button(text="₿ BTC (скоро)", callback_data="crypto_btc")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu"))
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

def order_actions_keyboard(order_id, is_owner=False):
    builder = InlineKeyboardBuilder()
    if not is_owner:
        builder.button(text="💎 КУПИТЬ", callback_data=f"buy_{order_id}")
    builder.row(InlineKeyboardButton(text="🔙 НАЗАД", callback_data="back"))
    return builder.as_markup()

def trade_actions_keyboard(trade_id, user_role):
    builder = InlineKeyboardBuilder()
    if user_role == 'buyer':
        builder.button(text="✅ ПОДТВЕРДИТЬ ОПЛАТУ", callback_data=f"trade_confirm_{trade_id}")
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
    builder.button(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu")
    builder.adjust(2, 1)
    return builder.as_markup()

# ============================================
# СТАРТ
# ============================================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    user = message.from_user
    
    referral_code = db.add_user(user.id, user.username, user.first_name)
    
    welcome_text = (
        f"🌟 <b>ДОБРО ПОЖАЛОВАТЬ В P2P МАРКЕТПЛЕЙС!</b> 🌟\n\n"
        f"👋 <b>Привет, {user.first_name}!</b>\n\n"
        f"🎮 <b>Здесь ты можешь:</b>\n"
        f"├ 🔥 Покупать и продавать игровую валюту\n"
        f"├ 🤝 Безопасные сделки\n"
        f"├ ⭐ Оставлять отзывы\n"
        f"└ 💰 Внутренний баланс: 10000 ₽ (тестовые)\n\n"
        f"👇 <b>Выбери раздел:</b>"
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
    await message.answer(
        "💰 <b>КРИПТО-БИРЖА</b>\n\n"
        "🚀 Раздел в разработке!\n"
        "Скоро здесь можно будет торговать USDT, TON и BTC.",
        reply_markup=crypto_keyboard()
    )

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
        f"├ Рейтинг: {stars} ({rating:.1f})\n\n"
        f"💰 <b>Баланс:</b> {balance} ₽\n"
    )
    
    await message.answer(text, reply_markup=profile_keyboard())

@dp.message(lambda m: m.text == "❓ ПОМОЩЬ")
async def help_section(message: Message):
    text = (
        "❓ <b>ЦЕНТР ПОМОЩИ</b>\n\n"
        "📌 <b>Как проходит сделка:</b>\n"
        "1️⃣ Находишь ордер\n"
        "2️⃣ Нажимаешь «Купить» и вводишь количество\n"
        "3️⃣ Деньги списываются с твоего баланса\n"
        "4️⃣ Продавец получает уведомление\n"
        "5️⃣ После подтверждения сделка завершается\n\n"
        f"💰 <b>Комиссия:</b> {COMMISSION}%\n"
        f"📞 <b>Поддержка:</b> @{SUPPORT_USERNAME}"
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
# ПОКАЗ ОРДЕРОВ
# ============================================

@dp.callback_query(lambda c: c.data.startswith('game_'))
async def show_game_orders(callback: CallbackQuery):
    game_id = callback.data.replace('game_', '')
    game = next((g for g in GAMES if g['id'] == game_id), None)
    if not game:
        await callback.answer("❌ Игра не найдена")
        return
    
    orders = db.get_orders(game_id=game_id)
    
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

@dp.callback_query(lambda c: c.data.startswith('view_order_'))
async def view_order(callback: CallbackQuery):
    order_id = int(callback.data.replace('view_order_', ''))
    order = db.get_order(order_id)
    if not order:
        await callback.answer("❌ Ордер не найден", show_alert=True)
        return
    
    is_owner = (order['user_id'] == callback.from_user.id)
    
    emoji = "📈" if order['order_type'] == 'sell' else "📉"
    type_text = "ПРОДАЖА" if order['order_type'] == 'sell' else "ПОКУПКА"
    
    text = (
        f"{order['game_icon']} <b>{order['game_name']}</b>\n"
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
    
    await callback.message.edit_text(text, reply_markup=order_actions_keyboard(order_id, is_owner))
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

@dp.callback_query(lambda c: c.data.startswith('create_game_'))
async def create_game_order(callback: CallbackQuery, state: FSMContext):
    game_id = callback.data.replace('create_game_', '')
    game = next((g for g in GAMES if g['id'] == game_id), None)
    if not game:
        await callback.answer("❌ Игра не найдена")
        return
    
    await state.update_data(game=game)
    await state.set_state(OrderStates.choosing_type)
    await callback.message.edit_text(f"{game['icon']} <b>{game['name']}</b>\n\nТы хочешь продать или купить?", reply_markup=order_type_keyboard())
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
        f"{data['game']['icon']} <b>ПРОВЕРЬ ДАННЫЕ:</b>\n\n"
        f"📌 <b>Тип:</b> {'📈 ПРОДАЖА' if data['order_type'] == 'sell' else '📉 ПОКУПКА'}\n"
        f"🎮 <b>Игра:</b> {data['game']['name']}\n"
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
        game_id=data['game']['id'],
        game_name=data['game']['name'],
        game_icon=data['game']['icon'],
        order_type=data['order_type'],
        amount=data['amount'],
        price=data['price'],
        comment=data['comment']
    )
    
    await state.clear()
    
    text = f"✅ <b>ОРДЕР УСПЕШНО СОЗДАН!</b>\n\n📋 <b>ID ордера:</b> #{order_id}"
    
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
    
    balance = db.get_balance(callback.from_user.id)
    min_total = order['min_amount'] * order['price']
    
    if balance < min_total:
        await callback.answer(f"❌ Недостаточно средств. Нужно минимум {min_total:.0f} ₽", show_alert=True)
        return
    
    await state.update_data(order_id=order_id)
    await state.set_state(TradeStates.entering_amount)
    
    await callback.message.edit_text(
        f"💰 <b>ВВЕДИ КОЛИЧЕСТВО:</b>\n\n"
        f"Доступно: {order['amount']}\n"
        f"Цена: {order['price']} ₽\n"
        f"Мин. сделка: {order['min_amount']:.0f}\n\n"
        f"Твой баланс: {balance} ₽",
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
    balance = db.get_balance(message.from_user.id)
    
    if balance < total:
        await message.answer(f"❌ Недостаточно средств. Нужно {total:.0f} ₽", reply_markup=cancel_keyboard())
        return
    
    # Списываем деньги
    db.update_balance(message.from_user.id, -total)
    
    # Создаём сделку
    trade_id = db.create_trade(data['order_id'], message.from_user.id, amount)
    
    if not trade_id:
        await message.answer("❌ Ошибка создания сделки")
        db.update_balance(message.from_user.id, total)
        await state.clear()
        return
    
    await state.clear()
    
    await message.answer(
        f"✅ <b>СДЕЛКА СОЗДАНА!</b>\n\n"
        f"📋 <b>ID сделки:</b> #{trade_id}\n"
        f"💰 <b>Сумма:</b> {total:.0f} ₽\n\n"
        f"Деньги списаны с твоего счёта.\n"
        f"Ожидай подтверждения от продавца."
    )
    
    seller_keyboard = InlineKeyboardBuilder()
    seller_keyboard.button(text="✅ ПОДТВЕРДИТЬ СДЕЛКУ", callback_data=f"trade_confirm_{trade_id}")
    seller_keyboard.row(InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu"))
    
    await bot.send_message(
        order['user_id'],
        f"🔄 <b>НОВАЯ СДЕЛКА!</b>\n\n"
        f"Покупатель хочет купить {amount} {order['game_name']}\n"
        f"на сумму {total:.0f} ₽\n\n"
        f"Деньги уже списаны с его счёта.\n"
        f"Подтверди сделку, если всё хорошо:",
        reply_markup=seller_keyboard.as_markup()
    )

# ============================================
# ПОДТВЕРЖДЕНИЕ СДЕЛКИ
# ============================================

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
    
    # Завершаем сделку
    db.complete_trade(trade_id)
    
    # Переводим деньги продавцу
    db.update_balance(trade['seller_id'], trade['total'] - trade['commission'])
    
    await callback.message.edit_text(
        f"✅ <b>СДЕЛКА ПОДТВЕРЖДЕНА!</b>\n\n"
        f"Сделка #{trade_id} завершена.\n"
        f"Деньги поступили на твой счёт.\n\n"
        f"Комиссия платформы: {trade['commission']} ₽"
    )
    
    # Предлагаем оставить отзыв покупателю
    await bot.send_message(
        trade['buyer_id'],
        f"✅ <b>СДЕЛКА ЗАВЕРШЕНА!</b>\n\n"
        f"Продавец подтвердил получение денег.\n\n"
        f"Оцени продавца:",
        reply_markup=review_keyboard(trade_id, trade['seller_id'])
    )
    await callback.answer()

# ============================================
# ОТЗЫВЫ
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

# ============================================
# МОИ СДЕЛКИ
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
    
    for trade in trades[:10]:
        status_emoji = "✅" if trade['status'] == 'completed' else "⏳"
        role = "📤" if trade['seller_id'] == callback.from_user.id else "📥"
        text += f"{status_emoji} {role} #{trade['id']} - {trade['total']} ₽\n"
    
    await callback.message.edit_text(text, reply_markup=back_keyboard())
    await callback.answer()

# ============================================
# ЗАПУСК БОТА
# ============================================

async def on_startup():
    print("\n" + "="*50)
    print("🔥 P2P МАРКЕТПЛЕЙС ЗАПУЩЕН!")
    print("="*50)
    print(f"🤖 Бот: @{(await bot.get_me()).username}")
    print(f"👑 Админ ID: {ADMIN_ID}")
    print(f"🎮 Игр в базе: {len(GAMES)}")
    print(f"⚡ Комиссия: {COMMISSION}%")
    print("="*50 + "\n")
    
    await bot.send_message(
        ADMIN_ID,
        f"🚀 <b>P2P МАРКЕТПЛЕЙС ЗАПУЩЕН!</b>\n\n"
        f"✅ Все системы работают!\n"
        f"🎮 Тестовый баланс: 10000 ₽"
    )

async def main():
    await on_startup()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
