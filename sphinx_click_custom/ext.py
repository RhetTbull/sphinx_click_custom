"""Custom Sphinx extension for documenting Click commands with custom get_help() methods.

This extension extends sphinx_click to properly handle custom Click commands
that override the get_help() method to provide custom help text.
"""

import re
import typing as ty
from importlib import import_module

import click
from docutils import nodes
from docutils.parsers.rst import directives
from docutils.statemachine import ViewList
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective

logger = logging.getLogger(__name__)


def _get_click_object(import_name: str) -> click.Command:
    """Import and return a click object from a module path."""
    try:
        module_name, obj_name = import_name.rsplit(":", 1)
    except ValueError:
        raise ValueError(
            f"Invalid import name: {import_name}. Expected format: 'module:object'"
        )

    module = import_module(module_name)
    return getattr(module, obj_name)


def _format_help(help_string: str) -> ty.Generator[str, None, None]:
    """Format help text by handling ANSI escape sequences and special formatting."""
    # Remove ANSI escape sequences
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    help_string = ansi_escape.sub("", help_string)

    # Split by lines and yield each line
    for line in help_string.splitlines():
        yield line


def _format_command_custom(ctx: click.Context) -> ty.Generator[str, None, None]:
    """Format a command using its custom get_help() method if available."""
    command = ctx.command

    # Check if this is a custom command with get_help method
    if hasattr(command, "get_help") and callable(getattr(command, "get_help")):
        # Use the custom get_help() method
        try:
            help_text = command.get_help(ctx)
            yield from _format_help(help_text)
            return
        except Exception as e:
            logger.warning(
                f"Failed to get custom help for command {ctx.info_name}: {e}"
            )

    # Fallback to standard help extraction
    help_string = command.help or command.short_help
    if help_string:
        yield from _format_help(help_string)


class ClickCustomDirective(SphinxDirective):
    """Sphinx directive for documenting Click commands with custom help methods."""

    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {
        "prog": directives.unchanged,
        "nested": directives.unchanged,
        "commands": directives.unchanged,
        "show-nested": directives.flag,
    }

    def run(self) -> ty.List[nodes.Node]:
        """Generate documentation nodes for the click command."""
        import_name = self.arguments[0]

        try:
            command = _get_click_object(import_name)
        except Exception as e:
            logger.error(f"Failed to import click object '{import_name}': {e}")
            return []

        if not isinstance(command, click.Command):
            logger.error(f"Object '{import_name}' is not a Click command")
            return []

        # Get options
        prog_name = self.options.get("prog", import_name.split(":")[-1])
        show_nested = "show-nested" in self.options
        nested = self.options.get("nested", "short" if show_nested else "none")

        # Create click context
        ctx = click.Context(command, info_name=prog_name)

        # Generate content lines
        content_lines = list(_format_command_custom(ctx))

        # Create a ViewList for the content
        content: ViewList = ViewList()
        for line_num, line in enumerate(content_lines):
            content.append(line, f"<{self.name}>", line_num)

        # Parse the content as reStructuredText
        container = nodes.container()
        self.state.nested_parse(content, self.content_offset, container)

        return container.children


def setup(app):
    """Set up the Sphinx extension."""
    app.add_directive("click-custom", ClickCustomDirective)

    return {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
