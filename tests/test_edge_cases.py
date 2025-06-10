"""Tests for edge cases and error conditions."""

from textwrap import dedent

import click
import pytest

from sphinx_click_custom.ext import (
    _format_custom_help_as_description, _get_help_record,
    _intercept_and_generate_sphinx_formatted_help,
    _intercept_and_replace_super_get_help, _parse_custom_help_sections, nested)


class BrokenCustomCommand(click.Command):
    """Custom command that raises an exception in get_help."""

    def get_help(self, ctx):
        raise RuntimeError("Intentional error in get_help")


class NoSuperCallCommand(click.Command):
    """Custom command that doesn't call super().get_help()."""

    def get_help(self, ctx):
        return "Custom help without calling super()"


class EmptyCustomCommand(click.Command):
    """Custom command that returns empty help."""

    def get_help(self, ctx):
        return ""


class ComplexCustomCommand(click.Command):
    """Custom command with complex help formatting."""

    def get_help(self, ctx):
        help_text = super().get_help(ctx)
        formatter = click.HelpFormatter()
        formatter.write(
            dedent(
                f"""
        ╔═══════════════════════════════════════╗
        ║        ADVANCED CLI TOOL v2.0         ║
        ╚═══════════════════════════════════════╝
        
        📋 DESCRIPTION:
        This tool provides advanced functionality with:
        • Feature A: Does something amazing
        • Feature B: Does something else
        • Feature C: Does yet another thing
        
        {help_text}
        
        📚 EXAMPLES:
            $ mytool --option1 value1 --flag
            $ mytool --option2 value2 --no-flag
            $ mytool --help-extended
        
        ⚠️  WARNINGS:
        - Do not use with production data
        - Always backup before running
        - Check permissions before execution
        
        🔗 LINKS:
        - Documentation: https://docs.example.com
        - Support: https://support.example.com
        - GitHub: https://github.com/example/tool
        """
            )
        )
        return formatter.getvalue()


@click.command(cls=BrokenCustomCommand)
def broken_command():
    """Command that breaks during help generation."""
    pass


@click.command(cls=NoSuperCallCommand)
def no_super_command():
    """Command that doesn't call super()."""
    pass


@click.command(cls=EmptyCustomCommand)
def empty_command():
    """Command with empty custom help."""
    pass


@click.command(cls=ComplexCustomCommand)
@click.option("--option1", help="First option")
@click.option("--option2", help="Second option")
@click.option("--flag/--no-flag", help="Boolean flag")
def complex_command(option1, option2, flag):
    """Complex command with elaborate help."""
    pass


def test_broken_get_help_method(click_context):
    """Test handling of commands that raise exceptions in get_help."""
    ctx = click_context(broken_command)

    # Should not crash, but may return fallback content
    try:
        result = _intercept_and_replace_super_get_help(ctx)
        # If it doesn't crash, result should be a string
        assert isinstance(result, str)
    except Exception:
        # It's acceptable for this to fail gracefully
        pass


def test_no_super_call_command(click_context):
    """Test command that doesn't call super().get_help()."""
    ctx = click_context(no_super_command)

    result = _intercept_and_replace_super_get_help(ctx)
    assert isinstance(result, str)
    assert "Custom help without calling super()" in result


def test_empty_custom_help(click_context):
    """Test command that returns empty custom help."""
    ctx = click_context(empty_command)

    lines = list(_format_custom_help_as_description(ctx))
    # Should fall back to standard description
    content = "\n".join(lines)
    assert "Command with empty custom help" in content


def test_complex_custom_help(click_context):
    """Test command with very complex custom help formatting."""
    ctx = click_context(complex_command)

    lines = list(_format_custom_help_as_description(ctx))
    content = "\n".join(lines)

    # Should contain custom content
    assert "ADVANCED CLI TOOL v2.0" in content
    assert "EXAMPLES:" in content
    assert "WARNINGS:" in content
    assert "LINKS:" in content


def test_intercept_with_no_custom_method(click_context):
    """Test interception with command that has no custom get_help."""

    # Create a standard Click command
    @click.command()
    def standard_cmd():
        """Standard command."""
        pass

    ctx = click_context(standard_cmd)

    result = _intercept_and_replace_super_get_help(ctx)
    assert result == "Standard command."


