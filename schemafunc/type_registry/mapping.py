# mapping_type_handler.py

from collections.abc import Mapping as AbcMapping
from typing import Any, Dict, Mapping, Type, _TypedDictMeta, get_args, get_origin

from schemafunc.exceptions import UnsupportedTypeError
from schemafunc.type_registry.registry import (
    TypeHandler,
    register_type_handler,
    resolve_type,
)


@register_type_handler
class MappingTypeHandler(TypeHandler):
    def is_type(self, param_type: Type) -> bool:
        origin = get_origin(param_type)
        is_typed_dict = isinstance(param_type, _TypedDictMeta)
        if is_typed_dict:
            return False
        valid_origin = origin in [dict, Mapping, AbcMapping]

        try:
            return valid_origin or issubclass(param_type, AbcMapping)
        except TypeError:
            return False

    def resolve(self, param_type: Type) -> Dict[str, Any]:
        key_type, value_type = get_args(param_type)
        if key_type != str:
            raise UnsupportedTypeError(f"Mapping keys must be strings, not {key_type}")
        return {
            "type": "object",
            "additionalProperties": resolve_type(value_type),
        }
