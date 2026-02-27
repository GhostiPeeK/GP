# Токен бота от @BotFather
BOT_TOKEN = "8339352233:AAGixj9izEbOVKHvhpKeTd_4_Y2CP-f-ZhE"

# Твой Telegram ID (для админки)
ADMIN_ID = 2091630272  # ЗАМЕНИ НА СВОЙ ID!

# ============================================
# НАСТРОЙКИ ПЛАТЕЖЕЙ
# ============================================

STARS_ENABLED = True
STARS_TO_RUB = 1.79

CRYPTO_ENABLED = True
CRYPTO_API_KEY = "540261:AAzd4sQW2mo4I8UdxardSygAc3H3CSZbZBs"  # Из @CryptoBot
CRYPTO_API_SECRET = ""
CRYPTO_CURRENCIES = ['USDT', 'TON', 'BTC']

CARDS_ENABLED = False  # Пока не надо

# ============================================
# НАСТРОЙКИ РЕФЕРАЛЬНОЙ СИСТЕМЫ
# ============================================

REFERRAL_BONUS = 10  # % от покупки реферала
REFERRAL_BONUS_STARS = 5  # Бонус за регистрацию по ссылке (в звездах)

# ============================================
# API ИГР (реальные ключи)
# ============================================

# PUBG Mobile (UC)
PUBG_API_KEY = "ТВОЙ_PUBG_API_KEY"
PUBG_API_URL = "https://api.pubg.com/v1/"

# Brawl Stars (гемы)
BRAWL_API_KEY = "ТВОЙ_BRAWL_API_KEY"
BRAWL_API_URL = "https://api.brawlstars.com/v1/"

# Steam
STEAM_API_KEY = "ТВОЙ_STEAM_API_KEY"
STEAM_API_URL = "https://api.steampowered.com/"

# Free Fire
FREE_FIRE_API_KEY = "ТВОЙ_FREE_FIRE_API_KEY"
FREE_FIRE_API_URL = "https://api.freefire.com/v1/"

# ============================================
# НАСТРОЙКИ ИГР
# ============================================

# Суммы в ЗВЕЗДАХ
PAYMENT_AMOUNTS = [1, 3, 5, 10, 25, 50, 100, 250]

# Список игр с расширенными данными
GAMES = {
    'pubg': {
        'name': 'PUBG Mobile (UC)',
        'api_key': PUBG_API_KEY,
        'api_url': PUBG_API_URL,
        'currency': 'UC',
        'min_amount': 1,
        'max_amount': 10000,
        'enabled': True
    },
    'brawl': {
        'name': 'Brawl Stars (гемы)',
        'api_key': BRAWL_API_KEY,
        'api_url': BRAWL_API_URL,
        'currency': 'гемы',
        'min_amount': 1,
        'max_amount': 5000,
        'enabled': True
    },
    'steam': {
        'name': 'Steam Balance',
        'api_key': STEAM_API_KEY,
        'api_url': STEAM_API_URL,
        'currency': 'руб',
        'min_amount': 10,
        'max_amount': 5000,
        'enabled': True
    },
    'freefire': {
        'name': 'Free Fire (алмазы)',
        'api_key': FREE_FIRE_API_KEY,
        'api_url': FREE_FIRE_API_URL,
        'currency': 'алмазы',
        'min_amount': 1,
        'max_amount': 10000,
        'enabled': True
    },
    'genshin': {
        'name': 'Genshin Impact (кристаллы)',
        'api_key': '',
        'api_url': '',
        'currency': 'кристаллы',
        'min_amount': 1,
        'max_amount': 5000,
        'enabled': False  # Пока нет API
    },
    'cod': {
        'name': 'Call of Duty Mobile (CP)',
        'api_key': '',
        'api_url': '',
        'currency': 'CP',
        'min_amount': 1,
        'max_amount': 5000,
        'enabled': False
    }
}
