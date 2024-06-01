from types import MappingProxyType
from typing import Any, Dict, Type

from .registry import TypeHandler, register_type_handler

JSON_SCHEMA_TYPES = MappingProxyType(
    {
        int: "integer",
        float: "number",
        str: "string",
        bool: "boolean",
        # Include both None and type(None) in the dictionary to handle two scenarios:
        #
        # 1. When a function parameter is annotated with None directly, such as:
        #      def func(param: None):
        #    The None key is used to map the type to the JSON Schema type "null".
        #
        # 2. When a function parameter is part of a union type with None, such as:
        #      def func(param: typing.Union[int, None]):
        #    The type(None) key is used when resolving the union type to map the None type
        #    to the JSON Schema type "null".
        #
        # By including both None and type(None), the code can handle both scenarios
        # correctly and avoid raising a ValueError for unsupported types.
        None: "null",
        type(None): "null",
    }
)


@register_type_handler
class BasicTypeHandler(TypeHandler):
    def is_type(self, param_type: Type) -> bool:
        return param_type in JSON_SCHEMA_TYPES

    def resolve(self, param_type: Type) -> Dict[str, Any]:
        return {"type": JSON_SCHEMA_TYPES[param_type]}
