# -*- config: utf-8 -*-
import argparse
import asyncio
import inspect
import os

import pendulum

from telestrip import comic_strips
from telestrip.base import ComicStrip
from telestrip.database import Database
from telestrip.helpers import (
    collect_strips,
    send_updates_to_telegram,
    print_updates_to_console,
)

RSS_DATE_FORMAT = "ddd, D MMM YYYY HH:mm:ss Z"


def main(specific_strips=None, day_delta=1, print_to_console=False):
    database = Database()
    now = pendulum.now()

    bot_token = os.environ.get("BOT_TOKEN")
    recipient_id = os.environ.get("RECIPIENT_ID")

    if not bot_token:
        print("No Telegram bot API token in BOT_TOKEN variable!")
        exit(-1)

    if not recipient_id:
        print("No recipient specified in RECIPIENT_ID variable!")
        exit(-1)

    requested_strips = [
        cls()
        for name, cls in inspect.getmembers(comic_strips, inspect.isclass)
        if issubclass(cls, ComicStrip) and cls.ID is not None
    ]

    if specific_strips:
        requested_strips = filter(
            lambda strip: strip.ID in specific_strips, requested_strips
        )

    last_seen_timestamps = {
        strip.ID: now.subtract(days=day_delta) for strip in requested_strips
    }

    timestamps_from_database = database.retrieve_strip_timestamps()
    last_seen_timestamps.update(timestamps_from_database)

    loop = asyncio.get_event_loop()
    updates = loop.run_until_complete(
        collect_strips(list(requested_strips), last_seen_timestamps)
    )

    database.store_strip_timestamps(updates)

    if not print_to_console:
        loop.run_until_complete(
            send_updates_to_telegram(recipient_id, bot_token, updates)
        )
    else:
        print_updates_to_console(updates)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--console",
        action="store_true",
        help="Display results in the console instead of sending them on.",
    )
    parser.add_argument(
        "--delta",
        type=int,
        help="Specify boundary in number of days from now.",
        default=1,
    )
    parser.add_argument("--strips", help="Collect only strips with specified IDs")
    args = parser.parse_args()

    if args.strips:
        strips = list(map(lambda s: s.strip(), args.strips.split(",")))
    else:
        strips = None

    main(specific_strips=strips, day_delta=args.delta, print_to_console=args.console)
