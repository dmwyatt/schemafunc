from abc import ABC
from typing import Any, Dict, Type

from schemafunc.exceptions import UnsupportedTypeError


class TypeHandler(ABC):
    def is_type(self, param_type: Type) -> bool:
        ...

    def resolve(self, param_type: Type) -> Dict[str, Any]:
        ...


type_registry: Dict[TypeHandler, TypeHandler] = {}


def register_type_handler(handler_class: Type[TypeHandler]):
    handler_instance = handler_class()
    type_registry[handler_instance] = handler_instance
    return handler_class


def resolve_type(param_type: Type) -> Dict[str, Any]:
    """
    Resolves a Python type into a JSON Schema dictionary.

    This function takes a Python type (such as `int`, `str`, `Union`,
    `List`, `Dict`, `TypedDict`, etc.) and returns a dictionary
    representing the equivalent JSON Schema type.

    Args:
        param_type (Type): The Python type to resolve.

    Returns:
        dict: A dictionary representing the JSON Schema equivalent of the input type.

    Raises:
        UnsupportedTypeError: If the input type is not supported by the function.

    Examples:
        >>> from typing import *
        >>> resolve_type(int)
        {'type': 'integer'}
    """
    # special cases:
    if param_type is Any:
        return {}
    for handler in type_registry.values():
        if handler.is_type(param_type):
            return handler.resolve(param_type)
    raise UnsupportedTypeError(f"Unsupported type: {param_type}")
