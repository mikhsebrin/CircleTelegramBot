import requests


def get_bot_info(token: str, data_type: str):
    response = requests.get(f"https://api.telegram.org/bot{token}/getMe")
    
    if response.status_code == 200:
        data = response.json()
        
        return data["result"][data_type]
