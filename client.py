from torrent import Torrent
from tracker import TrackerConnection

from urllib.parse import urlparse
import asyncio


class Client:

    def __init__(self, port: int=6881):
        self.port = port
        self.trackers = set()
        self.torrents = {}
        self.id_counter = 0
        self.queue = asyncio.Queue()
        self.abort = False

    def add_torrent(self, torrent: Torrent) -> int:
        self.torrents[self.id_counter] = torrent
        self.id_counter += 1
        tracker = urlparse(torrent.meta_info.announce).netloc
        self.trackers.add(tracker)
        return len(self.torrents) - 1

    def remove_torrent(self, torrent_id: int):
        try:
            del self.torrents[torrent_id]
        except KeyError:
            pass

    def start_torrent(self, torrent_id: int):
        torrent = self.torrents[torrent_id]
        connection = TrackerConnection(torrent, port=self.port)
        self.queue.put_nowait(connection)

    async def loop(self):
        while not self.abort:
            connection = await self.queue.get()
            response = await connection.send('started')


