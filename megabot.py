#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
██████╗ ██████╗ ██████╗     ███████╗████████╗ █████╗ ██████╗ ██╗     ███████╗
██╔══██╗╚════██╗╚════██╗    ██╔════╝╚══██╔══╝██╔══██╗██╔══██╗██║     ██╔════╝
██████╔╝ █████╔╝ █████╔╝    ███████╗   ██║   ███████║██████╔╝██║     █████╗  
██╔═══╝  ╚═══██╗ ╚═══██╗    ╚════██║   ██║   ██╔══██║██╔══██╗██║     ██╔══╝  
██║     ██████╔╝██████╔╝    ███████║   ██║   ██║  ██║██████╔╝███████╗███████╗
╚═╝     ╚═════╝ ╚═════╝     ╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═════╝ ╚══════╝╚══════╝

              🎮 P2P ГЕЙМИНГ МАРКЕТПЛЕЙС + КРИПТО-БИРЖА 🎮
                          СТАБИЛЬНАЯ ВЕРСИЯ
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
MIN_DEAL_AMOUNT = 100  # Минимальная сумма (руб)
REFERRAL_BONUS = 10  # Бонус рефереру (%)

# ============================================
# ИГРЫ
# ============================================

GAMES = {
    'pubg': {'name': 'PUBG Mobile', 'currency': 'UC', 'icon': '🪖'},
    'brawl': {'name': 'Brawl Stars', 'currency': 'гемы', 'icon': '🥊'},
    'freefire': {'name': 'Free Fire', 'currency': 'алмазы', 'icon': '🔥'},
    'steam': {'name': 'Steam', 'currency': 'руб', 'icon': '🎮'},
    'genshin': {'name': 'Genshin Impact', 'currency': 'кристаллы', 'icon': '✨'},
    'cod': {'name': 'Call of Duty', 'currency': 'CP', 'icon': '🔫'},
    'roblox': {'name': 'Roblox', 'currency': 'Robux', 'icon': '🎲'},
    'fortnite': {'name': 'Fortnite', 'currency': 'V-bucks', 'icon': '🛡️'}
}

# ============================================
# КРИПТОВАЛЮТЫ
# ============================================

CRYPTO_CURRENCIES = {
    'USDT': {'name': 'Tether', 'icon': '💵', 'network': 'TRC20'},
    'TON': {'name': 'Toncoin', 'icon': '💎', 'network': 'TON'},
    'BTC': {'name': 'Bitcoin', 'icon': '₿', 'network': 'BTC'}
}

# ============================================
# ПЛАТЁЖНЫЕ МЕТОДЫ
# ============================================

PAYMENT_METHODS = {
    'sbp': {'name': 'СБП', 'icon': '💳'},
    'card': {'name': 'Карта', 'icon': '💳'},
    'yoomoney': {'name': 'ЮMoney', 'icon': '💰'},
    'qiwi': {'name': 'Qiwi', 'icon': '📱'},
    'cash': {'name': 'Наличные', 'icon': '💵'}
}

# ============================================
# СОСТОЯНИЯ FSM
# ============================================

class CreateOrder(StatesGroup):
    choosing_market = State()  # game или crypto
    choosing_item = State()     # игра или валюта
    choosing_type = State()     # buy или sell
    entering_amount = State()   # количество
    entering_price = State()    # цена
    entering_comment = State()  # комментарий
    choosing_payment = State()  # способ оплаты
    confirm = State()           # подтверждение

class TradeProcess(StatesGroup):
    waiting_payment = State()
    waiting_confirmation = State()
    waiting_review = State()

# ============================================
# БАЗА ДАННЫХ (ПРОСТАЯ И РАБОЧАЯ)
# ============================================

