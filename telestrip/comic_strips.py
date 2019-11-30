from time import mktime
from typing import List, Union

import attr
import feedparser
import pendulum
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from pendulum import DateTime

from telestrip.helpers import fetch
from telestrip.base import ComicStrip, Update


class PennyArcade(ComicStrip):
    ID = "penny-arcade"
    TITLE = "Penny Arcade"
    INDEX_URL = "http://penny-arcade.com/feed"

    def to_telegram_markdown(self, soup):
        result = ""
        for p in soup.findAll("p"):
            for child in list(p.children)[0:-1]:
                if child.name is None:
                    result += str(child)
                    result += "\n\n"
                elif child.name == "a":
                    result = result.strip()
                    result += " [{0}]({1})".format(child.text, child.attrs["href"])
                elif child.name == "i":
                    result = result.strip()
                    result += " _{0}_ ".format(str(child.text))
                elif child.name == "b":
                    result = result.strip()
                    result += " *{0}* ".format(str(child.text))

        return result.replace("\0xa", "").strip()

    async def process_entry(self, entry, published_on: DateTime) -> Union[Update, None]:
        if not entry.title.startswith("Comic:"):
            self.log(f"Ignoring entry {entry.title}: not a comic")
            return None

        self.log(f"Fetching comic page for {entry.title}")
        response, comic_page = await fetch(entry.link)
        soup = BeautifulSoup(comic_page, "html.parser")
        comic_img = soup.find("div", {"id": "comicFrame"}).findChild("img")

        description = None

        post_link = soup.find("a", {"title": "Read News Post"})
        if post_link:
            self.log(f"Fetching post page for {entry.title}...")
            response, post_page = await fetch(post_link.attrs["href"])
            soup = BeautifulSoup(post_page, "html.parser")
            copy_text = soup.find("div", {"class": "copy"})
            if copy_text:
                description = self.to_telegram_markdown(copy_text)

        self.log(f'Fetching image from {comic_img.attrs["src"]}')
        response, image = await fetch(comic_img.attrs["src"])

        return Update(self.ID, entry.title, description, published_on, [image])


class PvP(ComicStrip):
    ID = "pvp"
    TITLE = "PvP"
    INDEX_URL = "http://pvponline.com/feed"

    async def process_entry(self, entry, published_on: DateTime) -> Union[Update, None]:
        if not entry.title.startswith("Comic:"):
            self.log(f"Ignoring entry {entry.title}: not a comic")
            return None

        self.log(f"Fetching comic page for {entry.title}")
        response, comic_page = await fetch(entry.link)
        soup = BeautifulSoup(comic_page, "html.parser")
        comic_img = soup.find("section", {"class": "comic-art"}).findChild("img")

        self.log(f'Fetching image from {comic_img.attrs["src"]}')
        response, image = await fetch(comic_img.attrs["src"])

        return Update(self.ID, entry.title, None, published_on, [image])


class SaturdayMorningBreakfastCereal(ComicStrip):
    ID = "smbc"
    TITLE = "Saturday Morning Breakfast Cereal"
    INDEX_URL = "https://www.smbc-comics.com/comic/rss"

    async def process_entry(self, entry, published_on: DateTime) -> Union[Update, None]:
        self.log(f"Fetching comic page for {entry.title}")
        soup = BeautifulSoup(entry.description, "html.parser")
        comic_img = soup.find("img")

        description = ""

        p_hovertext = soup.find("p")
        if p_hovertext:
            description = p_hovertext.findNext("br").next

        self.log(f'Fetching image from {comic_img.attrs["src"]}')
        response, image = await fetch(comic_img.attrs["src"])

        return Update(self.ID, entry.title, description, published_on, [image])


class XKCD(ComicStrip):
    ID = "xkcd"
    TITLE = "XKCD"
    INDEX_URL = "https://xkcd.com/rss.xml"

    async def process_entry(self, entry, published_on: DateTime) -> Union[Update, None]:
        self.log(f"Fetching comic page for {entry.title}")
        soup = BeautifulSoup(entry.description, "html.parser")
        comic_img = soup.find("img")

        self.log(f'Fetching image from {comic_img.attrs["src"]}')
        response, image = await fetch(comic_img.attrs["src"])
        return Update(
            self.ID, entry.title, comic_img.attrs["alt"], published_on, [image]
        )


