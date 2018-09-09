from time import mktime
from typing import List, Union

import attr
import feedparser
import pendulum
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from pendulum import DateTime


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
    ID = None
    TITLE = None
    INDEX_URL = None

    async def get_updates(self, moment: DateTime) -> List[Update]:
        result = []

        print(f"Requesting feed from {self.INDEX_URL}...")
        response, page = await fetch(self.INDEX_URL)
        rss = feedparser.parse(page)

        for entry in rss.entries:
            if 'published_parsed' in entry:
                parsed_timestamp = entry.published_parsed
            else:
                parsed_timestamp = entry.updated_parsed
            published_on = pendulum.from_timestamp(mktime(parsed_timestamp))

            if published_on < moment:
                print(f"[{self.TITLE}] Ignoring entry {entry.title}: too old")
                continue

            update = await self.process_entry(entry, published_on)
            if update is not None:
                result.append(update)

        return result

    async def process_entry(self, entry, published_on: DateTime) -> Union[Update, None]:
        raise NotImplemented


class PennyArcade(ComicStrip):
    ID = 'penny-arcade'
    TITLE = "Penny Arcade"
    INDEX_URL = "http://penny-arcade.com/feed"

    async def process_entry(self, entry, published_on: DateTime) -> Union[Update, None]:
        if not entry.title.startswith("Comic:"):
            print(f"[{self.TITLE}] Ignoring entry {entry.title}: not a comic")
            return None

        print(f"[{self.TITLE}] Fetching comic page for {entry.title}")
        response, comic_page = await fetch(entry.link)
        soup = BeautifulSoup(comic_page, "html.parser")
        comic_img = soup.find("div", {"id": "comicFrame"}).findChild("img")

        print(f'[{self.TITLE}] Fetching image from {comic_img.attrs["src"]}')
        response, image = await fetch(comic_img.attrs["src"])

        return Update(entry.title, entry.summary, published_on, [image])


class PvP(ComicStrip):
    ID = 'pvp'
    TITLE = "PvP"
    INDEX_URL = "http://pvponline.com/feed"

    async def process_entry(self, entry, published_on: DateTime) -> Union[Update, None]:
        if not entry.title.startswith("Comic:"):
            print(f"[{self.TITLE}] Ignoring entry {entry.title}: not a comic")
            return None

        print(f"[{self.TITLE}] Fetching comic page for {entry.title}")
        response, comic_page = await fetch(entry.link)
        soup = BeautifulSoup(comic_page, "html.parser")
        comic_img = soup.find("section", {"class": "comic-art"}).findChild("img")

        print(f'[{self.TITLE}] Fetching image from {comic_img.attrs["src"]}')
        response, image = await fetch(comic_img.attrs["src"])

        return Update(entry.title, entry.summary, published_on, [image])


class SaturdayMorningBreakfastCereal(ComicStrip):
    ID = 'smbc'
    TITLE = "Saturday Morning Breakfast Cereal"
    INDEX_URL = "https://www.smbc-comics.com/comic/rss"

    async def process_entry(self, entry, published_on: DateTime) -> Union[Update, None]:
        print(f"[{self.TITLE}] Fetching comic page for {entry.title}")
        soup = BeautifulSoup(entry.description, "html.parser")
        comic_img = soup.find("img")

        print(f'[{self.TITLE}] Fetching image from {comic_img.attrs["src"]}')
        response, image = await fetch(comic_img.attrs["src"])

        return Update(entry.title, entry.summary, published_on, [image])


class XKCD(ComicStrip):

    TITLE = "XKCD"
    INDEX_URL = "https://xkcd.com/rss.xml"

    async def process_entry(self, entry, published_on: DateTime) -> Union[Update, None]:
        print(f"[{self.TITLE}] Fetching comic page for {entry.title}")
        soup = BeautifulSoup(entry.description, "html.parser")
        comic_img = soup.find("img")

        print(f'[{self.TITLE}] Fetching image from {comic_img.attrs["src"]}')
        response, image = await fetch(comic_img.attrs["src"])
        return Update(entry.title, comic_img.attrs['alt'], published_on, [image])


class CommitStrip(ComicStrip):
    ID = 'commit-strip'
    TITLE = "Commit Strip"
    INDEX_URL = 'https://www.commitstrip.com/en/feed/'

    async def process_entry(self, entry, published_on: DateTime) -> Union[Update, None]:
        print(f"[{self.TITLE}] Fetching comic page for {entry.title}")
        soup = BeautifulSoup(entry.content[0].value, "html.parser")
        comic_imgs = soup.findAll("img")

        if not comic_imgs:
            return None

        print(f'[{self.TITLE}] Fetching image from {comic_imgs[0].attrs["src"]}')
        response, image = await fetch(comic_imgs[0].attrs["src"])
        return Update(entry.title, '', published_on, [image])


class SlackWyrm(ComicStrip):
    ID = 'slack-wyrm'
    TITLE = 'Slack Wyrm'
    INDEX_URL = 'http://www.joshuawright.net/rss_joshuawright.xml'

    async def process_entry(self, entry, published_on: DateTime) -> Union[Update, None]:
        print(f"[{self.TITLE}] Fetching comic page for {entry.title}")
        response, comic_page = await fetch(entry.link)
        soup = BeautifulSoup(comic_page, "html.parser")
        comic_frames = soup.findAll("div", {"data-muse-type": "img_frame"})

        images = []
        for frame in comic_frames:
            comic_img = frame.findChild('img')
            print(f'[{self.TITLE}] Fetching image from {comic_img.attrs["src"]}')
            response, image = await fetch('http://www.joshuawright.net/' + comic_img.attrs["src"])
            images.append(image)

        return Update(entry.title, entry.summary, published_on, images)


__all__ = [
    'CommitStrip',
    'PvP',
    'PennyArcade',
    'SaturdayMorningBreakfastCereal',
    'XKCD',
    'ComicStrip',
    'Update',
    'SlackWyrm',
]
