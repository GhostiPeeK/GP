from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from config import GAMES, PAYMENT_AMOUNTS, STARS_ENABLED, CRYPTO_ENABLED, CARDS_ENABLED

def get_main_menu():
    """Главное меню"""
    builder = ReplyKeyboardBuilder()
    
    buttons = [
        KeyboardButton(text="🎮 Игры"),
        KeyboardButton(text="⭐ Пополнить"),
        KeyboardButton(text="📊 Профиль"),
        KeyboardButton(text="👥 Рефералы"),
        KeyboardButton(text="❓ Помощь"),
        KeyboardButton(text="📞 Контакты")
    ]
    
    builder.add(*buttons)
    builder.adjust(2, 2, 2)
    
    return builder.as_markup(resize_keyboard=True)

def get_games_inline():
    """Клавиатура с играми"""
    builder = InlineKeyboardBuilder()
    
    for game_id, game_data in GAMES.items():
        if game_data.get('enabled', True):
            builder.button(text=game_data['name'], callback_data=f"game_{game_id}")
    
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main"))
    
    return builder.as_markup()

def get_amounts_inline(game_id):
    """Клавиатура с суммами"""
    builder = InlineKeyboardBuilder()
    
    for amount in PAYMENT_AMOUNTS:
        builder.button(text=f"{amount} ⭐", callback_data=f"amount_{game_id}_{amount}")
    
    builder.adjust(3)
    builder.row(
        InlineKeyboardButton(text="🔙 К играм", callback_data="back_to_games"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main"),
        width=2
    )
    
    return builder.as_markup()

def get_payment_methods_inline(game_id, amount):
    """Клавиатура с выбором оплаты"""
    builder = InlineKeyboardBuilder()
    
    if STARS_ENABLED:
        builder.button(text="⭐ Telegram Stars", callback_data=f"pay_stars_{game_id}_{amount}")
    
    if CRYPTO_ENABLED:
        builder.button(text="₿ Криптовалюта", callback_data=f"pay_crypto_{game_id}_{amount}")
    
    if CARDS_ENABLED:
        builder.button(text="💳 Банковская карта", callback_data=f"pay_card_{game_id}_{amount}")
    
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data=f"back_to_amounts_{game_id}"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main"),
        width=2
    )
    
    return builder.as_markup()

def get_crypto_currencies_inline(game_id, amount):
    """Выбор криптовалюты"""
    from config import CRYPTO_CURRENCIES
    
    builder = InlineKeyboardBuilder()
    
    for currency in CRYPTO_CURRENCIES:
        builder.button(text=currency, callback_data=f"crypto_{currency}_{game_id}_{amount}")
    
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data=f"back_to_payment_{game_id}_{amount}"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main"),
        width=2
    )
    
    return builder.as_markup()

def get_referral_inline(referral_code):
    """Клавиатура для рефералов"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📤 Поделиться ссылкой", switch_inline_query=f"Присоединяйся! {referral_code}")
    builder.button(text="👥 Мои рефералы", callback_data="my_referrals")
    builder.button(text="🏠 Главное меню", callback_data="back_to_main")
    
    builder.adjust(2, 1)
    
    return builder.as_markup()

def get_profile_inline():
    """Клавиатура профиля"""
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
    """Админ-клавиатура"""
    builder = InlineKeyboardBuilder()
    
    buttons = [
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
        InlineKeyboardButton(text="💳 Платежи", callback_data="admin_payments"),
        InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users"),
        InlineKeyboardButton(text="📊 Графики", callback_data="admin_charts"),
        InlineKeyboardButton(text="⚙️ Настройки", callback_data="admin_settings"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")
    ]
    
    builder.add(*buttons)
    builder.adjust(2, 2, 2)
    
    return builder.as_markup()

def get_back_to_main():
    """Кнопка возврата"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 Главное меню", callback_data="back_to_main")
    return builder.as_markup()
