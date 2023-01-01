from notion_df.util.mixin import cache_on_input


def test_input_based_cache():
    @cache_on_input
    def hello(arg): return {arg}

    @cache_on_input
    def world(arg): return {arg * 2}

    assert hello('yes') is hello('yes')  # two outputs have identical id
    assert world('yes') is not hello('yes')  # cache id is different

