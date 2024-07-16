from schemafunc.schemafunc import add_schemafunc


def test_ignore_args_openai_schema():
    @add_schemafunc(ignore_args=["arg_to_ignore"])
    def test_function(arg_to_ignore: int, arg_to_keep: str):
        """
        Test function with an argument to ignore.

        :param arg_to_ignore: This argument should be ignored.
        :param arg_to_keep: This argument should be kept.
        """
        pass

    assert "arg_to_ignore" not in test_function.schemafunc.openai.schema["function"]["parameters"]["properties"]
    assert "arg_to_keep" in test_function.schemafunc.openai.schema["function"]["parameters"]["properties"]

def test_ignore_args_anthropic_schema():
    @add_schemafunc(ignore_args=["arg_to_ignore"])
    def test_function(arg_to_ignore: int, arg_to_keep: str):
        """
        Test function with an argument to ignore.

        :param arg_to_ignore: This argument should be ignored.
        :param arg_to_keep: This argument should be kept.
        """
        pass

    assert "arg_to_ignore" not in test_function.schemafunc.anthropic.schema["input_schema"]["properties"]
    assert "arg_to_keep" in test_function.schemafunc.anthropic.schema["input_schema"]["properties"]
