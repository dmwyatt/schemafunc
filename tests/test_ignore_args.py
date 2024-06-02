from schemafunc.schemafunc import add_schemafunc


def test_ignore_single_arg():
    @add_schemafunc(ignore_args=["arg_to_ignore"])
    def test_function(arg_to_ignore: int, arg_to_keep: str):
        """
        Test function with an argument to ignore.

        :param arg_to_ignore: This argument should be ignored.
        :param arg_to_keep: This argument should be kept.
        """
        pass

    assert test_function.schemafunc.schema == {
        "type": "function",
        "function": {
            "name": "test_function",
            "description": "Test function with an argument to ignore.",
            "parameters": {
                "type": "object",
                "properties": {
                    "arg_to_keep": {
                        "type": "string",
                        "description": "This argument should be kept.",
                    },
                },
                "required": ["arg_to_keep"],
            },
        },
    }


def test_ignore_multiple_args():
    @add_schemafunc(ignore_args=["arg1", "arg2"])
    def test_function(arg1: int, arg2: float, arg3: str):
        """
        Test function with multiple arguments to ignore.

        :param arg1: This argument should be ignored.
        :param arg2: This argument should also be ignored.
        :param arg3: This argument should be kept.
        """
        pass

    assert test_function.schemafunc.schema == {
        "type": "function",
        "function": {
            "name": "test_function",
            "description": "Test function with multiple arguments to ignore.",
            "parameters": {
                "type": "object",
                "properties": {
                    "arg3": {
                        "type": "string",
                        "description": "This argument should be kept.",
                    },
                },
                "required": ["arg3"],
            },
        },
    }
