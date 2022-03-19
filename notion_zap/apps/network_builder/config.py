from __future__ import annotations

from notion_zap.cli.structs import PropertyColumn, PropertyFrame


# noinspection PyUnresolvedReferences
# TODO: self.tag 를 tuple 로 다시 짜기.
class NetworkPropertyColumn(PropertyColumn):
    @property
    def edge_type(self):
        return self.tag.split('_')[0]

    @property
    def edge_vertical(self):
        return self.EDGE_VERTICALS[self.edge_type]

    @property
    def edge_weight(self):
        return self.EDGE_WEIGHTS[self.edge_type]

    @property
    def edge_target(self):
        return self.tag.split('_')[1]

    EDGE_ASPECTS = ['edge_type', 'edge_vertical',
                    'edge_weight', 'edge_target']

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
        :return list of valid structs columns
        """
        res = []
        for tag in self.key_aliases():
            unit = self.by_alias[tag]
            if isinstance(unit, NetworkPropertyColumn):
                for aspect in unit.EDGE_ASPECTS:
                    try:
                        if getattr(unit, aspect) == keyword:
                            res.append(unit)
                            break
                    except KeyError:
                        pass
        return res


class NetworkFrames:
    _Frame = NetworkPropertyFrame
    _NCl = NetworkPropertyColumn
    _Cl = PropertyColumn
    # TODO
    _common = _Frame([
        _NCl(tag='hi_self', key='✖️구성'),
        _NCl(tag='in_self', key='➖속성'),
        _NCl(tag='lo_self', key='➗요소'),
        _NCl(tag='out_self', key='➕적용'),
        _NCl(tag='front_self', key='⭕결산'),
        _NCl(tag='back_self', key='⭕경과'),
        _Cl(tag='forbidden', key='🔵접근성=금지'),
    ])
    THEMES = _Frame(_common, [
        _NCl(tag='in_ideas', key='📕속성'),
        _NCl(tag='lo_ideas', key='📕요소'),
    ])
    IDEAS = _Frame(_common, [
        _NCl(tag='hi_themes', key='📕구성'),
        _NCl(tag='out_themes', key='📕적용')
    ])
