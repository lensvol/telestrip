# -*- config: utf-8 -*-
import asyncio
import itertools
import os
from typing import Iterator

from aiotg import Bot

from telestrip.comic_strips import *

RSS_DATE_FORMAT = "ddd, D MMM YYYY HH:mm:ss Z"


async def send_updates_to_telegram(sender_id: str, api_token: str, updates: List[Update]) -> None:
    bot = Bot(api_token)
    private = bot.private(sender_id)

    for update in sorted(updates, key=lambda u: u.timestamp):
        for strip in update.images:
            print(f'Sending {update.title}...')
            human_dt = update.timestamp.to_datetime_string()
            await private.send_photo(
                photo=strip,
                caption=f'{update.title} - {human_dt}'
            )


async def collect_strips(comic_strips: List[ComicStrip], moment: pendulum.DateTime) -> Iterator[Update]:
    tasks = [
        asyncio.ensure_future(comic_strip.get_updates(moment))
        for comic_strip in comic_strips
    ]

    updates = await asyncio.gather(*tasks)

    return itertools.chain.from_iterable(updates)