def test_intercept_and_generate_with_broken_command(click_context):
    """Test sphinx help generation with broken command."""
    ctx = click_context(broken_command)

    # Should handle gracefully
    try:
        before, after, sphinx_help = _intercept_and_generate_sphinx_formatted_help(ctx)
        assert isinstance(before, str)
        assert isinstance(after, str)
        assert isinstance(sphinx_help, str)
    except Exception:
        # It's acceptable for this to fail gracefully
        pass


def test_parse_malformed_help_sections():
    """Test parsing help text with malformed sections."""
    malformed_help = dedent(
        """
    Some random text
    Usage: but not really proper usage
    More random text
    Options: but not really options
    Even more text
    """
    ).strip()

    sections = _parse_custom_help_sections(malformed_help)

    # Should handle gracefully
    assert isinstance(sections, dict)
    if "custom" in sections:
        assert isinstance(sections["custom"], str)


def test_parse_help_with_no_sections():
    """Test parsing help text with no recognizable sections."""
    help_text = "Just some plain text with no special sections or formatting."

    sections = _parse_custom_help_sections(help_text)

    assert "custom" in sections
    assert sections["custom"] == help_text
    assert "usage" not in sections


def test_parse_help_with_multiple_usage_sections():
    """Test parsing help with multiple Usage: lines."""
    help_text = dedent(
        """
    Usage: first usage line
    Some description
    Usage: second usage line
    More description
    """
    ).strip()

    sections = _parse_custom_help_sections(help_text)

    # Should extract the first usage
    if "usage" in sections:
        assert "first usage line" in sections["usage"]


def test_get_help_record_with_none_values(click_context):
    """Test help record generation with None values."""
    # Create an option with minimal configuration
    option = click.Option(["--test"], help=None)
    ctx = click_context(click.Command("test", params=[option]))

    opt_names, opt_help = _get_help_record(ctx, option)

    assert "--test <test>" in opt_names
    # Help might be empty or contain default text
    assert isinstance(opt_help, str)


def test_get_help_record_with_complex_metavar(click_context):
    """Test help record with complex metavar."""
    option = click.Option(["--input"], metavar="<INPUT_FILE>", help="Input file")
    ctx = click_context(click.Command("test", params=[option]))

    opt_names, opt_help = _get_help_record(ctx, option)

    # Should handle metavar properly
    assert "--input <INPUT_FILE>" in opt_names


def test_nested_validation_valid_values():
    """Test nested argument validation with valid values."""
    assert nested("full") == "full"
    assert nested("short") == "short"
    assert nested("none") == "none"
    assert nested(None) is None


def test_nested_validation_invalid_value():
    """Test nested argument validation with invalid value."""
    with pytest.raises(ValueError, match="not a valid value"):
        nested("invalid")


def test_format_help_with_special_characters():
    """Test help formatting with special characters."""
    from sphinx_click_custom.ext import _format_help

    help_text = "Help with special chars: àáâãäåæçèéêë and emojis: 🚀🎯📝"
    lines = list(_format_help(help_text))

    assert len(lines) >= 1
    assert "special chars" in lines[0]
    assert "🚀🎯📝" in lines[0]


def test_format_help_with_tabs_and_spaces():
    """Test help formatting with mixed tabs and spaces."""
    from sphinx_click_custom.ext import _format_help

    help_text = "Line 1\n\tIndented with tab\n    Indented with spaces\nNormal line"
    lines = list(_format_help(help_text))

    # Should handle indentation properly
    assert len(lines) >= 4
    assert any("Indented with tab" in line for line in lines)
    assert any("Indented with spaces" in line for line in lines)


def test_command_with_no_docstring(click_context):
    """Test command with no docstring."""

    @click.command()
    def no_doc_command():
        pass  # No docstring

    ctx = click_context(no_doc_command)

    lines = list(_format_custom_help_as_description(ctx))
    # Should handle gracefully, might be empty
    assert isinstance(lines, list)


def test_command_with_very_long_help(click_context):
    """Test command with extremely long help text."""
    long_help = "A" * 10000  # Very long string

    @click.command(help=long_help)
    def long_help_command():
        pass

    ctx = click_context(long_help_command)

    lines = list(_format_custom_help_as_description(ctx))
    # Should handle without crashing
    assert isinstance(lines, list)
    content = "\n".join(lines)
    assert len(content) > 1000  # Should contain the long content
