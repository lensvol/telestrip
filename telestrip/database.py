# -*- coding: utf-8 -*-
import sqlite3

from typing import List, Dict


class Database(object):
    def store_strip_timestamps(self, updates: List["Update"]):
        last_seen = {}
        for update in updates:
            previously_seen = last_seen.get(update.strip_id)
            if not previously_seen or update.timestamp > previously_seen:
                last_seen[update.strip_id] = update.timestamp.int_timestamp

    def retrieve_strip_timestamps(self) -> Dict[str, int]:
        return {}
