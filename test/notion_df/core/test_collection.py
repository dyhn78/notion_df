from dataclasses import dataclass

from notion_df.core.collection import coalesce_dataclass


def test_coalesce_dataclass():
    @dataclass
    class ExampleDataClass:
        field1: int | None = None
        field2: str | None = None
        field3: float | None = None


    instance1 = ExampleDataClass(field1=1, field2=None, field3=2.5)
    instance2 = ExampleDataClass(field1=None, field2="Hello", field3=None)
    merged_instance = coalesce_dataclass(instance1, instance2)

    assert merged_instance == ExampleDataClass(field1=1, field2='Hello', field3=2.5)
