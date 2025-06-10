# sphinx_click_custom

A Sphinx extension for documenting Click CLI commands that use custom `get_help()` methods.

## Overview

This extension extends the standard `sphinx_click` plugin to properly handle custom Click commands that override the `get_help()` method. While the standard `sphinx_click` plugin only uses the command's docstring, this plugin can extract and format custom help text while maintaining identical formatting to `sphinx_click`.

## How It Works

The plugin automatically detects two scenarios:

1. **Full Custom Help**: When your custom `get_help()` method returns help text that includes both "Usage:" and "Options:" sections, the plugin uses the entire custom help text and preserves the exact structure you intended.

2. **Partial Custom Help**: When your custom `get_help()` method only adds custom content around the standard help, the plugin intelligently extracts just the custom content and blends it with standard `sphinx_click` formatting.

## Usage

Add the extension to your Sphinx configuration:

```python
# conf.py
extensions = [
    'sphinx_click_custom',
    # ... other extensions
]
```

Document your custom Click commands:

```rst
.. click-custom:: mymodule:my_command
   :prog: my-command
```

## Example

```python
class CustomCliCommand(click.Command):
    def get_help(self, ctx):
        help_text = super().get_help(ctx)
        formatter = click.HelpFormatter()
        formatter.write(f"""
Additional Information

This command does something special.

{help_text}

More details appear here.
""")
        return formatter.getvalue()

@click.command(cls=CustomCliCommand)
@click.option("--name", help="Name to greet")
def my_command(name):
    """My custom command"""
    click.echo(f"Hello, {name}!")
```

The plugin will automatically preserve the inline structure where the standard help appears within your custom content.

## Features

- ✅ Identical formatting to `sphinx_click`
- ✅ Automatic detection of custom help structure
- ✅ Preserves inline placement of standard content
- ✅ No code modifications required
- ✅ No duplication of sections
- ✅ Works with any custom help format

## Requirements

- Python 3.7+
- Sphinx
- Click
- sphinx_click

## License

MIT License. This project incorporates code adapted from [sphinx_click](https://github.com/click-contrib/sphinx-click).