class CommitStrip(ComicStrip):
    ID = "commit-strip"
    TITLE = "Commit Strip"
    INDEX_URL = "https://www.commitstrip.com/en/feed/"

    async def process_entry(self, entry, published_on: DateTime) -> Union[Update, None]:
        self.log(f"Fetching comic page for {entry.title}")
        soup = BeautifulSoup(entry.content[0].value, "html.parser")
        comic_imgs = soup.findAll("img")

        if not comic_imgs:
            return None

        self.log(f'Fetching image from {comic_imgs[0].attrs["src"]}')
        response, image = await fetch(comic_imgs[0].attrs["src"])
        return Update(self.ID, entry.title, "", published_on, [image])


class SlackWyrm(ComicStrip):
    ID = "slack-wyrm"
    TITLE = "Slack Wyrm"
    INDEX_URL = "http://www.joshuawright.net/rss_joshuawright.xml"

    async def process_entry(self, entry, published_on: DateTime) -> Union[Update, None]:
        self.log(f"Fetching comic page for {entry.title}")
        response, comic_page = await fetch(entry.link)
        soup = BeautifulSoup(comic_page, "html.parser")
        comic_frames = soup.findAll("div", {"data-muse-type": "img_frame"})

        images = []
        for frame in comic_frames:
            comic_img = frame.findChild("img")
            self.log(f'Fetching image from {comic_img.attrs["src"]}')
            response, image = await fetch(
                "http://www.joshuawright.net/" + comic_img.attrs["src"]
            )
            images.append(image)

        return Update(self.ID, entry.title, entry.summary, published_on, images)


class Kill6BillionDemons(ComicStrip):
    ID = "kill-6-billion-demons"
    TITLE = "Kill 6 Billion Demons"
    INDEX_URL = "https://killsixbilliondemons.com/feed/"

    def to_telegram_markdown(self, soup):
        result = ""
        for p in soup.findAll("p"):
            for child in p.children:
                if child.name is None:
                    result += str(child)
                    result += "\n\n"
                elif child.name == "a":
                    result = result.strip()
                    result += " [{0}]({1})".format(child.text, child.attrs["href"])
                elif child.name == "i":
                    result = result.strip()
                    result += " _{0}_ ".format(str(child.text))
                elif child.name == "b":
                    result = result.strip()
                    result += " *{0}* ".format(str(child.text))

        return result.replace("\0xa", "").strip()

    async def process_entry(self, entry, published_on: DateTime) -> Union[Update, None]:
        self.log(f"Fetching comic page for {entry.title}")
        response, comic_page = await fetch(entry.link)
        soup = BeautifulSoup(comic_page, "html.parser")
        img_meta = soup.find("meta", {"property": "og:image"})

        if not img_meta:
            return None

        description = None
        entry_div = soup.find("div", {"class": "entry"})
        if entry_div:
            description = self.to_telegram_markdown(entry_div)

        response, image = await fetch(img_meta.attrs["content"])
        return Update(self.ID, entry.title, description, published_on, [image])


class DorkTower(ComicStrip):
    ID = "dork-tower"
    TITLE = "Dork Tower"
    INDEX_URL = "http://www.dorktower.com/feed/"

    async def process_entry(self, entry, published_on: DateTime) -> Union[Update, None]:
        self.log(f"Fetching comic page for {entry.title}")
        soup = BeautifulSoup(entry.content[0].value, "html.parser")
        candidate_imgs = soup.findAll("img")
        url = None

        for candidate in candidate_imgs:
            if "/DorkTower" in candidate.attrs["src"]:
                url = candidate.attrs["src"]
                break

        if not url:
            return None

        self.log(f"Fetching image from {url}")
        response, image = await fetch(url)
        return Update(self.ID, entry.title, "", published_on, [image])


__all__ = [
    "CommitStrip",
    "PvP",
    "PennyArcade",
    "SaturdayMorningBreakfastCereal",
    "XKCD",
    "ComicStrip",
    "Update",
    "SlackWyrm",
    "Kill6BillionDemons",
    "DorkTower",
]
