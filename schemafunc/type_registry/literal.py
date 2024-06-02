from typing import Any, Dict, Literal, Type, get_args, get_origin

from schemafunc.exceptions import UnsupportedLiteralTypeError
from schemafunc.type_registry.basic_types import JSON_SCHEMA_TYPES
from schemafunc.type_registry.registry import TypeHandler, register_type_handler


@register_type_handler
class LiteralTypeHandler(TypeHandler):
    def is_type(self, param_type: Type) -> bool:
        return get_origin(param_type) is Literal

    def resolve(self, param_type: Type) -> Dict[str, Any]:
        literal_values = get_args(param_type)
        # supported_types = (int, float, str, bool, type(None))
        supported_types = tuple(
            x for x in JSON_SCHEMA_TYPES.keys() if isinstance(x, type)
        )
        if all(isinstance(v, supported_types) for v in literal_values):
            return {"type": "string", "enum": list(literal_values)}
        else:
            raise UnsupportedLiteralTypeError(
                f"Unsupported Literal values: {literal_values}"
            )
