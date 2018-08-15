from bencoding import decode, encode
from data import Piece

from hashlib import sha1
from collections import namedtuple
from datetime import datetime
from typing import List


class Torrent:

    def __init__(self, filepath: str):
        self.filepath = filepath
        with open(filepath, 'rb') as file:
            data = decode(file.read())
        self.meta_info = MetaInfo(data)
        self.info_hash = sha1(encode(data['info'])).digest()
        self.uploaded = 0
        self.downloaded = 0
        self.tracker_id = None
        self.complete = False
        self.running = False

    @property
    def left(self):
        if not self.meta_info.multi_file:
            return self.meta_info.length - self.downloaded
        else:
            total = sum(file.length for file in self.meta_info.files)
            return total - self.downloaded

    def __str__(self):
        attributes = self.__dict__.items()
        attributes = ', '.join(f'{key}={value}' for key, value in attributes)
        return f'{self.__class__.__name__}({attributes})'

    def __repr__(self):
        return self.__str__()

    @property
    def bitfield(self) -> bytes:
        pieces = self.meta_info.pieces
        length = len(pieces) + (len(pieces) % 8)
        bitfield = bytearray(length // 8)
        current = 0
        for i in range(len(bitfield)):
            byte = 0
            for j in range(8):
                bit = pieces[current].completed if current < len(pieces) else 0
                byte += bit
                current += 1
                byte <<= 1
            byte >>= 1
            bitfield[i] = byte
        return bytes(bitfield)

    async def start(self, peers: List[Peer]):
        self.running = True


class MetaInfo:

    File = namedtuple('File', ('filepath', 'length', 'md5sum'))

    def __init__(self, data: dict):
        self.announce = str(data['announce'], encoding='utf-8')
        self.announce_list = data.get('announce-list')
        self.creation_date: int = data.get('creation date')
        if self.creation_date:
            self.creation_date = datetime.fromtimestamp(self.creation_date)
        self.comment = data.get('comment')
        self.created_by = data.get('created by')
        self.encoding = data.get('encoding')
        self.piece_length = data['info']['piece length']
        self.pieces = list()
        pieces = data['info']['pieces']
        for i in range(0, len(pieces), 20):
            piece_hash = pieces[i:i + 20]
            self.pieces.append(Piece(i, piece_hash, self.piece_length, 2**14))
        self.private = bool(data['info'].get('private'))
        if data['info'].get('length'):
            self.multi_file = False
            self.name = str(data['info']['name'], encoding='utf-8')
            self.length = data['info']['length']
            self.md5sum = data['info'].get('md5sum')
        else:
            self.multi_file = True
            self.directory = str(data['info']['name'], encoding='utf-8')
            self.files = list()
            for file in data['info']['files']:
                filepath = str(b'/'.join(file['path']), encoding='utf-8')
                self.files.append(self.File(filepath, file['length'],
                                            file.get('md5sum')))

    def __str__(self) -> str:
        attributes = self.__dict__.items()
        attributes = ', '.join(f'{key}={value}' for key, value in attributes)
        return f'{self.__class__.__name__}({attributes})'

    def __repr__(self) -> str:
        return self.__str__()
