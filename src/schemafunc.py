import inspect
import typing
from collections.abc import Sequence, Set
from functools import cached_property, wraps

from docstring_parser import Docstring, parse


class FunctionMetadata:
    def __init__(self, func, **schema_kwargs):
        self.func = func
        self.schema_kwargs = schema_kwargs

    @cached_property
    def schema(self):
        return function_to_schema(self.func, **self.schema_kwargs)

    @cached_property
    def openai_tool_kwargs(self):
        return {
            "tools": [self.schema],
            "tool_choice": {
                "type": "function",
                "function": {"name": self.schema["function"]["name"]},
            },
        }


def add_schemafunc(_func=None, **schema_kwargs):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        if not hasattr(wrapper, "function_metadata"):
            wrapper.schemafunc = FunctionMetadata(func, **schema_kwargs)

            # force evaluation of the cached properties so that we raise errors like
            # `NoDocstringError` at definition time
            # TODO: Maybe just drop the cached properties functionality?
            wrapper.schemafunc.openai_tool_kwargs

        return wrapper

    if _func is not None:
        return decorator(_func)
    else:
        return decorator


class NoDocstringError(Exception):
    pass


def function_to_schema(
    func: typing.Callable,
    require_param_descriptions: bool = True,
    allow_bare_generic_types: bool = False,
    ignore_undocumented_params: bool = False,
    ignore_no_docstring: bool = False,
) -> dict:
    signature = inspect.signature(func)
    docstring = parse(func.__doc__)

    if not docstring.short_description:
        if not ignore_no_docstring:
            raise NoDocstringError("The function must have a docstring")

    parameters = process_parameters(
        signature,
        docstring,
        require_param_descriptions,
        allow_bare_generic_types,
        ignore_undocumented_params,
        ignore_no_docstring,
    )
    return generate_schema(func, docstring, parameters, ignore_no_docstring)


class ParameterNotDocumentedError(Exception):
    pass


class ParameterMissingDescriptionError(Exception):
    pass


def process_parameters(
    signature: inspect.Signature,
    docstring: Docstring,
    require_param_descriptions: bool,
    allow_bare_generic_types: bool,
    ignore_undocumented_params: bool,
    ignore_no_docstring: bool,
) -> dict:
    parameters = {}

    for name, param in signature.parameters.items():
        if param.annotation == inspect.Parameter.empty:
            raise ValueError(f"Parameter {name} must have a type annotation")

        param_type = param.annotation
        param_docstring = next(
            (p for p in docstring.params if p.arg_name == name), None
        )

        try:
            param_schema = resolve_type(param_type)
        except BareGenericTypeError:
            if allow_bare_generic_types:
                param_schema = {"type": "array", "items": {}}  # Unspecified item type
            else:
                raise

        if param_docstring is None:
            if not ignore_undocumented_params and not ignore_no_docstring:
                raise ParameterNotDocumentedError(
                    f"Parameter {name} is not documented in the docstring"
                )
        else:
            if require_param_descriptions and not param_docstring.description:
                raise ParameterMissingDescriptionError(
                    f"Parameter {name} is missing a description in the docstring"
                )
            if param_docstring.description:
                param_schema["description"] = param_docstring.description

        if param.default != inspect.Parameter.empty and param.default is not None:
            param_schema["default"] = param.default

        parameters[name] = param_schema

    return parameters


class NoShortDescriptionError(Exception):
    pass


def generate_schema(
    func: typing.Callable,
    docstring: Docstring,
    parameters: dict,
    ignore_no_docstring: bool,
) -> dict:
    if not docstring.short_description and not ignore_no_docstring:
        raise NoShortDescriptionError(
            "The function must have a short description in the docstring"
        )

    schema = {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": docstring.short_description
            if docstring.short_description
            else "",
            "parameters": {
                "type": "object",
                "properties": parameters,
                "required": [
                    name
                    for name, param in inspect.signature(func).parameters.items()
                    if param.default == inspect.Parameter.empty
                ],
            },
        },
    }

    return schema


