# sphinx_click_custom

A Sphinx extension for documenting Click CLI commands that use custom `get_help()` methods.

## The Problem

The standard [`sphinx_click`](https://github.com/click-contrib/sphinx-click) extension is excellent for documenting Click commands, but it has a significant limitation: **it only uses the command's docstring and ignores custom `get_help()` methods**.

Many advanced CLI applications override the `get_help()` method to provide enhanced help text with additional context, examples, or custom formatting. However, when you try to document these commands with `sphinx_click`, you lose all the custom help content.

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

When you run `myapp process --help` in the terminal, you see the beautiful custom help with emojis, examples, and additional context. But when you document it with standard `sphinx_click`, you only get the basic docstring "Process data files with various formats." - all the custom content is lost!

## The Solution: sphinx_click_custom

`sphinx_click_custom` solves this problem by **intercepting calls to `super().get_help()`** and seamlessly integrating custom help content while maintaining sphinx_click's superior formatting for options, arguments, and other elements.

### Key Features

✅ **Preserves custom help content** - All your enhanced help text is captured  
✅ **Maintains sphinx_click formatting** - Options, arguments, and usage are formatted identically to sphinx_click  
✅ **Perfect inline placement** - Custom content appears exactly where you intended  
✅ **Zero code changes required** - Works with existing custom Click commands  
✅ **Automatic detection** - Intelligently handles different custom help patterns  
✅ **Full Click feature support** - Works with groups, subcommands, arguments, environment variables, etc.

## Installation

```bash
pip install sphinx_click_custom
```

## Development

### Testing

The project includes a comprehensive test suite using pytest with **50 tests** and **66% code coverage**:

```bash
# Install development dependencies
pip install -e ".[test]"

# Run all tests (50 tests)
pytest tests/

# Run tests with coverage report
pytest tests/ --cov=sphinx_click_custom --cov-report=term-missing

# Run specific test categories
pytest tests/test_formatting.py -v         # Core formatting (19 tests)
pytest tests/test_edge_cases.py -v         # Edge cases & error handling (17 tests)  
pytest tests/test_simple.py -v             # Basic functionality (4 tests)
pytest tests/test_directive_simple.py -v   # Directive functionality (6 tests)
pytest tests/test_integration_simple.py -v # Integration tests (4 tests)

# Use convenient test runner script
python tests/test_runner.py --coverage
```

**Test Results**: ✅ 50/50 passing, ✅ 66% coverage, ✅ All mypy checks pass

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
.. click-custom:: mymodule:process
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

**Result**: You get ALL the custom content exactly where it should appear, PLUS professional sphinx_click formatting for the options!

## How It Works

The plugin uses an innovative **interception approach**:

1. **Intercepts `super().get_help()` calls** by temporarily replacing the parent class method
2. **Captures the call location** using a unique marker 
3. **Splits custom content** into "before" and "after" sections around the marker
4. **Generates sphinx-formatted sections** for usage, options, arguments, etc.
5. **Combines everything** with perfect inline placement

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

### Environment Variables and Complex Options

The plugin handles all Click features:

- ✅ **Environment variables** - Properly documented with `:envvar:` directives
- ✅ **Required options** - Marked with **Required** 
- ✅ **Choice constraints** - Shown as `Options: A | B | C`
- ✅ **Default values** - Formatted as `:default: value`
- ✅ **Multiple options** - `--include` (can be used multiple times)
- ✅ **Boolean flags** - `--flag/--no-flag`
- ✅ **Arguments** - Required, optional, and multiple arguments

## Compatibility

- **Python**: 3.7+
- **Sphinx**: 4.0+
- **Click**: 7.0+
- **sphinx_click**: 4.0+

The plugin is designed to work alongside `sphinx_click`, not replace it. Use `sphinx_click` for standard commands and `sphinx_click_custom` for commands with custom help methods.

## When to Use This Plugin

Use `sphinx_click_custom` when you have Click commands that:

- Override the `get_help()` method
- Add custom content before/after standard help
- Include examples, additional notes, or enhanced formatting
- Use emojis, colors, or special formatting in help text
- Need to preserve the exact structure of custom help

For standard Click commands without custom help methods, continue using the excellent `sphinx_click` plugin.

## License

MIT License. This project incorporates code adapted from [sphinx_click](https://github.com/click-contrib/sphinx-click) under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- Built on top of the excellent [sphinx_click](https://github.com/click-contrib/sphinx-click) by Stephen Finucane
- Inspired by the need to document complex CLI applications with custom help formatting