import types
import typing
from typing import Type

from .registry import TypeHandler, register_type_handler, resolve_type


@register_type_handler
class UnionTypeHandler(TypeHandler):
    def is_type(self, param_type: Type) -> bool:
        return typing.get_origin(param_type) in [typing.Union, types.UnionType]

    def resolve(self, param_type: Type) -> typing.Dict[str, typing.Any]:
        union_types = typing.get_args(param_type)
        resolved_types = [resolve_type(t) for t in union_types]

        schema = {"type": []}
        for resolved_type in resolved_types:
            if resolved_type["type"] == "array":
                schema["type"].append("array")
                schema["items"] = resolved_type["items"]
            else:
                schema["type"].append(resolved_type["type"])

        return schema
