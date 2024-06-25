import functools
import inspect
import typing
import warnings
from functools import wraps

from docstring_parser import Docstring, parse

from schemafunc.exceptions import (
    BareGenericTypeError,
    NoDocstringError,
    NoShortDescriptionError,
    ParameterMissingDescriptionError,
    ParameterNotDocumentedError,
)
from .type_registry import resolve_type

P = typing.ParamSpec("P")
R = typing.TypeVar("R", covariant=True)


def generate_openai_schema(func: typing.Callable) -> dict:
    return function_to_schema(func)


def generate_anthropic_schema(func: typing.Callable) -> dict:
    openai_schema = function_to_schema(func)
    anthropic_schema = {
        "name": openai_schema["function"]["name"],
        "description": openai_schema["function"]["description"],
        "input_schema": openai_schema["function"]["parameters"],
    }
    # Remove the old keys to move data instead of copying
    del openai_schema["function"]["parameters"]
    del openai_schema["function"]["name"]
    del openai_schema["function"]["description"]
    return anthropic_schema


class OpenAISchema:
    def __init__(self, func: typing.Callable):
        self.func = func

    @functools.cached_property
    def schema(self) -> dict:
        return generate_openai_schema(self.func)


class AnthropicSchema:
    def __init__(self, func: typing.Callable):
        self.func = func

    @functools.cached_property
    def schema(self) -> dict:
        return generate_anthropic_schema(self.func)


class FunctionMetadata:
    def __init__(self, func: typing.Callable[P, R], **schema_kwargs: typing.Any):
        self.func = func
        self.schema_kwargs = schema_kwargs
        self.openai = OpenAISchema(func)
        self.anthropic = AnthropicSchema(func)

    @functools.cached_property
    def schema(self) -> dict:
        warnings.warn(
            "schema is deprecated, use openai.schema instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return function_to_schema(self.func, **self.schema_kwargs)

    @functools.cached_property
    def openai_tool_kwargs(self) -> dict:
        return {
            "tools": [self.schema],
            "tool_choice": {
                "type": "function",
                "function": {"name": self.schema.get("function", {}).get("name")},
            },
        }


class HasSchemaFuncAttribute(typing.Protocol[P, R]):
    schemafunc: FunctionMetadata

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R: ...


DecType = typing.Callable[[typing.Callable[P, R]], HasSchemaFuncAttribute[P, R]]


@typing.overload
def add_schemafunc(
    _func: None = None, **schema_kwargs: typing.Any
) -> DecType[P, R]: ...


@typing.overload
def add_schemafunc(
    _func: typing.Callable[P, R], **schema_kwargs: typing.Any
) -> HasSchemaFuncAttribute[P, R]: ...


def add_schemafunc(
    _func: typing.Optional[typing.Callable[P, R]] = None, **schema_kwargs: typing.Any
) -> typing.Union[DecType[P, R], HasSchemaFuncAttribute[P, R]]:
    def decorator(func: typing.Callable[P, R]) -> HasSchemaFuncAttribute[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            return func(*args, **kwargs)

        setattr(wrapper, "schemafunc", FunctionMetadata(func, **schema_kwargs))

        # force evaluation so that errors are caught early
        _ = wrapper.schemafunc.schema

        return typing.cast(HasSchemaFuncAttribute[P, R], wrapper)

    if _func is not None:
        return decorator(_func)
    else:
        return decorator


def function_to_schema(
    func: typing.Callable,
    /,
    ignore_args: typing.Sequence[str] = (),
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
        ignore_args (typing.Sequence[str], optional): A sequence of parameter names
            to ignore when generating the schema. Defaults to ().
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
    filtered_parameters = {
        name: param
        for name, param in signature.parameters.items()
        if name not in ignore_args
    }
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
        filtered_parameters,
        docstring,
        allow_bare_generic_types,
    )
    return generate_schema(func, docstring, parameters, ignore_args)


def process_parameters(
    signature: typing.Mapping[str, inspect.Parameter],
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
        signature (typing.Mapping[str, inspect.Parameter]): A mapping of parameter
            names to their corresponding inspect.Parameter objects.
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
        >>> process_parameters(sig.parameters, doc, allow_bare_generic_types=False)
        {'param': {'type': 'integer', 'description': 'The first parameter.'}}

    Note:
        Always provide type annotations for parameters in the function's
        signature. The function relies on these annotations to accurately define
        the JSON schema. The function also leverages the related documentation
        within the function's docstring to enhance the precision of the results,
        providing expanded context when required.
    """
    parameters = {}

    for name, param in signature.items():
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


def generate_schema(
    func: typing.Callable,
    docstring: Docstring,
    parameters: dict,
    ignore_args: typing.Sequence[str] = (),
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
                    and name not in ignore_args
                ],
            },
        },
    }

    return schema