class Database:
    def __init__(self, db_name="p2p_bot.db"):
        self.db_name = db_name
        self.init_db()
    
    def get_connection(self):
        return sqlite3.connect(self.db_name)
    
    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Пользователи
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                registered_at TIMESTAMP,
                referrer_id INTEGER DEFAULT NULL,
                referral_code TEXT UNIQUE,
                rating REAL DEFAULT 5.0,
                deals INTEGER DEFAULT 0,
                balance REAL DEFAULT 0
            )
        ''')
        
        # Ордера
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                market_type TEXT,
                item_id TEXT,
                item_name TEXT,
                order_type TEXT,
                amount REAL,
                price REAL,
                total REAL,
                comment TEXT,
                payment_method TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP
            )
        ''')
        
        # Сделки
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                seller_id INTEGER,
                buyer_id INTEGER,
                amount REAL,
                total REAL,
                commission REAL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP,
                expires_at TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # ========== ПОЛЬЗОВАТЕЛИ ==========
    
    def add_user(self, user_id, username, first_name, referrer_code=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        ref_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        referrer_id = None
        if referrer_code:
            cursor.execute('SELECT user_id FROM users WHERE referral_code = ?', (referrer_code,))
            res = cursor.fetchone()
            if res:
                referrer_id = res[0]
        
        cursor.execute('''
            INSERT OR REPLACE INTO users 
            (user_id, username, first_name, registered_at, referrer_id, referral_code)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, datetime.now(), referrer_id, ref_code))
        
        conn.commit()
        conn.close()
        return ref_code
    
    def get_user(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
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
    
    def create_order(self, user_id, market_type, item_id, item_name, order_type, 
                    amount, price, comment, payment_method):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        total = amount * price
        
        cursor.execute('''
            INSERT INTO orders 
            (user_id, market_type, item_id, item_name, order_type, amount, price, total, comment, payment_method, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, market_type, item_id, item_name, order_type, amount, price, total, 
              comment, payment_method, datetime.now()))
        
        order_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return order_id
    
    def get_active_orders(self, market_type=None, item_id=None, limit=20):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM orders WHERE status = "active"'
        params = []
        
        if market_type:
            query += ' AND market_type = ?'
            params.append(market_type)
        
        if item_id:
            query += ' AND item_id = ?'
            params.append(item_id)
        
        query += ' ORDER BY created_at DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        orders = []
        for row in rows:
            orders.append({
                'id': row[0],
                'user_id': row[1],
                'market_type': row[2],
                'item_id': row[3],
                'item_name': row[4],
                'order_type': row[5],
                'amount': row[6],
                'price': row[7],
                'total': row[8],
                'comment': row[9],
                'payment_method': row[10],
                'status': row[11],
                'created_at': row[12]
            })
        return orders
    
    def get_order(self, order_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'user_id': row[1],
                'market_type': row[2],
                'item_id': row[3],
                'item_name': row[4],
                'order_type': row[5],
                'amount': row[6],
                'price': row[7],
                'total': row[8],
                'comment': row[9],
                'payment_method': row[10],
                'status': row[11],
                'created_at': row[12]
            }
        return None
    
    def close_order(self, order_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE orders SET status = "completed" WHERE id = ?', (order_id,))
        conn.commit()
        conn.close()
    
    # ========== СДЕЛКИ ==========
    
    def create_trade(self, order_id, buyer_id, amount):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        order = self.get_order(order_id)
        if not order:
            conn.close()
            return None
        
        total = amount * order['price']
        commission = total * (COMMISSION / 100)
        
        cursor.execute('''
            INSERT INTO trades 
            (order_id, seller_id, buyer_id, amount, total, commission, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (order_id, order['user_id'], buyer_id, amount, total, commission, 
              datetime.now(), datetime.now() + timedelta(minutes=ESCROW_TIME)))
        
        trade_id = cursor.lastrowid
        
        # Обновляем ордер
        new_amount = order['amount'] - amount
        if new_amount <= 0:
            cursor.execute('UPDATE orders SET status = "completed" WHERE id = ?', (order_id,))
        else:
            cursor.execute('UPDATE orders SET amount = ? WHERE id = ?', (new_amount, order_id))
        
        conn.commit()
        conn.close()
        return trade_id
    
    def get_trade(self, trade_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM trades WHERE id = ?', (trade_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
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
            }
        return None
    
    def complete_trade(self, trade_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE trades SET status = "completed" WHERE id = ?', (trade_id,))
        
        # Начисляем комиссию админу
        trade = self.get_trade(trade_id)
        if trade:
            cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', 
                          (trade['commission'], ADMIN_ID))
        
        conn.commit()
        conn.close()
    
    def get_user_trades(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM trades 
            WHERE seller_id = ? OR buyer_id = ?
            ORDER BY created_at DESC LIMIT 10
        ''', (user_id, user_id))
        rows = cursor.fetchall()
        conn.close()
        
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
# КЛАВИАТУРЫ (ПРОСТЫЕ И ПОНЯТНЫЕ)
# ============================================

def main_keyboard():
    builder = ReplyKeyboardBuilder()
    buttons = [
        KeyboardButton(text="🎮 Игры"),
        KeyboardButton(text="💰 Крипта"),
        KeyboardButton(text="👤 Профиль"),
        KeyboardButton(text="📞 Помощь")
    ]
    builder.add(*buttons)
    builder.adjust(2, 2)
    return builder.as_markup(resize_keyboard=True)

def games_keyboard():
    builder = InlineKeyboardBuilder()
    for game_id, game in GAMES.items():
        builder.button(text=f"{game['icon']} {game['name']}", callback_data=f"game_{game_id}")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="➕ Создать ордер", callback_data="create_game_order"))
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    return builder.as_markup()

