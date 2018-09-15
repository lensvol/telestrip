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
    description: Union[str, None]
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

    def to_telegram_markdown(self, soup):
        result = ''
        for p in soup.findAll('p'):
            for child in list(p.children)[0:-1]:
                if child.name is None:
                    result += str(child)
                    result += '\n\n'
                elif child.name == 'a':
                    result = result.strip()
                    result += ' [{0}]({1})'.format(child.text, child.attrs['href'])
                elif child.name == 'i':
                    result += '*{0}*'.format(str(child.text))

        return result.replace('\0xa', '').strip()

    async def process_entry(self, entry, published_on: DateTime) -> Union[Update, None]:
        if not entry.title.startswith("Comic:"):
            print(f"[{self.TITLE}] Ignoring entry {entry.title}: not a comic")
            return None

        print(f"[{self.TITLE}] Fetching comic page for {entry.title}")
        response, comic_page = await fetch(entry.link)
        soup = BeautifulSoup(comic_page, "html.parser")
        comic_img = soup.find("div", {"id": "comicFrame"}).findChild("img")

        description = None

        post_link = soup.find('a', {'title': 'Read News Post'})
        if post_link:
            print(f"[{self.TITLE}] Fetching post page for {entry.title}...")
            response, post_page = await fetch(post_link.attrs['href'])
            soup = BeautifulSoup(post_page, 'html.parser')
            copy_text = soup.find('div', {'class': 'copy'})
            if copy_text:
                description = self.to_telegram_markdown(copy_text)

        print(f'[{self.TITLE}] Fetching image from {comic_img.attrs["src"]}')
        response, image = await fetch(comic_img.attrs["src"])

        return Update(entry.title, description, published_on, [image])


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

        return Update(entry.title, None, published_on, [image])


class SaturdayMorningBreakfastCereal(ComicStrip):
    ID = 'smbc'
    TITLE = "Saturday Morning Breakfast Cereal"
    INDEX_URL = "https://www.smbc-comics.com/comic/rss"

    async def process_entry(self, entry, published_on: DateTime) -> Union[Update, None]:
        print(f"[{self.TITLE}] Fetching comic page for {entry.title}")
        soup = BeautifulSoup(entry.description, "html.parser")
        comic_img = soup.find("img")

        description = ''

        p_hovertext = soup.find('p')
        if p_hovertext:
            description = p_hovertext.findNext('br').next

        print(f'[{self.TITLE}] Fetching image from {comic_img.attrs["src"]}')
        response, image = await fetch(comic_img.attrs["src"])

        return Update(entry.title, description, published_on, [image])


class XKCD(ComicStrip):
    ID = 'xkcd'
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


class Kill6BillionDemons(ComicStrip):
    ID = 'kill-6-billion-demons'
    TITLE = 'Kill 6 Billion Demons'
    INDEX_URL = 'https://killsixbilliondemons.com/feed/'

    def to_telegram_markdown(self, soup):
        result = ''
        for p in soup.findAll('p'):
            for child in p.children:
                if child.name is None:
                    result += str(child)
                    result += '\n\n'
                elif child.name == 'a':
                    result = result.strip()
                    result += ' [{0}]({1})'.format(child.text, child.attrs['href'])
                elif child.name == 'i':
                    result += '*{0}*'.format(str(child.text))

        return result.replace('\0xa', '').strip()

    async def process_entry(self, entry, published_on: DateTime) -> Union[Update, None]:
        print(f"[{self.TITLE}] Fetching comic page for {entry.title}")
        response, comic_page = await fetch(entry.link)
        soup = BeautifulSoup(comic_page, "html.parser")
        img_meta = soup.find('meta', {'property': 'og:image'})

        if not img_meta:
            return None

        description = None
        entry_div = soup.find('div', {'class': 'entry'})
        if entry_div:
            description = self.to_telegram_markdown(entry_div)

        response, image = await fetch(img_meta.attrs['content'])
        return Update(entry.title, description, published_on, [image])


__all__ = [
    'CommitStrip',
    'PvP',
    'PennyArcade',
    'SaturdayMorningBreakfastCereal',
    'XKCD',
    'ComicStrip',
    'Update',
    'SlackWyrm',
    'Kill6BillionDemons',
]
