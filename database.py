import sqlite3
import logging
from datetime import datetime, timedelta

class Database:
    def __init__(self, db_name="bot_database.db"):
        self.db_name = db_name
        self.init_db()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Таблица пользователей (с рефералами)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                registered_at TIMESTAMP,
                referrer_id INTEGER DEFAULT NULL,
                referral_code TEXT UNIQUE,
                referral_bonus INTEGER DEFAULT 0,
                total_spent_stars INTEGER DEFAULT 0,
                total_payments INTEGER DEFAULT 0,
                last_activity TIMESTAMP,
                FOREIGN KEY (referrer_id) REFERENCES users(user_id)
            )
        ''')
        
        # Таблица платежей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                game_id TEXT,
                game_name TEXT,
                amount_stars INTEGER,
                amount_real REAL,
                currency TEXT,
                payment_method TEXT,
                telegram_payment_charge_id TEXT UNIQUE,
                status TEXT DEFAULT 'completed',
                created_at TIMESTAMP,
                delivered_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Таблица реферальных выплат
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referral_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER,
                referral_id INTEGER,
                payment_id INTEGER,
                amount_stars INTEGER,
                bonus_stars INTEGER,
                created_at TIMESTAMP,
                FOREIGN KEY (referrer_id) REFERENCES users(user_id),
                FOREIGN KEY (referral_id) REFERENCES users(user_id),
                FOREIGN KEY (payment_id) REFERENCES payments(id)
            )
        ''')
        
        # Таблица статистики по играм
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS games_stats (
                game_id TEXT PRIMARY KEY,
                game_name TEXT,
                total_payments INTEGER DEFAULT 0,
                total_stars INTEGER DEFAULT 0,
                total_users INTEGER DEFAULT 0,
                last_payment TIMESTAMP
            )
        ''')
        
        # Таблица для ожидающих выплат
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pending_deliveries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_id INTEGER,
                user_id INTEGER,
                game_id TEXT,
                amount INTEGER,
                game_account TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP,
                delivered_at TIMESTAMP,
                attempts INTEGER DEFAULT 0,
                last_attempt TIMESTAMP,
                FOREIGN KEY (payment_id) REFERENCES payments(id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logging.info("База данных инициализирована")
    
    def add_user(self, user_id, username, first_name, last_name, referrer_code=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Генерируем уникальный реферальный код
        import random
        import string
        referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        # Ищем реферера по коду
        referrer_id = None
        if referrer_code:
            cursor.execute('SELECT user_id FROM users WHERE referral_code = ?', (referrer_code,))
            result = cursor.fetchone()
            if result:
                referrer_id = result['user_id']
        
        cursor.execute('''
            INSERT OR REPLACE INTO users 
            (user_id, username, first_name, last_name, registered_at, referrer_id, referral_code, last_activity)
            VALUES (?, ?, ?, ?, COALESCE(
                (SELECT registered_at FROM users WHERE user_id = ?),
                ?
            ), COALESCE(
                (SELECT referrer_id FROM users WHERE user_id = ?),
                ?
            ), COALESCE(
                (SELECT referral_code FROM users WHERE user_id = ?),
                ?
            ), ?)
        ''', (
            user_id, username, first_name, last_name,
            user_id, datetime.now(),
            user_id, referrer_id,
            user_id, referral_code,
            datetime.now()
        ))
        
        conn.commit()
        conn.close()
        return referral_code
    
    def add_payment(self, user_id, game_id, game_name, amount_stars, amount_real, currency, payment_method, charge_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Добавляем платеж
        cursor.execute('''
            INSERT INTO payments 
            (user_id, game_id, game_name, amount_stars, amount_real, currency, payment_method, telegram_payment_charge_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, game_id, game_name, amount_stars, amount_real, currency, payment_method, charge_id, datetime.now()))
        
        payment_id = cursor.lastrowid
        
        # Обновляем статистику пользователя
        cursor.execute('''
            UPDATE users 
            SET total_spent_stars = total_spent_stars + ?,
                total_payments = total_payments + 1,
                last_activity = ?
            WHERE user_id = ?
        ''', (amount_stars, datetime.now(), user_id))
        
        # Обновляем статистику игры
        cursor.execute('''
            INSERT INTO games_stats (game_id, game_name, total_payments, total_stars, total_users, last_payment)
            VALUES (?, ?, 1, ?, 1, ?)
            ON CONFLICT(game_id) DO UPDATE SET
                total_payments = total_payments + 1,
                total_stars = total_stars + excluded.total_stars,
                total_users = total_users + 1,
                last_payment = excluded.last_payment
        ''', (game_id, game_name, amount_stars, datetime.now()))
        
        # Добавляем в очередь на выдачу
        cursor.execute('''
            INSERT INTO pending_deliveries (payment_id, user_id, game_id, amount, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (payment_id, user_id, game_id, amount_stars, datetime.now()))
        
        conn.commit()
        conn.close()
        logging.info(f"Платеж сохранен: User={user_id}, Game={game_id}, Stars={amount_stars}")
        return payment_id
    
    def process_referral_bonus(self, payment_id, referrer_id, referral_id, amount_stars, bonus_percent):
        """Начисляет бонус рефереру"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        bonus_stars = int(amount_stars * bonus_percent / 100)
        
        cursor.execute('''
            INSERT INTO referral_payments (referrer_id, referral_id, payment_id, amount_stars, bonus_stars, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (referrer_id, referral_id, payment_id, amount_stars, bonus_stars, datetime.now()))
        
        # Начисляем бонус рефереру
        cursor.execute('''
            UPDATE users 
            SET referral_bonus = referral_bonus + ?,
                total_spent_stars = total_spent_stars + ?
            WHERE user_id = ?
        ''', (bonus_stars, bonus_stars, referrer_id))
        
        conn.commit()
        conn.close()
        return bonus_stars
    
    def get_pending_deliveries(self, limit=10):
        """Получает задачи на выдачу"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM pending_deliveries 
            WHERE status = 'pending'
            ORDER BY created_at ASC
            LIMIT ?
        ''', (limit,))
        
        result = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return result
    
    def mark_delivered(self, delivery_id):
        """Отмечает задачу как выполненную"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE pending_deliveries 
            SET status = 'delivered', delivered_at = ?
            WHERE id = ?
        ''', (datetime.now(), delivery_id))
        
        cursor.execute('''
            UPDATE payments 
            SET delivered_at = ?
            WHERE id = (SELECT payment_id FROM pending_deliveries WHERE id = ?)
        ''', (datetime.now(), delivery_id))
        
        conn.commit()
        conn.close()
    
    def get_user_stats(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.*, 
                   (SELECT COUNT(*) FROM users WHERE referrer_id = u.user_id) as referrals_count,
                   (SELECT SUM(bonus_stars) FROM referral_payments WHERE referrer_id = u.user_id) as total_bonus
            FROM users u
            WHERE u.user_id = ?
        ''', (user_id,))
        
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None
    
    def get_referrals(self, user_id):
        """Получает список рефералов"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, username, first_name, registered_at, total_spent_stars 
            FROM users 
            WHERE referrer_id = ?
            ORDER BY registered_at DESC
        ''', (user_id,))
        
        result = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return result
    
    def get_game_stats(self, game_id=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if game_id:
            cursor.execute('SELECT * FROM games_stats WHERE game_id = ?', (game_id,))
            result = cursor.fetchone()
            result = dict(result) if result else None
        else:
            cursor.execute('SELECT * FROM games_stats ORDER BY total_stars DESC')
            result = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return result
    
    def get_recent_payments(self, limit=10):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.*, u.username, u.first_name 
            FROM payments p
            LEFT JOIN users u ON p.user_id = u.user_id
            ORDER BY p.created_at DESC 
            LIMIT ?
        ''', (limit,))
        
        result = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return result
    
    def get_daily_stats(self, days=7):
        """Статистика за последние дни"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        result = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            
            cursor.execute('''
                SELECT COUNT(*) as payments, SUM(amount_stars) as stars
                FROM payments 
                WHERE DATE(created_at) = ?
            ''', (date,))
            
            day_stats = cursor.fetchone()
            result.append({
                'date': date,
                'payments': day_stats['payments'] or 0,
                'stars': day_stats['stars'] or 0
            })
        
        conn.close()
        return result

db = Database()
