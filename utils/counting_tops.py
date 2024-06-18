import re
from typing import List, Tuple

from database.database import increment_user_field


async def counting_tops(members: List[Tuple], logs_list: List[str]) -> None:    
    for member, idp in members:
        for logs in logs_list:
            if re.search(rf'🕳 {member} 🛡', logs):
                await increment_user_field(idp, 'shields_used', 1)
                
                if re.search(rf'🕳 [а-яёa-z]+ 🔪 🛡🕳 {member}', logs, re.I):
                    await increment_user_field(idp, 'successful_shield_usage', 1)
            
            result = re.findall(rf'🕳 [а-яёa-z]+ 🔪 🛡🕳 {member}', logs, re.I)
            if result:
                await increment_user_field(idp, 'hits_blocked_by_shield', len(result))

            if re.search(rf'🕳 {member} 🦶 🕳', logs):
                await increment_user_field(idp, 'pings', 1)

            if re.search(rf'🕳 {member} 💫', logs):
                await increment_user_field(idp, 'misses', 1)

            if re.search(rf'🕳 {member} 🔪 🛡🕳 [а-яёa-z]+', logs, re.I):
                await increment_user_field(idp, 'blocked_hits', 1)

            result = re.search(rf'🕳 {member} 🔪 🛡?🕳 [а-яёa-z]+ \(-(?P<damage>\d+)❤️\)', logs, re.I)
            if result:
                await increment_user_field(idp, 'damage_dealt', result.group('damage'))
                await increment_user_field(idp, 'hits_dealt', 1)
            
            for name in re.findall('🕳 ([а-яёa-z]+) - ☠️', logs, re.I):
                result = re.findall(f'🕳 ([а-яёa-z]+) 🔪 🛡?🕳 {name} \(-\d+❤️\)', logs, re.I)[-1]
                if result and member == result:
                    await increment_user_field(idp, 'players_killed', 1)