json_schema_types = {
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


class UnsupportedTypeError(Exception):
    pass


def resolve_type(param_type: typing.Type) -> dict:
    if is_basic_type(param_type):
        return resolve_basic_type(param_type)
    elif is_union_type(param_type):
        return resolve_union_type(param_type)
    elif is_array_type(param_type):
        return resolve_array_type(param_type)
    elif is_literal_type(param_type):
        return resolve_literal_type(param_type)
    else:
        raise UnsupportedTypeError(f"Unsupported type: {param_type}")


def is_basic_type(param_type: typing.Type) -> bool:
    return param_type in json_schema_types


def resolve_basic_type(param_type: typing.Type) -> dict:
    return {"type": json_schema_types[param_type]}


def is_union_type(param_type: typing.Type) -> bool:
    return typing.get_origin(param_type) == typing.Union


def resolve_union_type(param_type: typing.Type) -> dict:
    """
    Resolves a union type into a JSON schema.

    Given a Python type that represents a union (i.e., a type that can be one of
    several types), this function returns a JSON schema that represents the union.

    Args:
        param_type (typing.Type): The union type to resolve.

    Returns:
        dict: A JSON schema representing the union type.

    Examples:
        Resolve a union of int and str:

        >>> import typing
        >>> resolve_union_type(typing.Union[int, str])
        {'type': ['integer', 'string']}

        Resolve a union of bool and None:

        # >>> resolve_union_type(typing.Union[bool, None])
        {'type': ['boolean', 'null']}

        Resolve a union of int, str, and list of int:

        >>> resolve_union_type(typing.Union[int, str, typing.List[int]])
        {'type': ['integer', 'string', 'array'], 'items': {'type': 'integer'}}
    """
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


def is_array_type(param_type: typing.Type) -> bool:
    """
    Determines if the given type is representable as a JavaScript array.

    This function handles both generic types and non-generic types. It uses
    `typing.get_origin` to get the original generic type for generic types,
    and falls back to the input type itself for non-generic types.

    Args:
        param_type (typing.Type): The type to check.

    Returns:
        bool: True if the type is representable as a JavaScript array, False otherwise.

    Examples:
        >>> is_array_type(typing.List[int])
        True
        >>> is_array_type(typing.Tuple[int, str, bool])
        True
        >>> is_array_type(list)
        True
        >>> is_array_type(tuple)
        True
        >>> is_array_type(dict)
        False
        >>> is_array_type(str)
        False
    """
    return is_representable_as_js_array(typing.get_origin(param_type) or param_type)


class BareGenericTypeError(ValueError):
    pass


def resolve_array_type(param_type: typing.Type) -> dict:
    """
    Returns a dictionary describing the given array-like generic type.

    If an unsubscripted generic type (like "list" or "List" without a specified item
    type) is passed to this function, it raises a `BareGenericTypeError`.

    Args:
        param_type (typing.Type): The array-like generic type to be analyzed.

    Returns:

        dict: A dictionary containing the resolved information about the array-like
              generic type. It includes two keys, 'type', and 'items'. 'type' value
              is always 'array', and 'items' value is the resolved item type's name.

    Raises:
        BareGenericTypeError: If the param_type is an unsubscripted generic.

    Example:
        >>> resolve_array_type(typing.List[int])  # `typing` module style
        {'type': 'array', 'items': {'type': 'integer'}}

    Note:
        Be sure to specify the item type when providing the array-like generic type,
        as unsubscripted generics will raise `BareGenericTypeError`.

    """
    item_type = typing.get_args(param_type)
    if item_type:
        resolved_item_type = resolve_type(item_type[0])
    else:
        raise BareGenericTypeError(f"Bare generic type {param_type} is not allowed.")
    return {"type": "array", "items": resolved_item_type}


def is_literal_type(param_type: typing.Type) -> bool:
    return typing.get_origin(param_type) == typing.Literal


class UnsupportedLiteralTypeError(Exception):
    pass


def resolve_literal_type(param_type: typing.Type) -> dict:
    """
    Resolves literal type parameters into structured definitions.

    Given a typing.Type parameter object that is expected to contain Literal values,
    this function extracts these Literal values and structures them into a dictionary
    that represents these values as string type and a list of their enumerated value
    counterparts.

    Args:
        param_type (typing.Type): Expected to be a typing.Literal type containing
            intrinsic literal values (int, float, str, bool, None).

    Returns:
        dict: A dictionary defining the type as 'string' (irrespective of the input
            literal types), and an 'enum' list of values which contains the literal
            values.

    Raises:
        UnsupportedLiteralTypeError: If any of the literal values are not of the
            supported literal types (int, float, str, bool, None).

    Example:
        >>> resolve_literal_type(typing.Literal[1, "two", True, None])
        {'type': 'string', 'enum': [1, 'two', True, None]}
    """
    literal_values = typing.get_args(param_type)
    supported_types = (int, float, str, bool, type(None))
    if all(isinstance(v, supported_types) for v in literal_values):
        return {"type": "string", "enum": list(literal_values)}
    else:
        raise UnsupportedLiteralTypeError(
            f"Unsupported Literal values: {literal_values}"
        )


def is_representable_as_js_array(typ: typing.Type) -> bool:
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
            typ, (str, bytes, bytearray, dict)
        ):
            return True
    except TypeError:
        # If the type is not a class, then nothing to check.
        return False
    return False
