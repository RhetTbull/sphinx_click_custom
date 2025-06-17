"""Tests for nested command functionality in sphinx-click-custom."""

import click
import pytest

from sphinx_click_custom.ext import _format_command_custom, _format_subcommands


class CustomCommand(click.Command):
    """Custom Click command for testing."""

    def get_help(self, ctx):
        return f"Custom help for {self.name}\n\n{super().get_help(ctx)}"


@click.group()
def cli_group():
    """Test group with subcommands."""
    pass


@cli_group.command(cls=CustomCommand)
@click.option("--count", default=1, help="Number of items.")
def subcommand1(count):
    """First subcommand."""
    pass


@cli_group.command()
def subcommand2():
    """Second subcommand."""
    pass


@cli_group.group()
def nested():
    """Nested group."""
    pass


@nested.command(cls=CustomCommand)
def nested_cmd():
    """Command in nested group."""
    pass


def test_format_subcommands():
    """Test _format_subcommands function."""
    ctx = click.Context(cli_group)
    lines = list(_format_subcommands(ctx))

    assert len(lines) == 3  # subcommand1, subcommand2, nested
    assert ":subcommand1: First subcommand." in lines
    assert ":subcommand2: Second subcommand." in lines
    assert ":nested: Nested group." in lines


def test_format_subcommands_filtered():
    """Test _format_subcommands with command filtering."""
    ctx = click.Context(cli_group)
    lines = list(_format_subcommands(ctx, commands=["subcommand1"]))

    assert len(lines) == 1
    assert ":subcommand1: First subcommand." in lines


def test_format_subcommands_non_group():
    """Test _format_subcommands with non-group command."""
    ctx = click.Context(subcommand1)
    lines = list(_format_subcommands(ctx))

    assert len(lines) == 0


def test_group_has_subcommands():
    """Test that our test group has the expected subcommands."""
    ctx = click.Context(cli_group)
    commands = cli_group.list_commands(ctx)

    assert "subcommand1" in commands
    assert "subcommand2" in commands
    assert "nested" in commands


def test_nested_short_shows_command_list():
    """Test that nested=short shows a command list."""
    from sphinx_click_custom.ext import _format_command_custom

    ctx = click.Context(cli_group)
    lines = list(_format_command_custom(ctx, "short"))

    # Should contain rubric and command list
    lines_str = "\n".join(lines)
    assert ".. rubric:: Commands" in lines_str
    assert ":subcommand1:" in lines_str
    assert ":subcommand2:" in lines_str
    assert ":nested:" in lines_str


def test_nested_none_no_subcommands():
    """Test that nested=none doesn't show subcommands."""
    from sphinx_click_custom.ext import _format_command_custom

    ctx = click.Context(cli_group)
    lines = list(_format_command_custom(ctx, "none"))

    # Should not contain command list
    lines_str = "\n".join(lines)
    assert ".. rubric:: Commands" not in lines_str
    assert ":subcommand1:" not in lines_str


def test_nested_full_no_subcommands():
    """Test that nested=full doesn't show inline command list."""
    from sphinx_click_custom.ext import _format_command_custom

    ctx = click.Context(cli_group)
    lines = list(_format_command_custom(ctx, "full"))

    # Should not contain inline command list (handled by recursive generation)
    lines_str = "\n".join(lines)
    assert ".. rubric:: Commands" not in lines_str
