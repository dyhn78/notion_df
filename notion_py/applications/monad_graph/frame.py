from __future__ import annotations
from typing import Union

from notion_py.interface.common import PropertyFrame, PropertyFrameUnit


class NetworkPropertyFrameUnit(PropertyFrameUnit):
    @property
    def edge_type(self):
        return self.prop_tag.split('_')[0]

    @property
    def edge_vertical(self):
        return self.EDGE_VERTICALS[self.edge_type]

    @property
    def edge_weight(self):
        return self.EDGE_WEIGHTS[self.edge_type]

    @property
    def edge_target(self):
        return self.prop_tag.split('_')[1]

    EDGE_VERTICALS = {
        'hi': 'up',
        'lo': 'down',
        'in': 'up',
        'out': 'down',
    }
    EDGE_WEIGHTS = {
        'hi': 'strong',
        'lo': 'strong',
        'in': 'weak',
        'out': 'weak',
    }


class NetworkPropertyFrame(PropertyFrame):
    def filter_tags(self, keyword: str):
        """
        :param keyword: currently supports {'hi', 'lo', 'in', 'out',
            'up', 'down', 'strong', 'weak',
            'self', 'themes', 'ideas'}
        :return list of valid frame units
        """
        res = []
        for tag in self.tags():
            unit = self.by_tag[tag]
            if isinstance(unit, NetworkPropertyFrameUnit):
                aspects = ['edge_type', 'edge_vertical',
                           'edge_weight', 'edge_target']
                for aspect in aspects:
                    if getattr(unit, aspect) == keyword:
                        res.append(unit)
                        break
        return res


class NetworkFrames:
    _Frame = NetworkPropertyFrame
    _Unit = NetworkPropertyFrameUnit
    _common = _Frame([
        _Unit(tag='hi_self', key='✖️구성'),
        _Unit(tag='in_self', key='➖속성'),
        _Unit(tag='lo_self', key='➗요소'),
        _Unit(tag='out_self', key='➕적용'),
    ])
    THEMES = _Frame(_common, [
        _Unit(tag='in_ideas', key='📕속성'),
        _Unit(tag='lo_ideas', key='📕요소'),
    ])
    IDEAS = _Frame(_common, [
        _Unit(tag='hi_themes', key='📕구성'),
        _Unit(tag='out_themes', key='📕적용')
    ])
