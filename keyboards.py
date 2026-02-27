from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from config import GAMES, PAYMENT_AMOUNTS

def get_main_menu():
    """Главное меню (снизу)"""
    builder = ReplyKeyboardBuilder()
    
    buttons = [
        KeyboardButton(text="🎮 Игры"),
        KeyboardButton(text="⭐ Пополнить"),
        KeyboardButton(text="📊 Профиль"),
        KeyboardButton(text="❓ Помощь"),
        KeyboardButton(text="👥 Рефералы"),
        KeyboardButton(text="📞 Контакты")
    ]
    
    builder.add(*buttons)
    builder.adjust(2, 2, 2)
    
    return builder.as_markup(resize_keyboard=True, input_field_placeholder="Выбери действие...")

def get_games_inline():
    """Инлайн клавиатура с играми"""
    builder = InlineKeyboardBuilder()
    
    for game_id, game_name in GAMES.items():
        builder.button(text=game_name, callback_data=f"game_{game_id}")
    
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main"))
    
    return builder.as_markup()

def get_amounts_inline():
    """Инлайн клавиатура с суммами"""
    builder = InlineKeyboardBuilder()
    
    for amount in PAYMENT_AMOUNTS:
        builder.button(text=f"{amount} ⭐", callback_data=f"amount_{amount}")
    
    builder.adjust(3)
    builder.row(
        InlineKeyboardButton(text="🔙 К играм", callback_data="back_to_games"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main"),
        width=2
    )
    
    return builder.as_markup()

def get_profile_inline():
    """Инлайн клавиатура для профиля"""
    builder = InlineKeyboardBuilder()
    
    buttons = [
        InlineKeyboardButton(text="📊 История", callback_data="profile_history"),
        InlineKeyboardButton(text="⭐ Пополнить", callback_data="to_games"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")
    ]
    
    builder.add(*buttons)
    builder.adjust(2, 1)
    
    return builder.as_markup()

def get_admin_inline():
    """Инлайн клавиатура для админа"""
    builder = InlineKeyboardBuilder()
    
    buttons = [
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
        InlineKeyboardButton(text="💳 Платежи", callback_data="admin_payments"),
        InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")
    ]
    
    builder.add(*buttons)
    builder.adjust(2, 2)
    
    return builder.as_markup()

def get_back_to_main():
    """Кнопка возврата в главное меню"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 Главное меню", callback_data="back_to_main")
    return builder.as_markup()
