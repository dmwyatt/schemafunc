# schemafunc

Generates an OpenAI-compatible tool schema *automatically* from a python function 
signature.

The intended use case is for LLM tool usage and output constraints.

Future updates should include explicit support for other LLMs, though the current 
functionality probably works with most or can be easily adapted.

Supports Python 3.8+.

## Output constraints?

You don't actually have to *really* want the LLM to "use a tool". You might just want 
to ensure it always returns valid JSON in a specific format.  "Function calling" or 
"tool usage" actually ends up being a great way to enforce that.  Just create a 
function whose arguments match the output you want. You don't actually have to use the 
function, but when you tell the LLM the function is available, it will constrain its 
output to match the schema of the function.


## Why?

* Manually keeping the JSON description of a python function up-to-date is 
  error-prone. Even if you use something like `pydantic` to build and enforce the 
  schema, you still end up with two sources of truth that you have to keep in sync.
* It's tedious and irritating to have to write the same information twice.
* In my experience, writing a Python function is more ergonomic, natural, and less 
  error-prone than writing a JSON schema by hand. Even if you were to use `pydantic` 
  and create a model that models the expected schema, I still find that it's not a 
  great mental model to map from a `BaseModel` to the type of "tool call" that OpenAI 
  and others expect.

## Key features

* **Automatic**: The schema is generated from the function.
  * Add `@add_schemafunc` to your function and your schema is done.
* Tool schema available as a property of the function, so you can access it easily.
  * `your_own_function.schemafunc.schema` 
* Easy tool kwargs for `openai` chat completions API.
  * `your_own_function.schemafunc.openai_tool_kwargs`
  * Use by unpacking the kwargs into the `openai` API call.
* Extracts the function description from the first line of the docstring.
* Extracts parameter descriptions from the docstring parameter list.
* Supports Numpy-style, Google-style, and RestructuredText-style docstrings.

## Installation
    
```bash
pip install schemafunc
```

## Example

### Quick Example

```python
import openai
import json
from schemafunc import add_schemafunc

@add_schemafunc  # 🪄✨ MAGIC DECORATOR
def my_awesome_tool(foo: str, bar: int):
    """
    This is a really cool tool that does something amazing.

    :param foo: A string parameter.
    :param bar: An integer parameter.
    """
    return {"foo": foo, "bar": bar}

client = openai.Client()
messages = [{"role": "user", "content": "When baz happens, use my_awesome_tool."}]
   
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=messages,
    # 🪄✨ THE MAGIC HAPPENS HERE!
    **my_awesome_tool.schemafunc.openai_tool_kwargs
)
print(json.loads(response.choices[0].message.tool_calls[0].function.arguments))
{
    "foo": "baz",
    "bar": 42
}
```

## Detailed example

You want to add a Wikipedia-searching tool to your chatbot. 

```python
from typing import List
from schemafunc import add_schemafunc

@add_schemafunc  # 🪄✨ MAGIC DECORATOR
def search_wikipedia(query: str, num_results: int = 5) -> List[str]:
    """
    Searches Wikipedia for the given query and returns the specified number of results.
    
    This will be a real function used in your code.

    :param query: The search query.
    :param num_results: The number of results to return (default: 5).
    :return: A list of search result summaries.
    """
    ...
```


Here's what the generated schema looks like:


```python
{
  "function": {
    "description": "Searches Wikipedia for the given query and returns the specified number of results.",
    "name": "search_wikipedia",
    "parameters": {
      "properties": {
        "num_results": {
          "default": 5,
          "description": "The number of results to return (default: 5).",
          "type": "integer",
        },
        "query": {"description": "The search query.", "type": "string"},
      },
      "required": ["query"],
      "type": "object",
    },
  },
  "type": "function",
}
```

However, there's not a lot of reason to see or interact with the schema. You only need 
to pass it to the LLM.  Here we use the `openai` package for interacting with GPT-3.5:

```python
from typing import Callable
import json
import openai


client = openai.Client()


def run_conversation(query: str, func: Callable):
   messages = [{"role": "user", "content": query}]
   
   response = client.chat.completions.create(
           model="gpt-3.5-turbo",
           messages=messages,
           # 🪄✨ THE MAGIC HAPPENS HERE!  
           **search_wikipedia.schemafunc.openai_tool_kwargs
   )
   return json.loads(response.choices[0].message.tool_calls[0].function.arguments)
```

And then we can use it like this:

```python
arguments = run_conversation(
        "Search Wikipedia for that cool programming language with significant whitespace.",
        search_wikipedia
)
```

Which will give you the arguments for the `search_wikipedia` function that the LLM 
decided to use.  Note how it matches up to the `search_wikipedia` function signature:


```python
print(arguments)
{
    "query": "Python",
    "num_results": 10
}
```

## Contributing

### Quick Start

1. **Fork & Clone**: Fork the project, then clone your fork and switch to a new branch for your feature or fix.

   ```bash
   git clone https://github.com/your-username/schemafunc.git
   cd schemafunc
   git checkout -b your-feature-branch
   ```

2. **Set Up Environment**: Use Poetry to install dependencies and set up your development environment.
   ```bash
   poetry install
   ```

3. **Make Changes**: Implement your feature or fix. Remember to add or update tests and documentation as needed.

4. **Test Locally**: Run the tests to ensure everything works as expected.
   ```bash
   poetry run test
   ```

5. **Commit & Push**: Commit your changes with a clear message, then push them to your fork.
   ```bash
   git commit -am "Add a brief but descriptive commit message"
   git push origin your-feature-branch
   ```

6. **Pull Request**: Open a pull request from your branch to the main `schemafunc` repository. Describe your changes and their impact.

### Guidelines

- Keep commits concise and relevant.
- Include comments in your code where necessary.
- Follow the coding style and standards of the project.

For any questions or to discuss larger changes, please open an issue first.
