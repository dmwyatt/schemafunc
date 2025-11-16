import collections
import typing
from unittest.mock import ANY, patch

import pytest

from schemafunc.exceptions import (
    NoDocstringError,
    UnsupportedLiteralTypeError,
    UnsupportedTypeError,
)
from schemafunc.schemafunc import (
    add_schemafunc,
)
from schemafunc.type_registry import resolve_type
from schemafunc.type_registry.array import is_representable_as_js_array


@pytest.mark.parametrize(
    "typ, expected",
    [
        (list, True),
        (int, False),
        (tuple, True),
        (set, True),
        (str, False),
        (collections.deque, True),
        (bytearray, False),
        (range, True),
        (dict, False),
        (collections.OrderedDict, False),
    ],
)
def test_is_representable_as_js_array(typ, expected):
    assert is_representable_as_js_array(typ) == expected


@patch("schemafunc.schemafunc.function_to_schema")
def test_decorator_passes_arguments_correctly(mock_function_to_schema):
    # Decorator is applied in a traditional way
    @add_schemafunc(require_param_descriptions=False, allow_bare_generic_types=True)
    def test_function(a: int):
        """
        Test function for decorator argument passing.

        :param a: An int parameter.
        :return: Nothing.
        """
        pass

    test_function.schemafunc.openai.schema

    # Check that function_to_schema was called correctly
    mock_function_to_schema.assert_called_once_with(
        ANY, require_param_descriptions=False, allow_bare_generic_types=True
    )


def test_decorator_does_not_modify_function_behavior():
    @add_schemafunc
    def function_behavior(a: int):
        """
        da func

        :param a: da param
        :return:
        """
        return a * 2

    assert function_behavior(10) == 20, (
        "The function should return the correct result after being decorated"
    )


def test_decorator_error_propagation():
    with pytest.raises(NoDocstringError):

        @add_schemafunc
        def error_function(a: int):
            pass


def test_decorator_applies_schemafunc():
    @add_schemafunc
    def sample_function(a: int, b: str = "default"):
        """
        A sample function for testing.

        :param a: The first parameter.
        :param b: The second parameter, optional.
        :return: Nothing.
        """
        pass

    assert hasattr(sample_function, "schemafunc"), (
        "schemafunc should be attached to the function"
    )
    assert hasattr(sample_function.schemafunc, "openai"), (
        "OpenAI schema should be attached to the function"
    )
    assert hasattr(sample_function.schemafunc, "openai_tool_kwargs"), (
        "Function should be attached to the function"
    )


def test_decorator_applies_openai_tool_kwargs():
    @add_schemafunc
    def sample_function(a: int, b: str = "default"):
        """
        A sample function for testing.

        :param a: The first parameter.
        :param b: The second parameter, optional.
        :return: Nothing.
        """
        pass

    assert sample_function.schemafunc.openai_tool_kwargs == {
        "tools": [sample_function.schemafunc.openai.schema],
        "tool_choice": {
            "type": "function",
            "function": {
                "name": sample_function.schemafunc.openai.schema["function"]["name"]
            },
        },
    }


def test_deprecated_schema_property_raises_warning():
    @add_schemafunc
    def sample_function(a: int):
        """
        A sample function for testing.

        :param a: The first parameter.
        :return: Nothing.
        """
        pass

    # Test that accessing .schema raises a DeprecationWarning
    with pytest.warns(
        DeprecationWarning, match="schema is deprecated, use openai.schema instead"
    ):
        deprecated_schema = sample_function.schemafunc.schema

    # Verify it returns the same schema as the new property
    assert deprecated_schema == sample_function.schemafunc.openai.schema
    
    # Subsequent accesses return the cached value without triggering another warning
    deprecated_schema_again = sample_function.schemafunc.schema
    assert deprecated_schema_again == deprecated_schema


def test_numpy_style_docstring():
    @add_schemafunc
    def sample_function(a: int, b: str = "default"):
        """
        A sample function for testing.

        Parameters
        ----------
        a : int
            The first parameter.
        b : str, optional
            The second parameter, optional.

        Returns
        -------
        None
        """
        pass

    assert sample_function.schemafunc.openai.schema == {
        "function": {
            "description": "A sample function for testing.",
            "name": "sample_function",
            "parameters": {
                "properties": {
                    "a": {"description": "The first parameter.", "type": "integer"},
                    "b": {
                        "default": "default",
                        "description": "The second parameter, optional.",
                        "type": "string",
                    },
                },
                "required": ["a"],
                "type": "object",
            },
        },
        "type": "function",
    }


