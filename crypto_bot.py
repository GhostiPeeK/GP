import aiohttp
import logging
import uuid
from datetime import datetime

class CryptoBot:
    def __init__(self, api_key, api_secret=None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://pay.crypt.bot/api"
        self.pending_payments = {}  # Временное хранилище
        
    async def create_invoice(self, amount, currency, description, user_id, game_id):
        """Создает счет в криптовалюте"""
        url = f"{self.base_url}/createInvoice"
        
        headers = {
            "Crypto-Pay-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        # Генерируем уникальный ID
        invoice_id = str(uuid.uuid4())[:8]
        
        data = {
            "asset": currency,  # USDT, TON, BTC
            "amount": str(amount),
            "description": description,
            "paid_btn_name": "openBot",
            "paid_btn_url": "https://t.me/GhostiPeeKPaY_bot",  # Твой бот
            "expires_in": 3600  # 1 час
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as resp:
                    result = await resp.json()
                    
                    if result.get("ok"):
                        invoice = result["result"]
                        
                        # Сохраняем в память
                        self.pending_payments[invoice["invoice_id"]] = {
                            "user_id": user_id,
                            "game_id": game_id,
                            "amount_crypto": float(amount),
                            "currency": currency,
                            "stars_amount": amount * 10,  # Примерная конвертация
                            "created_at": datetime.now(),
                            "status": "pending"
                        }
                        
                        return invoice
                    else:
                        logging.error(f"CryptoBot error: {result}")
                        return None
        except Exception as e:
            logging.error(f"CryptoBot exception: {e}")
            return None
    
    async def check_payment(self, invoice_id):
        """Проверяет статус оплаты"""
        url = f"{self.base_url}/getInvoices"
        
        headers = {
            "Crypto-Pay-API-Key": self.api_key
        }
        
        params = {
            "invoice_ids": invoice_id
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as resp:
                    result = await resp.json()
                    
                    if result.get("ok") and result["result"]["items"]:
                        invoice = result["result"]["items"][0]
                        return invoice
        except Exception as e:
            logging.error(f"Check payment error: {e}")
        
        return None
    
    async def wait_for_payment(self, invoice_id, timeout=300):
        """Ждет оплаты (простейшая реализация)"""
        import asyncio
        
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            invoice = await self.check_payment(invoice_id)
            
            if invoice and invoice.get("status") == "paid":
                return invoice
            
            await asyncio.sleep(3)  # Проверяем каждые 3 секунды
        
        return None

# Создаем глобальный экземпляр (будет инициализирован в main)
crypto_bot = None
