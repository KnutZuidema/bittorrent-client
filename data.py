class Piece:

    def __init__(self, index: int, piece_hash: bytes,
                 piece_length: int, block_length: int):
        self.index = index
        self.hash = piece_hash
        self.piece_length = piece_length
        self.block_length = block_length
        self.blocks = [Block(i, i*block_length, block_length)
                       for i in range(piece_length // block_length)]
        self.blocks.append(Block(len(self.blocks),
                                 piece_length - block_length,
                                 piece_length % block_length))

    @property
    def completed(self):
        return all(block.state == Block.Have for block in self.blocks)

    def __str__(self):
        attributes = self.__dict__.items()
        attributes = ', '.join(f'{key}={value}' for key, value in attributes)
        return f'{self.__class__.__name__}({attributes})'

    def __repr__(self):
        return self.__str__()


class Block:

    Missing = 0
    Have = 1
    Ongoing = 2

    def __init__(self, index: int, offset: int, length: int):
        self.index = index
        self.offset = offset
        self.length = length
        self.state = Block.Missing
        self.data = bytes(self.length)

    def __str__(self):
        attributes = self.__dict__.copy()
        del attributes['data']
        attributes = attributes.items()
        attributes = ', '.join(f'{key}={value}' for key, value in attributes)
        return f'{self.__class__.__name__}({attributes})'

    def __repr__(self):
        return self.__str__()
