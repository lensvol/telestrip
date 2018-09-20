from time import mktime
from typing import Union, List

import feedparser
import pendulum
import attr
from pendulum import DateTime

from telestrip.helpers import fetch


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

        self.log(f"Requesting feed from {self.INDEX_URL}...")
        response, page = await fetch(self.INDEX_URL)
        rss = feedparser.parse(page)

        for entry in rss.entries:
            if 'published_parsed' in entry:
                parsed_timestamp = entry.published_parsed
            else:
                parsed_timestamp = entry.updated_parsed
            published_on = pendulum.from_timestamp(mktime(parsed_timestamp))

            if published_on < moment:
                continue

            update = await self.process_entry(entry, published_on)
            if update is not None:
                result.append(update)

        return result

    async def process_entry(self, entry, published_on: DateTime) -> Union[Update, None]:
        raise NotImplemented

    def log(self, message: str):
        print(f'[{self.TITLE}] {message}')
