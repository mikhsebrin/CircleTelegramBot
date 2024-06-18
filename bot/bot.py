from pyrogram import Client

from configs.configs import BOT_TOKEN, API_ID, API_HASH 

bot = Client(
    "bot_session", 
    api_id=API_ID, 
    api_hash=API_HASH, 
    bot_token=BOT_TOKEN
)
app = Client(
    "client_session", 
    api_id=API_ID, 
    api_hash=API_HASH
)
