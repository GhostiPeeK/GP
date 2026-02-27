import aiohttp
import logging
import asyncio
from config import GAMES

class GameAPI:
    def __init__(self):
        self.apis = {}
        
    async def deliver_pubg(self, user_id, amount, account):
        """Пополнение PUBG Mobile"""
        try:
            # Здесь реальный API запрос к PUBG
            async with aiohttp.ClientSession() as session:
                # Пример запроса (замени на реальный)
                async with session.post(
                    "https://api.pubg.com/v1/deliver",
                    json={
                        "account": account,
                        "amount": amount,
                        "currency": "UC"
                    }
                ) as resp:
                    result = await resp.json()
                    if resp.status == 200:
                        logging.info(f"PUBG доставлено: {account}, {amount} UC")
                        return True
        except Exception as e:
            logging.error(f"PUBG API error: {e}")
        return False
    
    async def deliver_brawl(self, user_id, amount, account):
        """Пополнение Brawl Stars"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.brawlstars.com/v1/gems",
                    json={
                        "player_tag": account,
                        "gems": amount
                    }
                ) as resp:
                    if resp.status == 200:
                        logging.info(f"Brawl Stars доставлено: {account}, {amount} гемов")
                        return True
        except Exception as e:
            logging.error(f"Brawl Stars API error: {e}")
        return False
    
    async def deliver_steam(self, user_id, amount, account):
        """Пополнение Steam"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.steampowered.com/v1/wallet",
                    json={
                        "steam_id": account,
                        "amount": amount,
                        "currency": "RUB"
                    }
                ) as resp:
                    if resp.status == 200:
                        logging.info(f"Steam доставлено: {account}, {amount} руб")
                        return True
        except Exception as e:
            logging.error(f"Steam API error: {e}")
        return False
    
    async def deliver_freefire(self, user_id, amount, account):
        """Пополнение Free Fire"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.freefire.com/v1/diamonds",
                    json={
                        "uid": account,
                        "diamonds": amount
                    }
                ) as resp:
                    if resp.status == 200:
                        logging.info(f"Free Fire доставлено: {account}, {amount} алмазов")
                        return True
        except Exception as e:
            logging.error(f"Free Fire API error: {e}")
        return False
    
    async def deliver(self, game_id, user_id, amount, account):
        """Универсальный метод доставки"""
        methods = {
            'pubg': self.deliver_pubg,
            'brawl': self.deliver_brawl,
            'steam': self.deliver_steam,
            'freefire': self.deliver_freefire
        }
        
        method = methods.get(game_id)
        if method:
            return await method(user_id, amount, account)
        return False

# Создаем глобальный экземпляр
game_api = GameAPI()
