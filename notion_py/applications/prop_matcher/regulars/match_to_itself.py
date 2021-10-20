from notion_py.applications.prop_matcher.regulars.base import Matcher


class MatchertoItself(Matcher):
    def execute(self):
        for pagelist in [self.bs.journals, self.bs.memos, self.bs.writings]:
            for dom in pagelist:
                if bool(dom.props.read_at('to_itself')):
                    continue
                dom.props.write_at('to_itself', [dom.master_id])