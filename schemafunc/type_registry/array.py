# array_type_handler.py
from collections.abc import Mapping, Sequence, Set
from typing import Any, Dict, Type, get_args, get_origin

from schemafunc.exceptions import BareGenericTypeError
from schemafunc.type_registry.registry import (
    TypeHandler,
    register_type_handler,
    resolve_type,
)


def is_representable_as_js_array(typ: Type) -> bool:
    """
    Determines if a given type can be accurately represented as a JavaScript array.

    This function returns true if the provided type holds an ordered sequence of
    elements that can be accurately represented as a JavaScript array. Otherwise,
    it returns false.

    Args:
        typ (Type): The Python data type to evaluate.

    Returns:
        bool: Indicates whether the input type can be represented as a JavaScript array.

    Examples:
        >>> is_representable_as_js_array(list)
        True

        >>> is_representable_as_js_array(str)
        False

    """
    try:
        # Check if it's an iterable type, excluding specific types
        # that don't map well to JS arrays.
        if issubclass(typ, (Sequence, Set)) and not issubclass(
            typ, (str, bytes, bytearray, Mapping)
        ):
            return True
    except TypeError:
        # If the type is not a class, then nothing to check.
        return False
    return False


@register_type_handler
class ArrayTypeHandler(TypeHandler):
    def is_type(self, param_type: Type) -> bool:
        return is_representable_as_js_array(get_origin(param_type) or param_type)

    def resolve(self, param_type: Type) -> Dict[str, Any]:
        item_type = get_args(param_type)
        if item_type:
            resolved_item_type = resolve_type(item_type[0])
        else:
            raise BareGenericTypeError(
                f"Bare generic type {param_type} is not allowed."
            )
        return {"type": "array", "items": resolved_item_type}