def test_google_style_docstring():
    @add_schemafunc
    def sample_function(a: int, b: str = "default"):
        """
        A sample function for testing.

        Args:
            a (int): The first parameter.
            b (str, optional): The second parameter, optional.

        Returns:
            None
        """
        pass

    assert sample_function.schemafunc.openai.schema == {
        "function": {
            "description": "A sample function for testing.",
            "name": "sample_function",
            "parameters": {
                "properties": {
                    "a": {"description": "The first parameter.", "type": "integer"},
                    "b": {
                        "default": "default",
                        "description": "The second parameter, optional.",
                        "type": "string",
                    },
                },
                "required": ["a"],
                "type": "object",
            },
        },
        "type": "function",
    }


class SampleTypedDict(typing.TypedDict):
    name: str
    age: int


@pytest.mark.parametrize(
    "typ, expected",
    [
        (int, {"type": "integer"}),
        (str, {"type": "string"}),
        (typing.Union[int, str], {"type": ["integer", "string"]}),
        (typing.List[int], {"type": "array", "items": {"type": "integer"}}),
        (typing.Literal[1, "two", True], {"type": "string", "enum": [1, "two", True]}),
        (
            typing.Literal[1, "two", True, None],
            {"type": "string", "enum": [1, "two", True, None]},
        ),
        (typing.Literal[1, 2, 3], {"type": "string", "enum": [1, 2, 3]}),
        (typing.Literal["a", "b", "c"], {"type": "string", "enum": ["a", "b", "c"]}),
        (typing.Literal[True, False], {"type": "string", "enum": [True, False]}),
        (typing.Literal[None], {"type": "string", "enum": [None]}),
        (
            typing.Literal[1, "two", True, None, object()],
            pytest.raises(UnsupportedLiteralTypeError),
        ),
        (
            typing.Dict[str, int],
            {"type": "object", "additionalProperties": {"type": "integer"}},
        ),
        (
            typing.Mapping[str, int],
            {"type": "object", "additionalProperties": {"type": "integer"}},
        ),
        (
            SampleTypedDict,
            {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"},
                },
                "required": ["name", "age"],
                "additionalProperties": False,
            },
        ),
    ],
)
def test_resolve_type(typ, expected):
    if isinstance(expected, dict):
        assert resolve_type(typ) == expected
    else:
        with expected:
            resolve_type(typ)


def test_resolve_type_raises_error_for_unhandled_type():
    with pytest.raises(UnsupportedTypeError, match="Unsupported type"):
        resolve_type(complex)


def test_resolve_type_dict_str_int():
    assert resolve_type(typing.Dict[str, int]) == {
        "type": "object",
        "additionalProperties": {"type": "integer"},
    }


def test_resolve_type_dict_nested():
    assert resolve_type(typing.Dict[str, typing.List[int]]) == {
        "type": "object",
        "additionalProperties": {"type": "array", "items": {"type": "integer"}},
    }


def test_resolve_type_dict_union():
    assert resolve_type(typing.Dict[str, typing.Union[int, str]]) == {
        "type": "object",
        "additionalProperties": {"type": ["integer", "string"]},
    }


def test_resolve_type_any():
    assert resolve_type(typing.Any) == {}


def test_resolve_type_dict_any_value():
    assert resolve_type(typing.Dict[str, typing.Any]) == {
        "type": "object",
        "additionalProperties": {},
    }


def test_resolve_type_dict_non_string_key():
    with pytest.raises(UnsupportedTypeError, match="Mapping keys must be strings"):
        resolve_type(typing.Dict[int, str])


def test_resolve_type_dict_dict_values():
    assert resolve_type(typing.Dict[str, typing.Dict[str, int]]) == {
        "type": "object",
        "additionalProperties": {
            "type": "object",
            "additionalProperties": {"type": "integer"},
        },
    }


def test_resolve_type_typed_dict():
    class MyTypedDict(typing.TypedDict):
        name: str
        age: int

    assert resolve_type(MyTypedDict) == {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
        },
        "required": ["name", "age"],
        "additionalProperties": False,
    }


def test_resolve_type_typed_dict_optional_fields():
    class MyTypedDict(typing.TypedDict, total=False):
        name: str
        age: int

    assert resolve_type(MyTypedDict) == {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
        },
        "required": [],
        "additionalProperties": False,
    }


def test_resolve_type_typed_dict_nested():
    class NestedTypedDict(typing.TypedDict):
        value: int

    class MyTypedDict(typing.TypedDict):
        nested: NestedTypedDict
        other: str

    assert resolve_type(MyTypedDict) == {
        "type": "object",
        "properties": {
            "nested": {
                "type": "object",
                "properties": {
                    "value": {"type": "integer"},
                },
                "required": ["value"],
                "additionalProperties": False,
            },
            "other": {"type": "string"},
        },
        "required": ["nested", "other"],
        "additionalProperties": False,
    }


def test_resolve_type_typed_dict_union():
    class MyTypedDict(typing.TypedDict):
        value: typing.Union[int, str]

    assert resolve_type(MyTypedDict) == {
        "type": "object",
        "properties": {
            "value": {"type": ["integer", "string"]},
        },
        "required": ["value"],
        "additionalProperties": False,
    }
