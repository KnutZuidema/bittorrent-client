from typing import Union, Tuple

TOKEN_LIST = b'l'
TOKEN_INTEGER = b'i'
TOKEN_DICTIONARY = b'd'
TOKEN_STRING = b':'
TOKEN_END = b'e'
TOKENS = [TOKEN_DICTIONARY, TOKEN_END, TOKEN_INTEGER, TOKEN_LIST,
          TOKEN_STRING]


def decode(data: bytes) -> Union[list, dict, int, bytes]:
    return decode_with_length(data)[0]


def decode_with_length(data: bytes) -> Tuple[
                                       Union[list, dict, int, bytes], int]:
    assert len(data) > 0, 'no data'
    assert data[0:1] in [TOKEN_DICTIONARY, TOKEN_INTEGER, TOKEN_LIST] \
        or data[0:1] in b'1234567890', \
        f'{str(data[0:1])} is not a valid token'
    start = data[0:1]
    if start == TOKEN_DICTIONARY:
        return decode_dictionary(data)
    if start == TOKEN_INTEGER:
        return decode_integer(data)
    if start == TOKEN_LIST:
        return decode_list(data)
    return decode_string(data)


def encode(data: Union[int, str, list, dict]) -> bytes:
    if isinstance(data, int):
        return encode_int(data)
    if isinstance(data, str):
        return encode_string(data)
    if isinstance(data, bytes):
        return encode_bytes(data)
    if isinstance(data, list):
        return encode_list(data)
    if isinstance(data, dict):
        return encode_dictionary(data)


def index_of(token: bytes, data: bytes) -> int:
    try:
        return data.index(token)
    except ValueError as error:
        raise RuntimeError('Not a valid bencoded object') from error


def decode_integer(data: bytes) -> Tuple[int, int]:
    end = index_of(TOKEN_END, data)
    length = end + 1
    result = int(data[1:end])
    return result, length


def decode_string(data: bytes) -> Tuple[bytes, int]:
    delimiter = index_of(TOKEN_STRING, data)
    length = int(data[:delimiter])
    start = delimiter + 1
    end = start + length
    result = data[start:end]
    length = end
    return result, length


def decode_list(data: bytes) -> Tuple[list, int]:
    result = list()
    index = 1
    while data[index:index + 1] != TOKEN_END:
        value, length = decode_with_length(data[index:])
        result.append(value)
        index += length
    length = index + 1
    return result, length


def decode_dictionary(data: bytes) -> Tuple[dict, int]:
    result = dict()
    index = 1
    while data[index:index + 1] != TOKEN_END:
        key, length = decode_string(data[index:])
        key = str(key, encoding='utf-8')
        index += length
        value, length = decode_with_length(data[index:])
        index += length
        result[key] = value
    length = index + 1
    return result, length


def encode_int(data: int) -> bytes:
    result = b'i' + bytes(str(data), encoding='utf-8') + b'e'
    return result


def encode_string(data: str) -> bytes:
    result = bytes(str(len(data)), encoding='utf-8')
    result += b':' + bytes(data, encoding='utf-8')
    return result


def encode_bytes(data: bytes) -> bytes:
    result = bytes(str(len(data)), encoding='utf-8')
    result += b':' + data
    return result


def encode_list(data: list) -> bytes:
    result = b'l'
    for item in data:
        result += encode(item)
    result += b'e'
    return result


def encode_dictionary(data: dict) -> bytes:
    result = b'd'
    for key, value in data.items():
        assert isinstance(key, str), \
            f'key was of type {type(key)}, only str allowed'
        result += encode_string(key)
        result += encode(value)
    result += b'e'
    return result
