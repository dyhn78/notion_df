from notion_df.util.mixin import input_based_cache


def test_input_based_cache():
    @input_based_cache
    def hello(arg): return {arg}

    @input_based_cache
    def world(arg): return {arg * 2}

    assert hello('yes') is hello('yes')  # two outputs have identical id
    assert world('yes') is not hello('yes')  # cache id is different
