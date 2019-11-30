# -*- config: utf-8 -*-
import asyncio
import base64
import operator
from functools import reduce
from typing import Iterator, List, Dict

import pendulum
from aiohttp import ClientSession
from aiotg import Bot
from colorama import Fore, Style, init as init_colorama

RSS_DATE_FORMAT = "ddd, D MMM YYYY HH:mm:ss Z"
MAGIC_IMAGE_LINE = "\033]1337;File=inline=1;width=auto;height=auto;preserveAspectRatio=1:{encoded_image}\a"


async def fetch(url):
    async with ClientSession() as session:
        async with session.get(url) as response:
            return response, await response.read()


async def send_updates_to_telegram(
    sender_id: str, api_token: str, updates: List["Update"]
) -> None:
    bot = Bot(api_token)
    private = bot.private(sender_id)

    for update in sorted(updates, key=lambda u: u.timestamp):
        for strip in update.images:
            print(f"Sending {update.title}...")
            human_dt = update.timestamp.to_datetime_string()
            await private.send_photo(
                photo=strip,
                caption=f"*{update.title}*\n({human_dt})",
                parse_mode="Markdown",
            )

        if update.description:
            print(f"Sending description for {update.title} as separate post...")
            await private.send_text(
                f"*{update.title}*\n\n{update.description}", parse_mode="Markdown"
            )

    await bot.session.close()


async def collect_strips(
    comic_strips: List["ComicStrip"], timestamps: Dict[str, int]
) -> Iterator["Update"]:
    tasks = [
        asyncio.ensure_future(
            strip.get_updates(timestamps.get(strip.ID, pendulum.from_timestamp(1)))
        )
        for strip in comic_strips
    ]

    updates = await asyncio.gather(*tasks)
    return reduce(operator.concat, updates)


def print_updates_to_console(updates: List["Update"]) -> None:
    init_colorama()
    for update in updates:
        print(f"{Style.BRIGHT}[{update.title}]{Style.RESET_ALL}\n")
        for image in update.images:
            print(
                MAGIC_IMAGE_LINE.format(
                    encoded_image=base64.b64encode(image).decode("ascii")
                )
            )
            print()
            if update.description:
                print(f"{Fore.LIGHTGREEN_EX}{update.description}{Style.RESET_ALL}\n")
