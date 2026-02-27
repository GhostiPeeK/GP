# Токен бота от @BotFather
BOT_TOKEN = "8339352233:AAGixj9izEbOVKHvhpKeTd_4_Y2CP-f-ZhE"  # ВСТАВЬ СВОЙ ТОКЕН!

# Твой Telegram ID (для админки)
ADMIN_ID = 2091630272  # ЗАМЕНИ НА СВОЙ ID!

# ============================================
# НАСТРОЙКИ ПЛАТЕЖЕЙ
# ============================================

# 1. Telegram Stars (уже работает)
STARS_ENABLED = True
STARS_TO_RUB = 1.79  # 1 звезда ≈ 1.79 руб (примерный курс)

# 2. CryptoBot (криптовалюта)
# Зарегистрируйся в @CryptoBot → My Apps → Create App
CRYPTO_ENABLED = True
CRYPTO_API_KEY = "ТВОЙ_API_KEY"  # ВСТАВЬ СВОЙ КЛЮЧ!
CRYPTO_API_SECRET = "ТВОЙ_API_SECRET"  # ВСТАВЬ СВОЙ СЕКРЕТ!
CRYPTO_CURRENCIES = ['USDT', 'TON', 'BTC']  # Доступные валюты

# 3. ЮKassa (банковские карты) - пока в разработке
CARDS_ENABLED = False
YOOKASSA_SHOP_ID = ""
YOOKASSA_SECRET_KEY = ""

# ============================================
# НАСТРОЙКИ БОТА
# ============================================

# Суммы в ЗВЕЗДАХ (Telegram Stars)
# Для крипты и карт будет автоматический пересчет
PAYMENT_AMOUNTS = [1, 3, 5, 10, 25, 50, 100, 250]

# Список игр
GAMES = {
    'pubg': 'PUBG Mobile (UC)',
    'brawl': 'Brawl Stars (гемы)',
    'steam': 'Steam Balance',
    'freefire': 'Free Fire (алмазы)',
    'genshin': 'Genshin Impact (кристаллы)',
    'cod': 'Call of Duty Mobile (CP)',
    'mlbb': 'Mobile Legends (алмазы)',
    'fortnite': 'Fortnite (V-bucks)'
}