def crypto_keyboard():
    builder = InlineKeyboardBuilder()
    for curr_id, curr in CRYPTO_CURRENCIES.items():
        builder.button(text=f"{curr['icon']} {curr_id}", callback_data=f"crypto_{curr_id}")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="➕ Создать ордер", callback_data="create_crypto_order"))
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
    for pid, pm in PAYMENT_METHODS.items():
        builder.button(text=f"{pm['icon']} {pm['name']}", callback_data=f"payment_{pid}")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back"))
    return builder.as_markup()

def back_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад", callback_data="back")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(2)
    return builder.as_markup()

def profile_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Мои сделки", callback_data="my_trades")
    builder.button(text="💰 Баланс", callback_data="balance")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(2, 1)
    return builder.as_markup()

# ============================================
# БОТ
# ============================================

storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=storage)

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
        f"🎮 Здесь ты можешь:\n"
        f"• Покупать и продавать игровую валюту\n"
        f"• Торговать криптовалютой P2P\n"
        f"• Безопасные сделки через гаранта\n\n"
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
    await message.answer("💰 <b>Выбери валюту:</b>", reply_markup=crypto_keyboard())

@dp.message(lambda m: m.text == "👤 Профиль")
async def profile_section(message: Message):
    user = db.get_user(message.from_user.id)
    if user:
        text = (
            f"👤 <b>Твой профиль</b>\n\n"
            f"📊 Сделок: {user['deals']}\n"
            f"⭐ Рейтинг: {user['rating']}\n"
            f"💰 Баланс: {user['balance']} ₽\n"
        )
        await message.answer(text, reply_markup=profile_keyboard())

