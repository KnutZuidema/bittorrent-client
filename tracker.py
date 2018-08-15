from torrent import Torrent
from bencoding import decode
from peer import Peer

from urllib.parse import urlencode
import random

import aiohttp


class TrackerResponse:

    def __init__(self, data: dict):
        self.failure_reason = data.get('failure reason')
        self.warning_message = data.get('warning message')
        self.interval = data.get('interval')
        self.min_interval = data.get('min interval')
        self.tracker_id = data.get('tracker id')
        self.complete = data.get('complete')
        self.incomplete = data.get('incomplete')
        peers = data.get('peers')
        if isinstance(peers, list):
            self.peers = [Peer(peer) for peer in peers]
        elif isinstance(peers, bytes):
            peers = [peers[i:i + 6] for i in range(len(peers))]
            self.peers = [Peer(peer) for peer in peers]
        else:
            self.peers = None

    def __str__(self) -> str:
        attributes = self.__dict__.items()
        attributes = ', '.join(f'{key}={value}' for key, value in attributes)
        return f'{self.__class__.__name__}({attributes})'

    def __repr__(self) -> str:
        return self.__str__()


class TrackerConnection:

    def __init__(self, torrent: Torrent, port: int = 6881, peer_id: str = None,
                 compact: bool = True, no_peer_id: bool = False,
                 ip_address: str = None, max_peers: int = 25,
                 key: str = None):
        self.torrent = torrent
        self.port = port
        self.peer_id = peer_id
        self.compact = compact
        self.no_peer_id = no_peer_id
        self.ip_address = ip_address
        self.max_peers = max_peers
        self.key = key

    def build_parameters(self, event: str = None) -> dict:
        params = {
            'port': self.port,
            'compact': int(self.compact),
            'info_hash': self.torrent.info_hash,
            'uploaded': self.torrent.uploaded,
            'downloaded': self.torrent.downloaded,
            'left': self.torrent.left,
            'numwant': self.max_peers
        }
        if self.peer_id:
            params['peer_id'] = self.peer_id
        else:
            params['peer_id'] = ('-BC0001-{0}'.format(
                ''.join(random.choice('1234567890') for _ in range(12))))
        if self.ip_address:
            params['ip'] = self.ip_address
        if event:
            params['event'] = event
        if self.torrent.tracker_id:
            params['trackerid'] = self.torrent.tracker_id
        if self.key:
            params['key'] = self.key
        return params

    async def send(self, event: str = None) -> TrackerResponse:
        params = self.build_parameters(event=event)
        params = urlencode(params)
        url = f'{self.torrent.meta_info.announce}?{params}'
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise ConnectionError('Unable to reach tracker')
                data = await response.read()
        return TrackerResponse(decode(data))

    def __str__(self) -> str:
        attributes = self.__dict__.items()
        attributes = ', '.join(f'{key}={value}' for key, value in attributes)
        return f'{self.__class__.__name__}({attributes})'

    def __repr__(self) -> str:
        return self.__str__()
