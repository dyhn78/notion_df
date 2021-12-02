from .leaders import Block, Registry


class InvalidBlockTypeError(TypeError):
    def __init__(self, block: Block):
        self.block = block
        self.message = f"cannot perform the order upon invalid block type :: " \
                       f"{self.block}"
        super().__init__(self.message)


class InvalidParentTypeError(ValueError):
    def __init__(self, block: Block):
        self.block = block
        self.message = f"parent block should be the type of ChildrenBearer;" \
                       f"block info ::" \
                       f"{self.block}" \
                       f"parent info ::" \
                       f"{self.block.parent}"


class NoParentFoundError(ValueError):
    def __init__(self, block: Block):
        self.block = block
        self.message = f"cannot find parent of this block ::" \
                       f"{self.block}"


class DanglingBlockError(ValueError):
    def __init__(self, child_block: Block, registry: Registry):
        self.block = child_block
        self.attachments = registry
        self.message = f'{self.block} was never registered to {self.attachments}'