@dp.message(lambda m: m.text == "📞 Помощь")
async def help_section(message: Message):
    text = (
        "📞 <b>Помощь</b>\n\n"
        "1. Найди ордер\n"
        "2. Нажми «Купить»\n"
        "3. Введи количество\n"
        "4. Оплати продавцу\n"
        "5. Подтверди получение\n\n"
        f"⏱ Время на оплату: {ESCROW_TIME} минут\n"
        f"💰 Комиссия: {COMMISSION}%\n\n"
        "❓ Вопросы: @admin"
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
    current_state = await state.get_state()
    
    if current_state:
        await state.clear()
        await callback.message.edit_text(
            "🎮 <b>Выбери игру:</b>",
            reply_markup=games_keyboard()
        )
    else:
        await callback.message.edit_text(
            "🎮 <b>Выбери игру:</b>",
            reply_markup=games_keyboard()
        )
    
    await callback.answer()

# ============================================
# ПРОСМОТР ОРДЕРОВ (ИГРЫ)
# ============================================

@dp.callback_query(lambda c: c.data.startswith('game_'))
async def show_game_orders(callback: CallbackQuery):
    game_id = callback.data.replace('game_', '')
    game = GAMES[game_id]
    
    orders = db.get_active_orders(market_type='game', item_id=game_id)
    
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
# ПРОСМОТР ОРДЕРОВ (КРИПТА)
# ============================================

@dp.callback_query(lambda c: c.data.startswith('crypto_'))
async def show_crypto_orders(callback: CallbackQuery):
    curr_id = callback.data.replace('crypto_', '')
    currency = CRYPTO_CURRENCIES[curr_id]
    
    orders = db.get_active_orders(market_type='crypto', item_id=curr_id)
    
    if not orders:
        await callback.message.edit_text(
            f"{currency['icon']} <b>{curr_id}</b>\n\n"
            f"Нет активных ордеров.\n"
            f"Создай первый! 🚀",
            reply_markup=back_keyboard()
        )
        await callback.answer()
        return
    
    text = f"{currency['icon']} <b>{curr_id} - ордера:</b>\n\n"
    
    builder = InlineKeyboardBuilder()
    
    for order in orders[:5]:
        emoji = "📈" if order['order_type'] == 'sell' else "📉"
        text += f"{emoji} {order['amount']} {curr_id} × {order['price']}₽ = {order['total']:.0f}₽\n"
        
        builder.button(
            text=f"{emoji} {order['amount']} {curr_id}",
            callback_data=f"view_order_{order['id']}"
        )
    
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="➕ Создать ордер", callback_data=f"create_crypto_{curr_id}"))
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
    
    if order['market_type'] == 'game':
        game = GAMES[order['item_id']]
        icon = game['icon']
        currency = game['currency']
    else:
        currency = CRYPTO_CURRENCIES[order['item_id']]
        icon = currency['icon']
        currency = order['item_id']
    
    text = (
        f"{icon} <b>{order['item_name']}</b>\n"
        f"{'📈 ПРОДАЖА' if order['order_type'] == 'sell' else '📉 ПОКУПКА'}\n\n"
        
        f"💰 Количество: {order['amount']} {currency}\n"
        f"💵 Цена: {order['price']} ₽\n"
        f"💎 Сумма: {order['total']} ₽\n\n"
    )
    
    if order['comment']:
        text += f"📝 {order['comment']}\n\n"
    
    text += f"🕐 Создан: {order['created_at'][:16]}"
    
    builder = InlineKeyboardBuilder()
    
    if order['order_type'] == 'sell':
        builder.button(text="💎 Купить", callback_data=f"buy_{order_id}")
    else:
        builder.button(text="💎 Продать", callback_data=f"sell_{order_id}")
    
    builder.button(text="⭐ В избранное", callback_data=f"fav_{order_id}")
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=f"{order['market_type']}_{order['item_id']}"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

# ============================================
# СОЗДАНИЕ ОРДЕРА (ИГРЫ)
# ============================================

@dp.callback_query(lambda c: c.data.startswith('create_game_'))
async def create_game_order_start(callback: CallbackQuery, state: FSMContext):
    game_id = callback.data.replace('create_game_', '')
    game = GAMES[game_id]
    
    await state.update_data(market_type='game', item_id=game_id, item_name=game['name'])
    await state.set_state(CreateOrder.choosing_type)
    
    await callback.message.edit_text(
        f"{game['icon']} <b>{game['name']}</b>\n\n"
        f"Ты хочешь купить или продать?",
        reply_markup=order_type_keyboard()
    )
    await callback.answer()

@dp.callback_query(CreateOrder.choosing_type, lambda c: c.data.startswith('type_'))
async def create_order_type(callback: CallbackQuery, state: FSMContext):
    order_type = callback.data.replace('type_', '')
    
    await state.update_data(order_type=order_type)
    await state.set_state(CreateOrder.entering_amount)
    
    await callback.message.edit_text(
        f"💰 <b>Введи количество:</b>\n\n"
        f"Минимальная сумма: {MIN_DEAL_AMOUNT} ₽"
    )
    await callback.answer()

@dp.message(CreateOrder.entering_amount)
async def create_order_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError
    except:
        await message.answer("❌ Введи число больше 0")
        return
    
    await state.update_data(amount=amount)
    await state.set_state(CreateOrder.entering_price)
    
    await message.answer(
        f"💵 <b>Введи цену за единицу (в ₽):</b>"
    )

