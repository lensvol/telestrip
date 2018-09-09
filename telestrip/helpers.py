# -*- config: utf-8 -*-
import asyncio
import base64
from colorama import Fore, Back, Style, init as init_colorama
import itertools
from typing import Iterator, List

import pendulum
from aiotg import Bot

from telestrip.comic_strips import ComicStrip, Update

RSS_DATE_FORMAT = "ddd, D MMM YYYY HH:mm:ss Z"
MAGIC_IMAGE_LINE = '\033]1337;File=inline=1;width=auto;height=auto;preserveAspectRatio=1:{encoded_image}\a'


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


def print_updates_to_console(updates: List[Update]) -> None:
    init_colorama()
    for update in updates:
        print(f'{Style.BRIGHT}[{update.title}]\n{update.description}\n')
        for image in update.images:
            print(MAGIC_IMAGE_LINE.format(encoded_image=base64.b64encode(image).decode('ascii')))
            print()