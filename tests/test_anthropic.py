from schemafunc.schemafunc import add_schemafunc, generate_anthropic_schema


def test_generate_anthropic_schema_correct_format():
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

    schema = generate_anthropic_schema(only_built_in_type_params)

    assert schema == {
        "name": "only_built_in_type_params",
        "description": "An example function with various scalar types.",
        "input_schema": {
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
    }


def test_anthropic_func_metadata():
    @add_schemafunc
    def test_function(a: int):
        """
        Test function for decorator argument passing.

        :param a: An int parameter.
        :return: Nothing.
        """
        pass

    assert test_function.schemafunc.anthropic.schema == {
        "name": "test_function",
        "description": "Test function for decorator argument passing.",
        "input_schema": {
            "type": "object",
            "properties": {
                "a": {
                    "type": "integer",
                    "description": "An int parameter.",
                },
            },
            "required": ["a"],
        },
    }
