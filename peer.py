import asyncio
from struct import pack, unpack
from enum import Enum
from typing import Union
import random


class Peer:

    def __init__(self, data: Union[dict, bytes]):
        if isinstance(data, dict):
            self.peer_id = data['peer id']
            self.ip_address = data['ip']
            self.port = data['port']
        elif isinstance(data, bytes):
            self.peer_id = None
            self.ip_address = '.'.join(str(byte) for byte in data[:4])
            self.port = unpack('>H', data[4:])[0]
        else:
            raise TypeError(f'Cannot be constructed from {type(data)}')

    def __str__(self) -> str:
        attributes = self.__dict__.items()
        attributes = ', '.join(
            f'{key}={value}' for key, value in attributes)
        return f'{self.__class__.__name__}({attributes})'

    def __repr__(self) -> str:
        return self.__str__()


class MessageId(Enum):
    KeepAlive = -1
    Choke = 0
    Unchoke = 1
    Interested = 2
    NotInterested = 3
    Have = 4
    Bitfield = 5
    Request = 6
    Piece = 7
    Cancel = 8


class Message:

    def __init__(self, message_id: MessageId, **kwargs):
        self.id = message_id.value
        self.type = message_id
        if self.id == -1:
            self.length = 1
            self.id = None
            self.payload = None
        elif self.id in (0, 1, 2, 3):
            self.length = 1
            self.payload = None
        elif self.id == 4:
            self.length = 5
            self.index = kwargs['index']
            self.payload = pack('>I', self.index)
        elif self.id == 5:
            self.bitfield = kwargs['bitfield']
            self.length = 1 + len(self.bitfield)
            self.payload = self.bitfield
        elif self.id in (6, 8):
            self.index = kwargs['index']
            self.begin = kwargs['begin']
            self.size = kwargs.get('size', 2 ** 15)
            self.length = 13
            self.payload = pack('>III', self.index, self.begin, self.size)
        elif self.id == 7:
            self.block = kwargs['block']
            self.index = kwargs['index']
            self.begin = kwargs['begin']
            self.length = 9 + len(self.block)
            self.payload = pack('>II', self.index, self.begin)
            self.payload += self.block

    @staticmethod
    def to_binary(length: int, message_id: int=None,
                  payload: bytes=None) -> bytes:
        message = bytearray()
        message.extend(pack('>I', length))
        if message_id is not None:
            message.extend([message_id])
        if payload is not None:
            message.extend(payload)
        return bytes(message)

    @classmethod
    def from_binary(cls, data: bytes):
        length = unpack('>I', data[:4])
        if length == 0:
            return Message(MessageId.KeepAlive)
        message_id = data[4]
        kwargs = {}
        if message_id == 4:
            kwargs['index'] = unpack('>I', data[5:])
        elif message_id == 5:
            kwargs['bitfield'] = data[5:]
        elif message_id in (6, 8):
            kwargs['index'] = unpack('>I', data[5:9])
            kwargs['begin'] = unpack('>I', data[9:13])
            kwargs['size'] = unpack('>I', data[13:17])
        elif message_id == 7:
            kwargs['index'] = unpack('>I', data[5:9])
            kwargs['begin'] = unpack('>I', data[9:13])
            kwargs['block'] = data[13:]
        else:
            raise ValueError('invalid binary data')
        return cls(MessageId(message_id), **kwargs)

    @property
    def binary(self):
        return Message.to_binary(self.length, self.id, self.payload)

    def __str__(self):
        attributes = self.__dict__.items()
        attributes = ', '.join(f'{key}={value}' for key, value in attributes)
        return f'{self.__class__.__name__}({attributes})'

    def __repr__(self):
        return self.__str__()


class PeerConnection:

    def __init__(self, info_hash: bytes, ip_address: str, port: int,
                 peer_id: str = None):
        self.info_hash = info_hash
        self.ip_address = ip_address
        self.port = port
        self._peer_id = peer_id
        self.is_choking = True
        self.is_interested = False
        self.peer_choking = True
        self.peer_interested = False
        self.reader: asyncio.StreamReader = None
        self.writer: asyncio.StreamWriter = None

    @property
    def peer_id(self) -> str:
        if self._peer_id:
            return self._peer_id
        return ('-BC0001-{}'.format(
                ''.join(random.choice('1234567890') for _ in range(12))))

    async def send_handshake(self):
        message = bytearray([19])                         # protocol length
        message += b'BitTorrent protocol'                 # protocol name
        message += bytes(8)                               # reserved bits
        message += self.info_hash                         # torrent info hash
        message += bytes(self.peer_id, encoding='utf-8')  # own peer id
        if not self.writer:
            await self.open_connection()
        self.writer.write(bytes(message))

    async def receive_handshake(self) -> bool:
        if not self.reader:
            await self.open_connection()
        length = await self.reader.read(1)
        length = length[0]
        # TODO check if protocol is valid
        _ = await self.reader.read(length)
        # TODO implement possible extensions
        _ = await self.reader.read(8)
        info_hash = await self.reader.read(20)
        # TODO check if peer_id matches tracker (give option to abort if not)
        _ = await self.reader.read(20)
        return info_hash == self.info_hash

    async def send(self, message: Message):
        data = message.binary
        if not self.writer:
            await self.open_connection()
        self.writer.write(data)

    async def receive(self) -> Message:
        if not self.reader:
            await self.open_connection()
        length = await self.reader.read(4)
        length = unpack('>I', length)
        data = await self.reader.read(length)
        length = pack('>I', length)
        data = length + data
        return Message.from_binary(data)

    async def open_connection(self):
        reader, writer = await asyncio.open_connection(self.ip_address,
                                                       self.port)
        self.reader = reader
        self.writer = writer

    def close_connection(self):
        self.writer.close()

    def __str__(self):
        attributes = self.__dict__.items()
        attributes = ', '.join(f'{key}={value}' for key, value in attributes)
        return f'{self.__class__.__name__}({attributes})'

    def __repr__(self):
        return self.__str__()
