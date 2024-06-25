from typing import Any, Dict, Type, TypedDict, _TypedDictMeta, get_type_hints

from schemafunc.type_registry.registry import (
    TypeHandler,
    register_type_handler,
    resolve_type,
)


@register_type_handler
class TypedDictTypeHandler(TypeHandler):
    def is_type(self, param_type: Type) -> bool:
        return isinstance(param_type, _TypedDictMeta)

    def resolve(self, param_type: Type[TypedDict]) -> Dict[str, Any]:
        properties = {}
        required = []
        for field_name, field_type in get_type_hints(param_type).items():
            properties[field_name] = resolve_type(field_type)
            if field_name in param_type.__required_keys__:
                required.append(field_name)
        return {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        }
