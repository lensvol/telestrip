# -*- config: utf-8 -*-
import asyncio
import os

from telestrip.comic_strips import *
from telestrip.helpers import collect_strips, send_updates_to_telegram

RSS_DATE_FORMAT = "ddd, D MMM YYYY HH:mm:ss Z"

def main():
    bot_token = os.environ.get('BOT_TOKEN')
    recipient_id = os.environ.get('RECIPIENT_ID')
    if not bot_token:
        print('No Telegram bot API token in BOT_TOKEN variable!')
        exit(-1)

    if not recipient_id:
        print('No recipient specified in RECIPIENT_ID variable!')
        exit(-1)

    now = pendulum.now()
    loop = asyncio.get_event_loop()
    updates = loop.run_until_complete(collect_strips([
        PennyArcade(),
        PvP(),
        SaturdayMorningBreakfastCereal(),
        XKCD(),
    ], now.subtract(days=3)))

    loop.run_until_complete(send_updates_to_telegram(recipient_id, bot_token, updates))


if __name__ == "__main__":
    main()
