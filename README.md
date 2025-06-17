# sphinx_click_custom

A Sphinx extension for documenting Click CLI commands that use custom `get_help()` methods.

## The Problem

The standard [`sphinx_click`](https://github.com/click-contrib/sphinx-click) extension is excellent for documenting Click commands, but it has a significant limitation: **it only uses the command's docstring and standard Click help output and ignores custom `get_help()` methods**.

I write a lot of CLI applications that override the `get_help()` method to provide enhanced help text with additional context, examples, or custom formatting. However, when trying to document these commands with `sphinx_click`, you lose all the custom help content.

### Example of the Problem

Consider this Click command with custom help:

```python
import click
from textwrap import dedent

class CustomCliCommand(click.Command):
    def get_help(self, ctx):
        help_text = super().get_help(ctx)
        formatter = click.HelpFormatter()
        formatter.write(dedent(f"""
        🚀 ADVANCED TOOL

        This tool provides enhanced functionality with custom help.

        {help_text}

        📝 EXAMPLES:
        - myapp process input.csv --format json
        - myapp process data.xml --format xml --limit 100

        For more help, visit: https://docs.example.com
        """))
        return formatter.getvalue()

@click.command(cls=CustomCliCommand)
@click.option("--format", type=click.Choice(["csv", "json", "xml"]), default="csv")
@click.option("--limit", type=int, help="Maximum records to process")
def process(format, limit):
    """Process data files with various formats."""
    click.echo(f"Processing with format: {format}")
```

When you run `myapp process --help` in the terminal, you see the custom help with examples and additional context. But when you document it with standard `sphinx_click`, you only get the basic docstring "Process data files with various formats." - all the custom content is lost.

## The Solution: sphinx_click_custom

`sphinx_click_custom` solves this problem by **intercepting calls to `super().get_help()`** and seamlessly integrating custom help content while maintaining sphinx_click's formatting for options, arguments, and other elements.

### Key Features

* **Preserves custom help content** - All your enhanced help text is captured
* **Maintains sphinx_click formatting** - Options, arguments, and usage are formatted identically to sphinx_click
* **Perfect inline placement** - Custom content appears exactly where you intended
* **Zero code changes required** - Works with existing custom Click commands
* **Full Click feature support** - Works with groups, subcommands, arguments, environment variables, etc.

## Installation

```bash
pip install sphinx_click_custom
```

## Development

### Testing

```bash
# Install development dependencies
pip install -e ".[test]"

pytest -vv tests/

# with coverage
pytest -vv tests/ --cov=sphinx_click_custom --cov-report=term-missing
```

### Type Checking

Ensure code passes mypy type checking:

```bash
pip install mypy
mypy sphinx_click_custom/
```

## Usage

### 1. Add to Sphinx Configuration

```python
# conf.py
extensions = [
    'sphinx_click',  # Keep this for standard commands
    'sphinx_click_custom',  # Add this for custom commands
    # ... other extensions
]
```

### 2. Document Your Commands

Use the `click-custom` directive instead of `click` for commands with custom help:

```rst
Simple Custom Help Example:
___________________________

.. click-custom:: cli_custom:cli
   :prog: cli

CLI Example with Custom Help and Groups:
__________________________

Main command group with global options:

.. click-custom:: cli_comprehensive:cli
   :prog: myapp

Process command with arguments and various option types:

.. click-custom:: cli_comprehensive:process
   :prog: myapp process
```

## Comparison: sphinx_click vs sphinx_click_custom

Let's see the difference in output for our example command:

### Standard sphinx_click Output

When using `.. click:: mymodule:process`, you get:

```
process

Process data files with various formats.

Usage: myapp process [OPTIONS]

Options:
  --format [csv|json|xml]  [default: csv]
  --limit INTEGER          Maximum records to process
  --help                   Show this message and exit.
```

**Problem**: All the custom help content (🚀 header, examples, additional notes) is completely missing!

### sphinx_click_custom Output

When using `.. click-custom:: mymodule:process`, you get:

```
process

🚀 ADVANCED TOOL

This tool provides enhanced functionality with custom help.

Process data files with various formats.

📝 EXAMPLES:
- myapp process input.csv --format json
- myapp process data.xml --format xml --limit 100

For more help, visit: https://docs.example.com

Usage: myapp process [OPTIONS]

Options:
  --format <format>        [default: csv]
                          Options: csv | json | xml
  --limit <limit>          Maximum records to process
  --help                   Show this message and exit.
```

## How It Works

The plugin uses an **interception approach**:

1. **Intercepts `super().get_help()` calls** by temporarily replacing the parent class method
2. **Captures the call location** using a unique marker
3. **Splits custom content** into "before" and "after" sections around the marker
4. **Generates sphinx-formatted sections** for usage, options, arguments, etc.
5. **Combines everything** with inline placement

This approach is robust because it doesn't try to parse the help text - it intercepts the actual method calls and replaces them with properly formatted sphinx content.

## Advanced Examples

### Groups and Subcommands

```python
class CustomGroup(click.Group):
    def get_help(self, ctx):
        help_text = super().get_help(ctx)
        return f"🎯 COMMAND GROUP\n\n{help_text}\n\n💡 TIP: Use --help with any subcommand."

@click.group(cls=CustomGroup)
def database():
    """Database management commands."""
    pass

@database.command(cls=CustomCliCommand)
@click.argument("table_name")
@click.option("--host", envvar="DB_HOST", default="localhost")
def backup(table_name, host):
    """Backup a database table."""
    pass
```

Document with:

```rst
.. click-custom:: mymodule:database
   :prog: myapp database

.. click-custom:: mymodule:backup
   :prog: myapp database backup
```

## Compatibility

- **Python**: 3.10+
- **Sphinx**: 4.0+
- **Click**: 7.0+
- **sphinx_click**: 4.0+

The plugin is designed to work alongside `sphinx_click`, not replace it. Use `sphinx_click` for standard commands and `sphinx_click_custom` for commands with custom help methods.

## When to Use This Plugin

Use `sphinx_click_custom` when you have Click commands that:

- Override the `get_help()` method
- Add custom content before/after standard help
- Include examples, additional notes, or enhanced formatting
- Need to preserve the exact structure of custom help

For standard Click commands without custom help methods, continue using the `sphinx_click` plugin.

## License

MIT License. This project incorporates code adapted from [sphinx_click](https://github.com/click-contrib/sphinx-click) under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- Built on top of the excellent [sphinx_click](https://github.com/click-contrib/sphinx-click) by Stephen Finucane
- This plugin was built with significant help from AI, specifically, [Claude code](https://www.anthropic.com/claude-code), using the Sonet 4.0 model. If you don't want to use AI generated code, then don't use this package.
