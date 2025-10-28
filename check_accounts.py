#!/usr/bin/env python3
import asyncio
from twscrape import API

async def check_accounts():
    api = API()
    accounts = await api.pool.accounts_info()
    print('Статус акаунтів:')
    for acc in accounts:
        status = 'Активний' if acc['active'] else 'Неактивний'
        error = acc.get('error_msg', 'OK')
        username = acc['username']
        print(f'  {username}: {status} - {error}')

if __name__ == "__main__":
    asyncio.run(check_accounts())