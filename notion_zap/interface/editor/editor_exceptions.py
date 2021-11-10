from notion_zap.interface.editor.struct import MasterEditor


class BlockTypeError(TypeError):
    def __init__(self, block: MasterEditor):
        self.block = block
        self.message = f"cannot perform the order upon invalid block type :: " \
                       f"{self.block}"
        super().__init__(self.message)


class NoParentFoundError(ValueError):
    def __init__(self, block: MasterEditor):
        self.block = block
        self.message = f"cannot find parent_block of ::" \
                       f"{self.block}"
