from utils.get_bot_info import get_bot_info

BOT_TOKEN: str = None

# Test bot
# BOT_TOKEN: str = None

API_ID: int = None
API_HASH: str = None

CHANNEL_EVENTS_ID: int = -1001229378797
CHAT_CIRCLE_ID: int = -1001423896138

ADMINS_ID: list = []

__version__: str = '2.6.0'
__bot_username__: str = get_bot_info(token=BOT_TOKEN, data_type="username")
