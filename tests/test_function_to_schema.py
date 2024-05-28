from typing import Literal, Optional, Union

import pytest

from schemafunc import (
    BareGenericTypeError,
    NoDocstringError,
    ParameterMissingDescriptionError,
    ParameterNotDocumentedError,
    function_to_schema,
)


def test_only_optional_param():
    def only_optional_param(a: int = None):
        """
        A function with a docstring.

        :param a: The first arg.
        :return:
        """
        pass

    assert function_to_schema(only_optional_param) == {
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


def test_only_int_param():
    def only_int_param(a: int):
        """
        A function with a docstring.

        :param a: The first arg.
        :return:
        """
        pass

    assert function_to_schema(only_int_param) == {
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


def test_only_int_param_numpy_docstring():
    def only_int_param(a: int):
        """
        A function with a docstring.

        Parameters
        ----------
        a : int
            The first arg.

        Returns
        -------
        None
        """
        pass

    assert function_to_schema(only_int_param) == {
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


def test_only_int_param_google_docstring():
    def only_int_param(a: int):
        """
        A function with a docstring.

        Args:
            a (int): The first arg.

        Returns:
            None
        """
        pass

    assert function_to_schema(only_int_param) == {
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


def test_only_built_in_type_params():
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

    assert function_to_schema(only_built_in_type_params) == {
        "type": "function",
        "function": {
            "name": "only_built_in_type_params",
            "description": "An example function with various scalar types.",
            "parameters": {
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "A string parameter.",
                    },
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


def test_only_bare_list_param_allowed_by_default():
    def only_bare_list_param(a: list):
        """
        A function with a docstring.

        :param a: The first arg.
        :return:
        """
        pass

    assert function_to_schema(only_bare_list_param) == {
        "type": "function",
        "function": {
            "name": "only_bare_list_param",
            "description": "A function with a docstring.",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {
                        "type": "array",
                        "description": "The first arg.",
                        "items": {},
                    },
                },
                "required": ["a"],
            },
        },
    }


def test_only_bare_list_param_bare_disallowed():
    def only_bare_list_param(a: list):
        """
        A function with a docstring.

        :param a: The first arg.
        :return:
        """
        pass

    with pytest.raises(BareGenericTypeError) as e:
        function_to_schema(only_bare_list_param, allow_bare_generic_types=False)


def test_get_current_weather():
    def get_current_weather(location: str, format: Literal["celsius", "fahrenheit"]):
        """
        Get the current weather

        example from:
        https://github.com/openai/openai-cookbook/blob/a4054685808487907129db40910a70d2b49fc40c/examples/How_to_call_functions_with_chat_models.ipynb

        :param location: The city and state, e.g. San Francisco, CA
        :param format: The temperature unit to use. Infer this from the users location.
        """
        pass

    assert function_to_schema(get_current_weather) == {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather\n\nexample from:\nhttps://github.com/openai/openai-cookbook/blob/a4054685808487907129db40910a70d2b49fc40c/examples/How_to_call_functions_with_chat_models.ipynb",
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


def test_get_n_day_weather_forecast():
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

    assert function_to_schema(get_n_day_weather_forecast) == {
        "type": "function",
        "function": {
            "name": "get_n_day_weather_forecast",
            "description": "Get an N-day weather forecast\n\nexample from:\nhttps://github.com/openai/openai-cookbook/blob/a4054685808487907129db40910a70d2b49fc40c/examples/How_to_call_functions_with_chat_models.ipynb",
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


def test_no_docstring_disallowed_by_default():
    def no_docstring(a: int, b: str = "default"):
        pass

    with pytest.raises(NoDocstringError):
        function_to_schema(no_docstring)


def test_no_docstring_allowed():
    def no_docstring(a: int, b: str = "default"):
        pass

    assert function_to_schema(
        no_docstring,
        require_all_params_in_doc=False,
        require_descriptions_for_params=False,
        require_short_description=False,
    ) == {
        "type": "function",
        "function": {
            "name": "no_docstring",
            "description": "",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {
                        "type": "integer",
                    },
                    "b": {
                        "type": "string",
                        "default": "default",
                    },
                },
                "required": ["a"],
            },
        },
    }


def test_param_not_documented_disallowed():
    def param_not_documented(a: int, no_doc_here: str):
        """
        A function with a docstring.

        :param a: The first arg.
        """
        pass

    with pytest.raises(ParameterNotDocumentedError) as e:
        function_to_schema(param_not_documented)

    # assert that the error message ends with "docstring: b"
    assert str(e.value).endswith("docstring: no_doc_here")


def test_param_not_documented_allowed():
    def param_not_documented(a: int, no_doc_here: str):
        """
        A function with a docstring.

        :param a: The first arg.
        """
        pass

    assert function_to_schema(
        param_not_documented,
        require_all_params_in_doc=False,
        require_descriptions_for_params=False,
        require_short_description=False,
    ) == {
        "type": "function",
        "function": {
            "name": "param_not_documented",
            "description": "A function with a docstring.",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {
                        "type": "integer",
                        "description": "The first arg.",
                    },
                    "no_doc_here": {
                        "type": "string",
                    },
                },
                "required": ["a", "no_doc_here"],
            },
        },
    }


def test_param_not_described_disallowed():
    def param_not_described(a: int, b: str):
        """
        A function with a docstring.

        :param a: The first arg.
        :param b:
        """
        pass

    with pytest.raises(ParameterMissingDescriptionError) as e:
        function_to_schema(param_not_described)

    # assert that the error message ends with "docstring: b"
    assert str(e.value).endswith("docstring: b")


def test_param_not_described_allowed():
    def param_not_described(a: int, b: str):
        """
        A function with a docstring.

        :param a: The first arg.
        :param b:
        """
        pass

    assert function_to_schema(
        param_not_described,
        require_descriptions_for_params=False,
    ) == {
        "type": "function",
        "function": {
            "name": "param_not_described",
            "description": "A function with a docstring.",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {
                        "type": "integer",
                        "description": "The first arg.",
                    },
                    "b": {
                        "type": "string",
                    },
                },
                "required": ["a", "b"],
            },
        },
    }


def test_has_union_with_none():
    def has_union_with_none(a: Union[int, None]):
        """
        Uses a Union with None.

        :param a: The first arg.
        :return:
        """
        pass

    assert function_to_schema(has_union_with_none) == {
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


def test_has_union_with_none_and_default_value():
    def has_union_with_none_and_default_value(a: Union[int, None] = None):
        """
        Uses a Union with None and a default value of None.

        :param a: The first arg.
        :return:
        """
        pass

    assert function_to_schema(has_union_with_none_and_default_value) == {
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


def test_has_none_as_default_value_without_corresponding_type_annotation():
    def has_none_as_default_value_without_corresponding_type_annotation(a: int = None):
        """
        Uses a default value of None without a corresponding type annotation.


        This isn't technically correct, but it's a common pattern in Python.  To be
        correct, the type annotation should be Union[int, None] or Optional[int].

        :param a: The first arg.
        :return:
        """
        pass

    assert function_to_schema(
        has_none_as_default_value_without_corresponding_type_annotation
    ) == {
        "type": "function",
        "function": {
            "name": "has_none_as_default_value_without_corresponding_type_annotation",
            "description": "Uses a default value of None without a corresponding type annotation.\n\nThis isn't technically correct, but it's a common pattern in Python.  To be\ncorrect, the type annotation should be Union[int, None] or Optional[int].",
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


def test_has_optional_type_annotation_without_default_none():
    def has_optional_type_annotation_without_default_none(a: Optional[int]):
        """
        Uses an Optional type annotation.


        This (incorrectly, IMO) uses Optional[int] without providing a default value
        of None. A more correct way if you don't want a default value would be to use
        Union[int, None], which conveys the intended meaning more clearly.

        :param a: The first arg.
        :return:
        """
        pass

    assert function_to_schema(has_optional_type_annotation_without_default_none) == {
        "type": "function",
        "function": {
            "name": "has_optional_type_annotation_without_default_none",
            "description": "Uses an Optional type annotation.\n\nThis (incorrectly, IMO) uses Optional[int] without providing a default value\nof None. A more correct way if you don't want a default value would be to use\nUnion[int, None], which conveys the intended meaning more clearly.",
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


def test_has_optional_type_annotation_with_default_none():
    def has_optional_type_annotation_with_default_none(a: Optional[int] = None):
        """
        Uses an Optional type annotation with a default value of None.

        :param a: The first arg.
        :return:
        """
        pass

    assert function_to_schema(has_optional_type_annotation_with_default_none) == {
        "type": "function",
        "function": {
            "name": "has_optional_type_annotation_with_default_none",
            "description": "Uses an Optional type annotation with a default value of None.",
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
