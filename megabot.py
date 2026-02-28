#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
██████╗ ██████╗ ██████╗     ██████╗  ██████╗ ████████╗
██╔══██╗╚════██╗╚════██╗    ██╔══██╗██╔═══██╗╚══██╔══╝
██████╔╝ █████╔╝ █████╔╝    ██████╔╝██║   ██║   ██║   
██╔═══╝  ╚═══██╗ ╚═══██╗    ██╔═══╝ ██║   ██║   ██║   
██║     ██████╔╝██████╔╝    ██║     ╚██████╔╝   ██║   
╚═╝     ╚═════╝ ╚═════╝     ╚═╝      ╚═════╝    ╚═╝   
                                                        
         🎮 ГЕЙМИНГ P2P + КРИПТО-БИРЖА 🎮
              СТАБИЛЬНАЯ РАБОЧАЯ ВЕРСИЯ
"""

import os
import sys
import sqlite3
import logging
import asyncio
import random
import string
from datetime import datetime, timedelta

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
# НАСТРОЙКИ
# ============================================

COMMISSION = 1.0  # %
ESCROW_TIME = 60  # минут
MIN_AMOUNT = 100  # рублей
REFERRAL_BONUS = 10  # %

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
# ПЛАТЁЖНЫЕ МЕТОДЫ
# ============================================

PAYMENT_METHODS = [
    {"id": "sbp", "name": "СБП", "icon": "💳"},
    {"id": "card", "name": "Карта РФ", "icon": "💳"},
    {"id": "yoomoney", "name": "ЮMoney", "icon": "💰"},
    {"id": "qiwi", "name": "Qiwi", "icon": "📱"},
    {"id": "cash", "name": "Наличные", "icon": "💵"},
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

# ============================================
# БАЗА ДАННЫХ (ПРОСТАЯ И РАБОЧАЯ)
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
                referrer_id INTEGER,
                referral_code TEXT,
                rating REAL DEFAULT 5.0,
                deals INTEGER DEFAULT 0,
                balance REAL DEFAULT 0
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
                comment TEXT,
                payment_method TEXT,
                status TEXT DEFAULT 'active',
                created_at TEXT
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
                total REAL,
                commission REAL,
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                expires_at TEXT
            )
        ''')
        
        self.conn.commit()
    
    # ========== ПОЛЬЗОВАТЕЛИ ==========
    
    def add_user(self, user_id, username, first_name, referrer_code=None):
        # Проверяем, есть ли уже
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
            INSERT INTO users (user_id, username, first_name, registered_at, referrer_id, referral_code)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, datetime.now().isoformat(), referrer_id, ref_code))
        
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
                'deals': row[7],
                'balance': row[8]
            }
        return None
    
    # ========== ОРДЕРА ==========
    
    def create_order(self, user_id, market_type, item, order_type, amount, price, comment, payment_method):
        total = amount * price
        
        self.cursor.execute('''
            INSERT INTO orders 
            (user_id, market_type, item_id, item_name, item_icon, order_type, amount, price, total, comment, payment_method, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            comment, 
            payment_method,
            datetime.now().isoformat()
        ))
        
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_orders(self, market_type=None, item_id=None, status='active'):
        query = 'SELECT * FROM orders WHERE status = ?'
        params = [status]
        
        if market_type:
            query += ' AND market_type = ?'
            params.append(market_type)
        
        if item_id:
            query += ' AND item_id = ?'
            params.append(item_id)
        
        query += ' ORDER BY created_at DESC'
        
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
                'comment': row[10],
                'payment_method': row[11],
                'status': row[12],
                'created_at': row[13]
            })
        return orders
    
    def get_order(self, order_id):
        self.cursor.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
        row = self.cursor.fetchone()
        if row:
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
                'comment': row[10],
                'payment_method': row[11],
                'status': row[12],
                'created_at': row[13]
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
        if not order:
            return None
        
        total = amount * order['price']
        commission = total * (COMMISSION / 100)
        
        self.cursor.execute('''
            INSERT INTO trades (order_id, seller_id, buyer_id, amount, total, commission, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            order_id, 
            order['user_id'], 
            buyer_id, 
            amount, 
            total, 
            commission,
            datetime.now().isoformat(),
            (datetime.now() + timedelta(minutes=ESCROW_TIME)).isoformat()
        ))
        
        trade_id = self.cursor.lastrowid
        
        # Обновляем ордер
        new_amount = order['amount'] - amount
        self.update_order_amount(order_id, new_amount)
        
        self.conn.commit()
        return trade_id
    
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
                'total': row[5],
                'commission': row[6],
                'status': row[7],
                'created_at': row[8],
                'expires_at': row[9]
            })
        return trades

db = Database()

# ============================================
# БОТ
# ============================================

storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=storage)

# Временные данные
user_temp = {}

# ============================================
# КЛАВИАТУРЫ
# ============================================

def main_keyboard():
    builder = ReplyKeyboardBuilder()
    buttons = [
        KeyboardButton(text="🎮 Игры"),
        KeyboardButton(text="💰 Крипта"),
        KeyboardButton(text="👤 Профиль"),
        KeyboardButton(text="❓ Помощь")
    ]
    builder.add(*buttons)
    builder.adjust(2, 2)
    return builder.as_markup(resize_keyboard=True)

def games_keyboard():
    builder = InlineKeyboardBuilder()
    for game in GAMES:
        builder.button(
            text=f"{game['icon']} {game['name']}", 
            callback_data=f"game_{game['id']}"
        )
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="➕ Создать ордер", callback_data="create_game"))
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    return builder.as_markup()

def crypto_keyboard():
    builder = InlineKeyboardBuilder()
    for crypto in CRYPTO:
        builder.button(
            text=f"{crypto['icon']} {crypto['name']}", 
            callback_data=f"crypto_{crypto['id']}"
        )
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="➕ Создать ордер", callback_data="create_crypto"))
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    return builder.as_markup()

def order_type_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📈 Купить", callback_data="type_buy")
    builder.button(text="📉 Продать", callback_data="type_sell")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back"))
    return builder.as_markup()

def payment_keyboard():
    builder = InlineKeyboardBuilder()
    for pm in PAYMENT_METHODS:
        builder.button(text=f"{pm['icon']} {pm['name']}", callback_data=f"payment_{pm['id']}")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back"))
    return builder.as_markup()

def back_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад", callback_data="back")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(2)
    return builder.as_markup()

# ============================================
# СТАРТ
# ============================================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    user = message.from_user
    args = message.text.split()
    ref_code = args[1] if len(args) > 1 else None
    
    db.add_user(user.id, user.username, user.first_name, ref_code)
    
    await message.answer(
        f"👋 <b>Привет, {user.first_name}!</b>\n\n"
        f"🎮 P2P биржа игровой валюты и крипты\n"
        f"🤝 Безопасные сделки через гаранта\n"
        f"💰 Комиссия {COMMISSION}%\n\n"
        f"👇 Выбери раздел:",
        reply_markup=main_keyboard()
    )

# ============================================
# ГЛАВНОЕ МЕНЮ
# ============================================

@dp.message(lambda m: m.text == "🎮 Игры")
async def games_section(message: Message):
    await message.answer("🎮 <b>Выбери игру:</b>", reply_markup=games_keyboard())

@dp.message(lambda m: m.text == "💰 Крипта")
async def crypto_section(message: Message):
    await message.answer("💰 <b>Выбери криптовалюту:</b>", reply_markup=crypto_keyboard())

@dp.message(lambda m: m.text == "👤 Профиль")
async def profile_section(message: Message):
    user = db.get_user(message.from_user.id)
    if user:
        trades = db.get_user_trades(message.from_user.id)
        text = (
            f"👤 <b>Профиль</b>\n\n"
            f"📊 Сделок: {len(trades)}\n"
            f"⭐ Рейтинг: {user['rating']}\n"
            f"💰 Баланс: {user['balance']} ₽\n"
        )
        
        builder = InlineKeyboardBuilder()
        builder.button(text="📊 Мои сделки", callback_data="my_trades")
        builder.button(text="🏠 Главное меню", callback_data="main_menu")
        builder.adjust(2)
        
        await message.answer(text, reply_markup=builder.as_markup())

@dp.message(lambda m: m.text == "❓ Помощь")
async def help_section(message: Message):
    text = (
        "❓ <b>Помощь</b>\n\n"
        "1️⃣ <b>Найди ордер</b> — выбери игру или крипту\n"
        "2️⃣ <b>Нажми «Купить»</b> — введи количество\n"
        "3️⃣ <b>Оплати</b> — переведи деньги продавцу\n"
        "4️⃣ <b>Подтверди</b> — нажми «Я оплатил»\n"
        "5️⃣ <b>Получи</b> — продавец подтвердит и товар твой\n\n"
        f"⏱ Время на оплату: {ESCROW_TIME} минут\n"
        f"💰 Комиссия: {COMMISSION}%\n\n"
        f"📞 Связь с админом: @p2p_support"
    )
    await message.answer(text, reply_markup=back_keyboard())

# ============================================
# НАВИГАЦИЯ
# ============================================

@dp.callback_query(lambda c: c.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        "🏠 <b>Главное меню</b>",
        reply_markup=main_keyboard()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "back")
async def back_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🎮 <b>Выбери игру:</b>",
        reply_markup=games_keyboard()
    )
    await callback.answer()

# ============================================
# ПОКАЗ ОРДЕРОВ (ИГРЫ)
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
            f"{game['icon']} <b>{game['name']}</b>\n\n"
            f"Нет активных ордеров.\n"
            f"Создай первый! 🚀",
            reply_markup=back_keyboard()
        )
        await callback.answer()
        return
    
    text = f"{game['icon']} <b>{game['name']} - ордера:</b>\n\n"
    builder = InlineKeyboardBuilder()
    
    for order in orders[:5]:
        emoji = "📈" if order['order_type'] == 'sell' else "📉"
        text += f"{emoji} {order['amount']:.0f} {game['currency']} × {order['price']}₽ = {order['total']:.0f}₽\n"
        builder.button(
            text=f"{emoji} {order['amount']:.0f} {game['currency']}",
            callback_data=f"view_order_{order['id']}"
        )
    
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="➕ Создать ордер", callback_data=f"create_game_{game_id}"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

# ============================================
# ПОКАЗ ОРДЕРОВ (КРИПТА)
# ============================================

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
            f"{crypto['icon']} <b>{crypto['name']}</b>\n\n"
            f"Нет активных ордеров.\n"
            f"Создай первый! 🚀",
            reply_markup=back_keyboard()
        )
        await callback.answer()
        return
    
    text = f"{crypto['icon']} <b>{crypto['name']} - ордера:</b>\n\n"
    builder = InlineKeyboardBuilder()
    
    for order in orders[:5]:
        emoji = "📈" if order['order_type'] == 'sell' else "📉"
        text += f"{emoji} {order['amount']} {crypto_id.upper()} × {order['price']}₽ = {order['total']:.0f}₽\n"
        builder.button(
            text=f"{emoji} {order['amount']} {crypto_id.upper()}",
            callback_data=f"view_order_{order['id']}"
        )
    
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="➕ Создать ордер", callback_data=f"create_crypto_{crypto_id}"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

# ============================================
# ПРОСМОТР ОРДЕРА
# ============================================

@dp.callback_query(lambda c: c.data.startswith('view_order_'))
async def view_order(callback: CallbackQuery):
    order_id = int(callback.data.replace('view_order_', ''))
    order = db.get_order(order_id)
    
    if not order:
        await callback.answer("❌ Ордер не найден", show_alert=True)
        return
    
    text = (
        f"{order['item_icon']} <b>{order['item_name']}</b>\n"
        f"{'📈 ПРОДАЖА' if order['order_type'] == 'sell' else '📉 ПОКУПКА'}\n\n"
        f"💰 Количество: {order['amount']}\n"
        f"💵 Цена: {order['price']} ₽\n"
        f"💎 Сумма: {order['total']} ₽\n"
    )
    
    if order['comment']:
        text += f"\n📝 {order['comment']}\n"
    
    text += f"\n🕐 {order['created_at'][:16]}"
    
    builder = InlineKeyboardBuilder()
    
    if order['order_type'] == 'sell' and order['user_id'] != callback.from_user.id:
        builder.button(text="💎 Купить", callback_data=f"buy_{order['id']}")
    
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=f"{order['market_type']}_{order['item_id']}"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

# ============================================
# СОЗДАНИЕ ОРДЕРА (НАЧАЛО)
# ============================================

@dp.callback_query(lambda c: c.data == "create_game")
async def create_game_start(callback: CallbackQuery, state: FSMContext):
    await state.update_data(market_type='game')
    
    builder = InlineKeyboardBuilder()
    for game in GAMES:
        builder.button(text=f"{game['icon']} {game['name']}", callback_data=f"create_item_{game['id']}")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back"))
    
    await callback.message.edit_text(
        "🎮 <b>Выбери игру:</b>",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "create_crypto")
async def create_crypto_start(callback: CallbackQuery, state: FSMContext):
    await state.update_data(market_type='crypto')
    
    builder = InlineKeyboardBuilder()
    for crypto in CRYPTO:
        builder.button(text=f"{crypto['icon']} {crypto['name']}", callback_data=f"create_item_{crypto['id']}")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back"))
    
    await callback.message.edit_text(
        "💰 <b>Выбери валюту:</b>",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith('create_item_'))
async def create_order_item(callback: CallbackQuery, state: FSMContext):
    item_id = callback.data.replace('create_item_', '')
    data = await state.get_data()
    
    if data['market_type'] == 'game':
        item = next((g for g in GAMES if g['id'] == item_id), None)
    else:
        item = next((c for c in CRYPTO if c['id'] == item_id), None)
    
    if not item:
        await callback.answer("❌ Не найдено")
        return
    
    await state.update_data(item=item)
    await state.set_state(OrderStates.choosing_type)
    
    await callback.message.edit_text(
        f"{item['icon']} <b>{item['name']}</b>\n\n"
        f"Ты хочешь купить или продать?",
        reply_markup=order_type_keyboard()
    )
    await callback.answer()

@dp.callback_query(OrderStates.choosing_type, lambda c: c.data.startswith('type_'))
async def create_order_type(callback: CallbackQuery, state: FSMContext):
    order_type = callback.data.replace('type_', '')
    await state.update_data(order_type=order_type)
    await state.set_state(OrderStates.entering_amount)
    
    await callback.message.edit_text(
        f"💰 <b>Введи количество:</b>\n\n"
        f"Отправь число (например: 100)"
    )
    await callback.answer()

# ============================================
# ВВОД ДАННЫХ
# ============================================

@dp.message(OrderStates.entering_amount)
async def enter_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError
    except:
        await message.answer("❌ Введи положительное число")
        return
    
    await state.update_data(amount=amount)
    await state.set_state(OrderStates.entering_price)
    await message.answer(f"💵 <b>Введи цену за единицу (в ₽):</b>")

@dp.message(OrderStates.entering_price)
async def enter_price(message: Message, state: FSMContext):
    try:
        price = float(message.text)
        if price <= 0:
            raise ValueError
    except:
        await message.answer("❌ Введи положительное число")
        return
    
    data = await state.get_data()
    total = data['amount'] * price
    
    if total < MIN_AMOUNT:
        await message.answer(f"❌ Минимальная сумма {MIN_AMOUNT} ₽. Увеличь количество или цену.")
        return
    
    await state.update_data(price=price)
    await state.set_state(OrderStates.entering_comment)
    await message.answer(
        f"📝 <b>Комментарий (или отправь «-» чтобы пропустить):</b>"
    )

@dp.message(OrderStates.entering_comment)
async def enter_comment(message: Message, state: FSMContext):
    comment = message.text if message.text != '-' else ''
    await state.update_data(comment=comment)
    await state.set_state(OrderStates.choosing_payment)
    
    await message.answer(
        f"💳 <b>Выбери способ оплаты:</b>",
        reply_markup=payment_keyboard()
    )

@dp.callback_query(OrderStates.choosing_payment, lambda c: c.data.startswith('payment_'))
async def choose_payment(callback: CallbackQuery, state: FSMContext):
    payment = callback.data.replace('payment_', '')
    pm = next((p for p in PAYMENT_METHODS if p['id'] == payment), None)
    
    await state.update_data(payment_method=payment, payment_name=pm['name'])
    await state.set_state(OrderStates.confirming)
    
    data = await state.get_data()
    total = data['amount'] * data['price']
    
    text = (
        f"{data['item']['icon']} <b>Проверь данные:</b>\n\n"
        f"Тип: {'📈 Продажа' if data['order_type'] == 'sell' else '📉 Покупка'}\n"
        f"Товар: {data['item']['name']}\n"
        f"Количество: {data['amount']}\n"
        f"Цена: {data['price']} ₽\n"
        f"Сумма: {total} ₽\n"
        f"Оплата: {pm['name']}\n"
    )
    
    if data['comment']:
        text += f"Комментарий: {data['comment']}\n"
    
    text += f"\n✅ Всё верно?"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, создать", callback_data="confirm_order")
    builder.button(text="❌ Нет, заново", callback_data="cancel_order")
    builder.adjust(2)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(OrderStates.confirming, lambda c: c.data == "confirm_order")
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    order_id = db.create_order(
        user_id=callback.from_user.id,
        market_type=data['market_type'],
        item=data['item'],
        order_type=data['order_type'],
        amount=data['amount'],
        price=data['price'],
        comment=data['comment'],
        payment_method=data['payment_method']
    )
    
    await state.clear()
    
    await callback.message.edit_text(
        f"✅ <b>Ордер создан!</b>\n\n"
        f"ID: {order_id}\n"
        f"Он появится в списке ордеров.",
        reply_markup=back_keyboard()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "cancel_order")
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ Создание отменено",
        reply_markup=games_keyboard()
    )
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
        f"💰 <b>Введи количество:</b>\n\n"
        f"Доступно: {order['amount']}\n"
        f"Цена: {order['price']} ₽",
        reply_markup=back_keyboard()
    )
    await callback.answer()

@dp.message(TradeStates.entering_amount)
async def buy_enter_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
    except:
        await message.answer("❌ Введи число")
        return
    
    data = await state.get_data()
    order = db.get_order(data['order_id'])
    
    if not order:
        await message.answer("❌ Ордер не найден")
        await state.clear()
        return
    
    if amount > order['amount']:
        await message.answer(f"❌ Максимум {order['amount']}")
        return
    
    if amount * order['price'] < MIN_AMOUNT:
        await message.answer(f"❌ Минимальная сумма {MIN_AMOUNT} ₽")
        return
    
    # Создаём сделку
    trade_id = db.create_trade(data['order_id'], message.from_user.id, amount)
    
    if not trade_id:
        await message.answer("❌ Ошибка создания сделки")
        await state.clear()
        return
    
    await state.clear()
    
    await message.answer(
        f"✅ <b>Сделка создана!</b>\n\n"
        f"ID: {trade_id}\n"
        f"Сумма: {amount * order['price']} ₽\n\n"
        f"💰 Переведи деньги продавцу\n"
        f"⏱ Время: {ESCROW_TIME} минут",
        reply_markup=back_keyboard()
    )

# ============================================
# МОИ СДЕЛКИ
# ============================================

@dp.callback_query(lambda c: c.data == "my_trades")
async def my_trades(callback: CallbackQuery):
    trades = db.get_user_trades(callback.from_user.id)
    
    if not trades:
        await callback.message.edit_text(
            "📊 <b>Мои сделки</b>\n\n"
            "У тебя пока нет сделок.",
            reply_markup=back_keyboard()
        )
        await callback.answer()
        return
    
    text = "📊 <b>Мои сделки:</b>\n\n"
    for trade in trades:
        status = "✅" if trade['status'] == 'completed' else "⏳"
        text += f"{status} {trade['total']} ₽ - {trade['created_at'][:16]}\n"
    
    await callback.message.edit_text(text, reply_markup=back_keyboard())
    await callback.answer()

# ============================================
# ЗАПУСК
# ============================================

async def main():
    print("\n" + "="*50)
    print("🔥 P2P БОТ ЗАПУСКАЕТСЯ...")
    print("="*50)
    
    me = await bot.get_me()
    print(f"✅ Бот: @{me.username}")
    print(f"👑 Админ: {ADMIN_ID}")
    print("="*50 + "\n")
    
    await bot.send_message(ADMIN_ID, "🚀 <b>Бот запущен и готов к работе!</b>")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
