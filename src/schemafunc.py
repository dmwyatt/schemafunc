import inspect
import types
import typing
from collections.abc import Sequence, Set
from functools import wraps
from types import MappingProxyType

from docstring_parser import Docstring, parse


class FunctionMetadata:
    def __init__(
        self, func: typing.Callable[..., typing.Any], **schema_kwargs: typing.Any
    ):
        self.func = func
        self.schema_kwargs = schema_kwargs
        self.schema = function_to_schema(self.func, **self.schema_kwargs)
        self.openai_tool_kwargs = {
            "tools": [self.schema],
            "tool_choice": {
                "type": "function",
                "function": {"name": self.schema.get("function", {}).get("name")},
            },
        }


P = typing.ParamSpec("P")
R = typing.TypeVar("R", covariant=True)


class HasSchemaFuncAttribute(typing.Protocol[P, R]):
    schemafunc: FunctionMetadata

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        ...


DecType = typing.Callable[[typing.Callable[P, R]], HasSchemaFuncAttribute[P, R]]


def add_schemafunc(
    _func: typing.Optional[typing.Callable[P, R]] = None, **schema_kwargs: typing.Any
) -> typing.Union[DecType[P, R], HasSchemaFuncAttribute[P, R]]:
    def decorator(func: typing.Callable[P, R]) -> HasSchemaFuncAttribute[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            return func(*args, **kwargs)

        setattr(wrapper, "schemafunc", FunctionMetadata(func, **schema_kwargs))

        return typing.cast(HasSchemaFuncAttribute[P, R], wrapper)

    if _func is not None:
        return decorator(_func)
    else:
        return decorator


class NoDocstringError(Exception):
    pass


def function_to_schema(
    func: typing.Callable,
    require_all_params_in_doc: bool = True,
    require_descriptions_for_params: bool = True,
    allow_bare_generic_types: bool = True,
    require_short_description: bool = True,
) -> dict:
    """
    Generates a JSON schema from a given function.

    The function's parameters and their types, as well as the descriptions provided
    in the function's docstring, are included in the resulting schema. This provides
    a machine-readable definition of the function's expected inputs and behaviors.

    Parameters:
        func (typing.Callable): The function to be converted into a schema.
        require_all_params_in_doc (bool, optional): If True, an exception is raised
            if not all parameters are documented. Defaults to True.
        require_descriptions_for_params (bool, optional): If True, an exception is
            raised if a documented parameter lacks a description. Defaults to True.
        allow_bare_generic_types (bool, optional): If True, bare generic types such
            as List, Dict are allowed. Defaults to True.
        require_short_description (bool, optional): If True, an exception is raised
            if the function docstring lacks a short description. Defaults to True.

    Returns:
        dict: A representation of the function as a JSON schema.

    Raises:
        NoDocstringError: Raised if the function lacks a docstring and
            require_all_params_in_doc is True.
        NoShortDescriptionError: Raised if function docstring lacks a short
            description and require_short_description is True.
        ValueError: Raised if a parameter lacks a type annotation.
        BareGenericTypeError: Raised if a parameter has a bare generic type and
            allow_bare_generic_types is False.
        ParameterNotDocumentedError: Raised if a parameter is not documented in the
            docstring and require_all_params_in_doc is True.
        ParameterMissingDescriptionError: Raised if a parameter is documented but
            lacks a description and require_descriptions_for_params is True.

    Examples:
        >>> def example_function(param1: int):
        ...    '''
        ...    Simple example function.
        ...    Args:
        ...        param1 (int): The first parameter.
        ...    '''
        ...    pass


        >>> function_to_schema(example_function)
        {'type': 'function', 'function': {'name': 'example_function', 'description': 'Simple example function.', 'parameters': {'type': 'object', 'properties': {'param1': {'type': 'integer', 'description': 'The first parameter.'}}, 'required': ['param1']}}}
    """
    signature = inspect.signature(func)
    docstring = parse(func.__doc__) if func.__doc__ else None

    if (
        require_all_params_in_doc
        or require_descriptions_for_params
        or require_short_description
    ) and docstring is None:
        raise NoDocstringError("The function must have a docstring")

    if require_short_description and not docstring.short_description:
        raise NoShortDescriptionError(
            "The function must have a short description in the docstring"
        )

    if require_all_params_in_doc and signature.parameters:
        # list of missing parameters. Missing if not in docstring
        missing_params = [
            param_name
            for param_name in signature.parameters
            if param_name not in [p.arg_name for p in getattr(docstring, "params", [])]
        ]
        if missing_params:
            raise ParameterNotDocumentedError(
                "The following parameters are not documented in the docstring: "
                + ", ".join(missing_params)
            )

    if require_descriptions_for_params:
        # list of parameters with missing descriptions
        missing_desc_params = [
            param.arg_name for param in docstring.params if not param.description
        ]

        if missing_desc_params:
            raise ParameterMissingDescriptionError(
                f"The following parameters are missing descriptions in the docstring: {', '.join(missing_desc_params)}"
            )

    parameters = process_parameters(
        signature,
        docstring,
        allow_bare_generic_types,
    )
    return generate_schema(func, docstring, parameters)


class ParameterNotDocumentedError(Exception):
    pass


class ParameterMissingDescriptionError(Exception):
    pass


def process_parameters(
    signature: inspect.Signature,
    docstring: Docstring,
    allow_bare_generic_types: bool,
) -> typing.Dict[str, typing.Any]:
    """
    Generates JSON schema representation of the parameters of a function.

    This function systematically processes the parameters of a given function,
    guided by their type annotations and any related documentation provided
    within the function's docstring, and constructs a comprehensive JSON schema
    representation.

    Parameters:
        signature (inspect.Signature): A Signature object of the function
            to process.
        docstring (Docstring): A parsed docstring object which includes
            parameter's documentation.
        allow_bare_generic_types (bool): A boolean parameter that indicates
            whether to allow bare generic types (like List, Dict) without a
            specific item type. If True, it will instantiate the item type
            as an empty object. If False, it will raise a BareGenericTypeError
            for any parameter having a bare generic type.

    Returns:
        dict: A dictionary object that represents the JSON schema of the
            parameters of the function. Each entry represents a parameter,
            with its name as the key and the associated JSON schema as the
            value.

    Raises:
        ValueError: If a parameter lacks a type annotation.
        BareGenericTypeError: If allow_bare_generic_types is False and a
            parameter has a bare generic type.

    Example:
        >>> from inspect import signature
        >>> from docstring_parser import parse

        >>> def example_function(param: int):
        ...     '''
        ...     Example function.
        ...
        ...     Args:
        ...         param: The first parameter.
        ...     '''
        ...     pass
        >>> sig = signature(example_function)
        >>> doc = parse(example_function.__doc__)
        >>> process_parameters(sig, doc, allow_bare_generic_types=False)
        {'param': {'type': 'integer', 'description': 'The first parameter.'}}

    Note:
        Always provide type annotations for parameters in the function's
        signature. The function relies on these annotations to accurately define
        the JSON schema. The function also leverages the related documentation
        within the function's docstring to enhance the precision of the results,
        providing expanded context when required.
    """
    parameters = {}

    for name, param in signature.parameters.items():
        if param.annotation == inspect.Parameter.empty:
            raise ValueError(f"Parameter {name} must have a type annotation")

        param_type = param.annotation
        param_docstring = (
            next((p for p in docstring.params if p.arg_name == name), None)
            if docstring
            else None
        )

        try:
            param_schema = resolve_type(param_type)
        except BareGenericTypeError:
            if allow_bare_generic_types:
                param_schema = {"type": "array", "items": {}}  # Unspecified item type
            else:
                raise

        if param_docstring and param_docstring.description:
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
) -> dict:
    schema = {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": getattr(docstring, "description", "").strip(),
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


class UnsupportedTypeError(Exception):
    pass


def resolve_type(param_type: typing.Type) -> dict:
    """
    Resolves a Python type into a JSON Schema dictionary.

    This function takes a Python type (such as `int`, `str`, `typing.Union`,
    `typing.List`, `typing.Dict`, `typing.TypedDict`, etc.) and returns a dictionary
    representing the equivalent JSON Schema type.

    Args:
        param_type (typing.Type): The Python type to resolve.

    Returns:
        dict: A dictionary representing the JSON Schema equivalent of the input type.

    Raises:
        UnsupportedTypeError: If the input type is not supported by the function.

    Examples:
        >>> resolve_type(int)
        {'type': 'integer'}

        >>> resolve_type(typing.List[str])
        {'type': 'array', 'items': {'type': 'string'}}

        >>> resolve_type(typing.Union[int, str])
        {'type': ['integer', 'string']}

        >>> resolve_type(typing.Dict[str, int])
        {'type': 'object', 'additionalProperties': {'type': 'integer'}}

        >>> class MyTypedDict(TypedDict):
        ...     name: str
        ...     age: int
        ...
        >>> resolve_type(MyTypedDict)
        {'type': 'object', 'properties': {'name': {'type': 'string'}, 'age': {'type': 'integer'}}, 'required': ['name', 'age'], 'additionalProperties': False}

    The function supports the following types:

    - Basic types (`int`, `float`, `str`, `bool`, `None`): These are converted to the
      corresponding JSON Schema types (`'integer'`, `'number'`, `'string'`,
      `'boolean'`, `'null'`).

    - Union types (`typing.Union`): These are converted to a JSON Schema type array,
      where each element represents one of the types in the union.

    - Array types (`typing.List`, `typing.Tuple`, `typing.Set`, etc.): These are
      converted to a JSON Schema `'array'` type, with the `items` property
      representing the type of the array elements.

    - Literal types (`typing.Literal`): These are converted to a JSON Schema
      `'string'` type, with an `enum` property listing the permitted literal values.

    - Dictionary types (`typing.Dict`): These are converted to a JSON Schema
      `'object'` type, with the `additionalProperties` property representing the
      type of the dictionary values.

    - TypedDict types (`typing.TypedDict`): These are converted to a JSON Schema
      `'object'` type, with the `properties` property representing the fields of the
      TypedDict and their types, the `required` property listing the required fields,
      and `additionalProperties` set to `False`.
    """
    if param_type is typing.Any:
        return {}
    if is_basic_type(param_type):
        return resolve_basic_type(param_type)
    elif is_union_type(param_type):
        return resolve_union_type(param_type)
    elif is_array_type(param_type):
        return resolve_array_type(param_type)
    elif is_literal_type(param_type):
        return resolve_literal_type(param_type)
    elif is_typed_dict(param_type):
        return resolve_typed_dict(param_type)
    elif is_dict_type(param_type):
        return resolve_dict_type(param_type)

    else:
        raise UnsupportedTypeError(f"Unsupported type: {param_type}")


def is_basic_type(param_type: typing.Type) -> bool:
    return param_type in JSON_SCHEMA_TYPES


def resolve_basic_type(param_type: typing.Type) -> dict:
    return {"type": JSON_SCHEMA_TYPES[param_type]}


def is_union_type(param_type: typing.Type) -> bool:
    return typing.get_origin(param_type) in [typing.Union, types.UnionType]


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


def is_dict_type(param_type: typing.Type) -> bool:
    return typing.get_origin(param_type) == dict


def resolve_dict_type(param_type: typing.Type) -> dict:
    """
    Resolves a dictionary type into a JSON schema.

    This function expects the key type of the dictionary to be a string, as required
    by the JSON specification. If the key type is not a string, a UnsupportedTypeError is raised.
    The value type is resolved using the `resolve_type` function and included in the schema.

    Args:
        param_type (typing.Type): The dictionary type to resolve.

    Returns:
        dict: A JSON schema representing the dictionary type.

    Raises:
        UnsupportedTypeError: If the key type of the dictionary is not a string.
    """
    key_type, value_type = typing.get_args(param_type)
    if key_type != str:
        raise UnsupportedTypeError(f"Dictionary keys must be strings, not {key_type}")
    return {
        "type": "object",
        "additionalProperties": resolve_type(value_type),
    }


def is_typed_dict(param_type: typing.Type) -> bool:
    return isinstance(param_type, typing._TypedDictMeta)


def resolve_typed_dict(param_type: typing.Type[typing.TypedDict]) -> dict:
    properties = {}
    required = []
    for field_name, field_type in param_type.__annotations__.items():
        properties[field_name] = resolve_type(field_type)
        if field_name in param_type.__required_keys__:
            required.append(field_name)
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }
