import typing
from typing import Literal

import pytest

from src.schemafunc import (
    BareGenericTypeError,
    NoDocstringError,
    ParameterMissingDescriptionError,
    ParameterNotDocumentedError,
    function_to_schema,
)


def only_optional_param(a: int = None):
    """
    A function with a docstring.

    :param a: The first arg.
    :return:
    """
    pass


only_optional_param.expected = {
    "type": "function",
    "function": {
        "name": "only_optional_param",
        "description": "A function with a docstring.",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {
                    "type": "integer",
                    "description": "The first arg.",
                },
            },
            "required": [],
        },
    },
}


def only_int_param(a: int):
    """
    A function with a docstring.

    :param a: The first arg.
    :return:
    """
    pass


only_int_param.expected = {
    "type": "function",
    "function": {
        "name": "only_int_param",
        "description": "A function with a docstring.",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {
                    "type": "integer",
                    "description": "The first arg.",
                },
            },
            "required": ["a"],
        },
    },
}


def only_int_param_numpy_docstring(a: int):
    """
    A function with a docstring.

    Parameters
    ----------
    a : int
        The first arg.
    """
    pass


only_int_param_numpy_docstring.expected = {
    "type": "function",
    "function": {
        "name": "only_int_param_numpy_docstring",
        "description": "A function with a docstring.",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {
                    "type": "integer",
                    "description": "The first arg.",
                },
            },
            "required": ["a"],
        },
    },
}


def only_int_param_google_docstring(a: int):
    """
    A function with a docstring.

    Args:
        a: The first arg.
    """
    pass


only_int_param_google_docstring.expected = {
    "type": "function",
    "function": {
        "name": "only_int_param_google_docstring",
        "description": "A function with a docstring.",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {
                    "type": "integer",
                    "description": "The first arg.",
                },
            },
            "required": ["a"],
        },
    },
}


def only_built_in_type_params(
    param1: str, param2: int, param3: float, param4: bool, param5: None
):
    """
    An example function with various scalar types.

    :param param1: A string parameter.
    :param param2: An integer parameter.
    :param param3: A float parameter.
    :param param4: A boolean parameter.
    :param param5: A None parameter.
    """
    pass


only_built_in_type_params.expected = {
    "type": "function",
    "function": {
        "name": "only_built_in_type_params",
        "description": "An example function with various scalar types.",
        "parameters": {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "A string parameter."},
                "param2": {
                    "type": "integer",
                    "description": "An integer parameter.",
                },
                "param3": {
                    "type": "number",
                    "description": "A float parameter.",
                },
                "param4": {
                    "type": "boolean",
                    "description": "A boolean parameter.",
                },
                "param5": {
                    "type": "null",
                    "description": "A None parameter.",
                },
            },
            "required": ["param1", "param2", "param3", "param4", "param5"],
        },
    },
}


def only_bare_list_param(a: typing.List):
    """
    A function with a docstring.

    :param a: The first arg.
    :return:
    """
    pass


only_bare_list_param.expected = {
    "__fts_error__": BareGenericTypeError,
}


def only_list_param(a: typing.List[str]):
    """
    A function with a docstring.

    :param a: The first arg.
    :return:
    """
    pass


only_list_param.expected = {
    "type": "function",
    "function": {
        "name": "only_list_param",
        "description": "A function with a docstring.",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {
                    "type": "array",
                    "description": "The first arg.",
                    "items": {"type": "string"},
                },
            },
            "required": ["a"],
        },
    },
}


def get_current_weather(location: str, format: Literal["celsius", "fahrenheit"]):
    """
    Get the current weather

    example from:
    https://github.com/openai/openai-cookbook/blob/a4054685808487907129db40910a70d2b49fc40c/examples/How_to_call_functions_with_chat_models.ipynb

    :param location: The city and state, e.g. San Francisco, CA
    :param format: The temperature unit to use. Infer this from the users location.
    """


get_current_weather.expected = {
    "type": "function",
    "function": {
        "name": "get_current_weather",
        "description": "Get the current weather",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA",
                },
                "format": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "The temperature unit to use. Infer this from the users location.",
                },
            },
            "required": ["location", "format"],
        },
    },
}


def get_n_day_weather_forecast(
    location: str, format: Literal["celsius", "fahrenheit"], num_days: int
):
    """
    Get an N-day weather forecast

    example from:
    https://github.com/openai/openai-cookbook/blob/a4054685808487907129db40910a70d2b49fc40c/examples/How_to_call_functions_with_chat_models.ipynb

    :param location: The city and state, e.g. San Francisco, CA
    :param format: The temperature unit to use. Infer this from the users location.
    :param num_days: The number of days to forecast
    """


get_n_day_weather_forecast.expected = {
    "type": "function",
    "function": {
        "name": "get_n_day_weather_forecast",
        "description": "Get an N-day weather forecast",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA",
                },
                "format": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "The temperature unit to use. Infer this from the users location.",
                },
                "num_days": {
                    "type": "integer",
                    "description": "The number of days to forecast",
                },
            },
            "required": ["location", "format", "num_days"],
        },
    },
}


def no_docstring(a: int):
    pass


no_docstring.expected = {
    "__fts_error__": NoDocstringError,
}


def param_not_documented(a: int):
    """
    hi
    """


param_not_documented.expected = {
    "__fts_error__": ParameterNotDocumentedError,
}


def param_not_described(a: int):
    """
    The param isn't described.

    :param a:
    """


param_not_described.expected = {
    "__fts_error__": ParameterMissingDescriptionError,
}


def has_union_with_none(a: typing.Union[int, None]):
    """
    Uses a Union with None.

    :param a: The first arg.
    :return:
    """
    pass


has_union_with_none.expected = {
    "type": "function",
    "function": {
        "name": "has_union_with_none",
        "description": "Uses a Union with None.",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {
                    "type": ["integer", "null"],
                    "description": "The first arg.",
                },
            },
            "required": ["a"],
        },
    },
}


def has_union_with_none_and_default_value(a: typing.Union[int, None] = None):
    """
    Uses a Union with None and a default value of None.

    :param a: The first arg.
    :return:
    """
    pass


has_union_with_none_and_default_value.expected = {
    "type": "function",
    "function": {
        "name": "has_union_with_none_and_default_value",
        "description": "Uses a Union with None and a default value of None.",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {
                    "type": ["integer", "null"],
                    "description": "The first arg.",
                },
            },
            "required": [],
        },
    },
}


def has_none_as_default_value_without_corresponding_type_annotation(a: int = None):
    """
    Uses a default value of None without a corresponding type annotation.


    This isn't technically correct, but it's a common pattern in Python.  To be
    correct, the type annotation should be Union[int, None] or Optional[int].

    :param a: The first arg.
    :return:
    """
    pass


has_none_as_default_value_without_corresponding_type_annotation.expected = {
    "type": "function",
    "function": {
        "name": "has_none_as_default_value_without_corresponding_type_annotation",
        "description": "Uses a default value of None without a corresponding type annotation.",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {
                    "type": "integer",
                    "description": "The first arg.",
                },
            },
            "required": [],
        },
    },
}


def has_optional_type_annotation_without_default_none(a: typing.Optional[int]):
    """
    Uses an Optional type annotation.


    This is (incorrectly, IMO) uses Optional[int] without providing a default value
    of None. A more correct way if you don't want a default value would be to use
    Union[int, None], which conveys the intended meaning more clearly.

    :param a: The first arg.
    :return:
    """
    pass


has_optional_type_annotation_without_default_none.expected = {
    "type": "function",
    "function": {
        "name": "has_optional_type_annotation_without_default_none",
        "description": "Uses an Optional type annotation.",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {
                    "type": ["integer", "null"],
                    "description": "The first arg.",
                },
            },
            "required": ["a"],
        },
    },
}


def test_has_optional_type_annotation_with_default_none(a: typing.Optional[int] = None):
    """
    Uses an Optional type annotation with a default value of None.

    :param a: The first arg.
    :return:
    """
    pass


test_has_optional_type_annotation_with_default_none.expected = {
    "type": "function",
    "function": {
        "name": "test_has_optional_type_annotation_with_default_none",
        "description": "Uses an Optional type annotation with a default value of None.",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {
                    "type": ["integer"],
                    "description": "The first arg.",
                },
            },
            "required": [],
        },
    },
}


@pytest.mark.parametrize(
    "function",
    [
        only_optional_param,
        only_int_param,
        only_int_param_numpy_docstring,
        only_int_param_google_docstring,
        only_list_param,
        only_bare_list_param,
        only_built_in_type_params,
        get_current_weather,
        get_n_day_weather_forecast,
        no_docstring,
        param_not_documented,
        param_not_described,
        has_union_with_none,
        has_union_with_none_and_default_value,
        has_none_as_default_value_without_corresponding_type_annotation,
        has_optional_type_annotation_without_default_none,
    ],
)
def test_function_to_schema(function):
    fts_args = function.expected.get("__fts_args__", {})
    expected_error = function.expected.get("__fts_error__", None)

    if expected_error:
        with pytest.raises(expected_error):
            function_to_schema(function, **fts_args)
    else:
        assert function_to_schema(function, **fts_args) == function.expected
