# To use this code, make sure you
#
#     import json
#
# and then, to convert JSON from a string, do
#
#     result = batches_item_from_dict(json.loads(json_string))


from dataclasses import dataclass
from typing import Any, List, TypeVar, Type, cast, Callable


T = TypeVar("T")


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def from_int(x: Any) -> int:
    assert isinstance(x, int) and not isinstance(x, bool)
    return x


def from_none(x: Any) -> Any:
    assert x is None
    return x


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


@dataclass
class Recipe:
    name: str

    @staticmethod
    def from_dict(obj: Any) -> "Recipe":
        assert isinstance(obj, dict)
        name = from_str(obj.get("name"))
        return Recipe(name)

    def to_dict(self) -> dict:
        result: dict = {}
        result["name"] = from_str(self.name)
        return result


@dataclass
class BatchesItemElement:
    id: str
    name: str
    batch_no: int
    status: str
    brewer: None
    brew_date: int
    recipe: Recipe

    @staticmethod
    def from_dict(obj: Any) -> "BatchesItemElement":
        assert isinstance(obj, dict)
        id = from_str(obj.get("_id"))
        name = from_str(obj.get("name"))
        batch_no = from_int(obj.get("batchNo"))
        status = from_str(obj.get("status"))
        brewer = from_str(obj.get("brewer"))
        brew_date = from_int(obj.get("brewDate"))
        recipe = Recipe.from_dict(obj.get("recipe"))
        return BatchesItemElement(id, name, batch_no, status, brewer, brew_date, recipe)

    def to_dict(self) -> dict:
        result: dict = {}
        result["_id"] = from_str(self.id)
        result["name"] = from_str(self.name)
        result["batchNo"] = from_int(self.batch_no)
        result["status"] = from_str(self.status)
        result["brewer"] = from_str(self.brewer)
        result["brewDate"] = from_int(self.brew_date)
        result["recipe"] = to_class(Recipe, self.recipe)
        return result


def batches_item_from_dict(s: Any) -> List[BatchesItemElement]:
    return from_list(BatchesItemElement.from_dict, s)


def batches_item_to_dict(x: List[BatchesItemElement]) -> Any:
    return from_list(lambda x: to_class(BatchesItemElement, x), x)
