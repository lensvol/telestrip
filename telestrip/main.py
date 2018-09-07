# -*- config: utf-8 -*-
import asyncio
import itertools
import os
from datetime import datetime
from time import mktime
from typing import List, Iterator

import attr
import feedparser
import pendulum
from aiohttp import ClientSession
from aiotg import Bot
from bs4 import BeautifulSoup

RSS_DATE_FORMAT = "ddd, D MMM YYYY HH:mm:ss Z"


async def fetch(url):
    async with ClientSession() as session:
        async with session.get(url) as response:
            return response, await response.read()


@attr.s(auto_attribs=True)
class Update(object):
    title: str
    description: str
    timestamp: pendulum
    images: List[bytes]


class ComicStrip(object):

    TITLE = None
    INDEX_URL = None

    async def get_updates(self, moment: datetime) -> List[Update]:
        raise NotImplemented


class PennyArcade(ComicStrip):

    TITLE = "Penny Arcade"
    INDEX_URL = "http://penny-arcade.com/feed"

    async def get_updates(self, moment: datetime) -> List[Update]:
        result = []

        print(f"Requesting feed from {self.INDEX_URL}...")
        response, page = await fetch(self.INDEX_URL)
        rss = feedparser.parse(page)

        for entry in rss.entries:
            published_on = pendulum.from_timestamp(mktime(entry.published_parsed))

            if published_on < moment:
                print(f"[{self.TITLE}] Ignoring entry {entry.title}: too old")
                continue

            if not entry.title.startswith("Comic:"):
                print(f"[{self.TITLE}] Ignoring entry {entry.title}: not a comic")
                continue

            print(f"[{self.TITLE}] Fetching comic page for {entry.title}")
            response, comic_page = await fetch(entry.link)
            soup = BeautifulSoup(comic_page, "html.parser")
            comic_img = soup.find("div", {"id": "comicFrame"}).findChild("img")

            print(f'[{self.TITLE}] Fetching image from {comic_img.attrs["src"]}')
            response, image = await fetch(comic_img.attrs["src"])

            result.append(Update(entry.title, entry.summary, published_on, [image]))

        return result


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
    ], now.subtract(days=3)))

    loop.run_until_complete(send_updates_to_telegram(recipient_id, bot_token, updates))


if __name__ == "__main__":
    main()
