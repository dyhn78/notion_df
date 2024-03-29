import re
from itertools import chain

import networkx as nx

from notion_zap.apps.network_builder.config import NetworkFrames, NetworkPropertyFrame
from notion_zap.cli import blocks
from notion_zap.cli.core.base import Root


class TopologyBuilder:
    def __init__(self, request_size=0):
        self.request_size = request_size
        self.G = nx.DiGraph()
        self.root = Root(print_response_heads=5)
        self.themes = self.root.space.database(NetworkFrames.THEMES, ).rows
        self.ideas = self.root.space.database(NetworkFrames.IDEAS, ).rows
        self.all: dict[str, blocks.RowChildren] = {
            'themes': self.themes,
            'ideas': self.ideas
        }

    def execute(self):
        self.make_query()
        self.add_nodes()
        self.add_edges()
        return self.G

    def make_query(self):
        for pagelist in [self.themes]:
            query = pagelist.open_query()
            maker = query.filter_manager_by_tags.relation('front_self')
            ft = maker.__bool__()
            query.push_filter(ft)
            query.save()
        for pagelist in [self.ideas]:
            query = pagelist.open_query()
            query.save()

    def add_nodes(self):
        for i, page in enumerate(chain(*self.all.values())):
            self.G.add_node(self.parse_title(page.block_name), page_id=page.block_id)

    def add_edges(self):
        for down_pagelist in self.all.values():
            for down_page in down_pagelist:
                down_frame = down_pagelist.frame
                assert isinstance(down_frame, NetworkPropertyFrame)
                for unit in down_frame.filter_tags('up'):
                    target_str = unit.edge_target
                    if target_str == 'self':
                        up_pagelist = down_pagelist
                    else:
                        up_pagelist = self.all[unit.edge_target]
                    up_ids = down_page.read_key_alias(unit.tag)
                    for up_id in up_ids:
                        if up_id not in up_pagelist.ids():
                            continue
                        up_page = up_pagelist.by_id[up_id]
                        self.G.add_edge(
                            self.parse_title(up_page.block_name),
                            self.parse_title(down_page.block_name),
                            edge_type=unit.edge_type,
                            edge_weight=unit.edge_weight,
                        )

    def add_edges_naively(self):
        for down_pagelist in self.all.values():
            for down_page in down_pagelist:
                down_frame = down_pagelist.frame
                assert isinstance(down_frame, NetworkPropertyFrame)
                for unit in down_frame.filter_tags('up'):
                    up_ids = down_page.read_key_alias(unit.tag)
                    for up_id in up_ids:
                        if up_id not in self.root.ids():
                            continue
                        up_page = self.root.by_id[up_id]
                        self.G.add_edge(
                            self.parse_title(up_page.block_name),
                            self.parse_title(down_page.block_name),
                            edge_type=unit.edge_type,
                            edge_weight=unit.edge_weight,
                        )

    @staticmethod
    def parse_title(page_title: str):
        code = re.compile(r'(?<=\[).+(?=\])')  # ex) '[cdit.html_css] ....'
        if flag := code.search(page_title):
            return flag.group()
        return page_title