@dp.message(CreateOrder.entering_price)
async def create_order_price(message: Message, state: FSMContext):
    try:
        price = float(message.text)
        if price <= 0:
            raise ValueError
    except:
        await message.answer("❌ Введи число больше 0")
        return
    
    data = await state.get_data()
    total = data['amount'] * price
    
    if total < MIN_DEAL_AMOUNT:
        await message.answer(f"❌ Минимальная сумма сделки {MIN_DEAL_AMOUNT} ₽. Увеличь количество или цену.")
        return
    
    await state.update_data(price=price)
    await state.set_state(CreateOrder.entering_comment)
    
    await message.answer(
        f"📝 <b>Добавь комментарий (или отправь «-» чтобы пропустить):</b>"
    )

@dp.message(CreateOrder.entering_comment)
async def create_order_comment(message: Message, state: FSMContext):
    comment = message.text if message.text != '-' else ''
    
    await state.update_data(comment=comment)
    await state.set_state(CreateOrder.choosing_payment)
    
    await message.answer(
        f"💳 <b>Выбери способ оплаты:</b>",
        reply_markup=payment_keyboard()
    )

@dp.callback_query(CreateOrder.choosing_payment, lambda c: c.data.startswith('payment_'))
async def create_order_payment(callback: CallbackQuery, state: FSMContext):
    payment = callback.data.replace('payment_', '')
    
    await state.update_data(payment_method=payment)
    await state.set_state(CreateOrder.confirm)
    
    data = await state.get_data()
    total = data['amount'] * data['price']
    
    if data['market_type'] == 'game':
        game = GAMES[data['item_id']]
        icon = game['icon']
        name = game['name']
        currency = game['currency']
    else:
        currency = CRYPTO_CURRENCIES[data['item_id']]
        icon = currency['icon']
        name = data['item_id']
        currency = data['item_id']
    
    text = (
        f"{icon} <b>Проверь данные:</b>\n\n"
        f"Тип: {'📈 Продажа' if data['order_type'] == 'sell' else '📉 Покупка'}\n"
        f"Товар: {name}\n"
        f"Количество: {data['amount']} {currency}\n"
        f"Цена: {data['price']} ₽\n"
        f"Сумма: {total} ₽\n"
        f"Оплата: {PAYMENT_METHODS[data['payment_method']]['name']}\n"
    )
    
    if data['comment']:
        text += f"Комментарий: {data['comment']}\n"
    
    text += f"\n✅ Всё верно?"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, создать", callback_data="confirm_order")
    builder.button(text="❌ Нет, заново", callback_data="restart")
    builder.adjust(2)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(CreateOrder.confirm, lambda c: c.data == "confirm_order")
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    order_id = db.create_order(
        user_id=callback.from_user.id,
        market_type=data['market_type'],
        item_id=data['item_id'],
        item_name=data['item_name'],
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
        f"Ты можешь найти его в списке ордеров.",
        reply_markup=back_keyboard()
    )
    await callback.answer()

# ============================================
# ПОКУПКА
# ============================================

@dp.callback_query(lambda c: c.data.startswith('buy_'))
async def buy_order(callback: CallbackQuery, state: FSMContext):
    order_id = int(callback.data.replace('buy_', ''))
    order = db.get_order(order_id)
    
    if not order or order['status'] != 'active':
        await callback.answer("❌ Ордер уже недоступен", show_alert=True)
        return
    
    await state.update_data(order_id=order_id)
    
    await callback.message.edit_text(
        f"💰 <b>Введи количество:</b>\n\n"
        f"Доступно: {order['amount']}\n"
        f"Цена: {order['price']} ₽",
        reply_markup=back_keyboard()
    )
    await callback.answer()

# ============================================
# ПРОФИЛЬ
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

@dp.callback_query(lambda c: c.data == "balance")
async def show_balance(callback: CallbackQuery):
    user = db.get_user(callback.from_user.id)
    await callback.message.edit_text(
        f"💰 <b>Твой баланс:</b>\n\n"
        f"{user['balance']} ₽",
        reply_markup=back_keyboard()
    )
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
