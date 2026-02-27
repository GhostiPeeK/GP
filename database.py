import sqlite3
import logging
from datetime import datetime

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
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                registered_at TIMESTAMP,
                total_spent_stars INTEGER DEFAULT 0,
                total_payments INTEGER DEFAULT 0
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
                telegram_payment_charge_id TEXT UNIQUE,
                status TEXT DEFAULT 'completed',
                created_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Таблица статистики по играм
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS games_stats (
                game_id TEXT PRIMARY KEY,
                game_name TEXT,
                total_payments INTEGER DEFAULT 0,
                total_stars INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
        logging.info("База данных инициализирована")
    
    def add_user(self, user_id, username, first_name, last_name):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO users 
            (user_id, username, first_name, last_name, registered_at, total_spent_stars, total_payments)
            VALUES (?, ?, ?, ?, COALESCE(
                (SELECT registered_at FROM users WHERE user_id = ?),
                ?
            ), COALESCE(
                (SELECT total_spent_stars FROM users WHERE user_id = ?),
                0
            ), COALESCE(
                (SELECT total_payments FROM users WHERE user_id = ?),
                0
            ))
        ''', (
            user_id, username, first_name, last_name,
            user_id, datetime.now(),
            user_id,
            user_id
        ))
        
        conn.commit()
        conn.close()
    
    def add_payment(self, user_id, game_id, game_name, amount_stars, charge_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Добавляем платеж
        cursor.execute('''
            INSERT INTO payments (user_id, game_id, game_name, amount_stars, telegram_payment_charge_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, game_id, game_name, amount_stars, charge_id, datetime.now()))
        
        # Обновляем статистику пользователя
        cursor.execute('''
            UPDATE users 
            SET total_spent_stars = total_spent_stars + ?,
                total_payments = total_payments + 1
            WHERE user_id = ?
        ''', (amount_stars, user_id))
        
        # Обновляем статистику игры
        cursor.execute('''
            INSERT INTO games_stats (game_id, game_name, total_payments, total_stars)
            VALUES (?, ?, 1, ?)
            ON CONFLICT(game_id) DO UPDATE SET
                total_payments = total_payments + 1,
                total_stars = total_stars + excluded.total_stars
        ''', (game_id, game_name, amount_stars))
        
        conn.commit()
        conn.close()
        logging.info(f"Платеж сохранен: User={user_id}, Game={game_id}, Stars={amount_stars}")
    
    def get_user_stats(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM users WHERE user_id = ?
        ''', (user_id,))
        
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None
    
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
            SELECT * FROM payments 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (limit,))
        
        result = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return result

# Создаем глобальный экземпляр БД
db = Database()
