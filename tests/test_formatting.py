"""Tests for formatting functions in sphinx_click_custom."""

from textwrap import dedent

import click

from sphinx_click_custom.ext import (_format_arguments,
                                     _format_custom_help_as_description,
                                     _format_description, _format_envvars,
                                     _format_help, _format_options,
                                     _format_usage, _get_help_record,
                                     _get_usage,
                                     _intercept_and_replace_super_get_help,
                                     _parse_custom_help_sections)

from .conftest import CustomCliCommand, sample_custom_command, standard_command


def test_format_help_basic():
    """Test basic help text formatting."""
    help_text = "This is a test help text."
    lines = list(_format_help(help_text))

    assert len(lines) >= 2  # At least content + empty line
    assert lines[0] == "This is a test help text."
    assert lines[-1] == ""  # Ends with empty line


def test_format_help_multiline():
    """Test multiline help text formatting."""
    help_text = dedent(
        """
    This is a multiline
    help text with
    multiple paragraphs.
    
    Second paragraph here.
    """
    ).strip()

    lines = list(_format_help(help_text))
    assert len(lines) > 5
    assert "This is a multiline" in lines
    assert "Second paragraph here." in lines


def test_format_help_with_ansi():
    """Test help text with ANSI escape sequences."""
    help_text = "This is \x1b[1mbold\x1b[0m text."
    lines = list(_format_help(help_text))

    # ANSI sequences should be stripped
    assert lines[0] == "This is bold text."


def test_get_usage(click_context):
    """Test usage string generation."""
    ctx = click_context(sample_custom_command, "test-cmd")
    usage = _get_usage(ctx)

    assert "test-cmd" in usage
    assert "[OPTIONS]" in usage
    assert "INPUT_FILE" in usage


def test_format_usage(click_context):
    """Test usage formatting for Sphinx."""
    ctx = click_context(sample_custom_command, "test-cmd")
    lines = list(_format_usage(ctx))

    assert ".. code-block:: shell" in lines
    assert any("test-cmd" in line for line in lines)


def test_get_help_record_basic_option(click_context):
    """Test help record generation for basic option."""
    ctx = click_context(sample_custom_command)
    option = sample_custom_command.params[0]  # --name option

    opt_names, opt_help = _get_help_record(ctx, option)

    assert "--name <name>" in opt_names
    assert "Name to greet" in opt_help


def test_get_help_record_choice_option(click_context):
    """Test help record for choice option."""
    ctx = click_context(sample_custom_command)
    format_option = None
    for param in sample_custom_command.params:
        if hasattr(param, "name") and param.name == "format":
            format_option = param
            break

    assert format_option is not None
    opt_names, opt_help = _get_help_record(ctx, format_option)

    assert "--format <format>" in opt_names
    assert ":options: plain | fancy" in opt_help


def test_get_help_record_required_option(click_context):
    """Test help record for required option."""
    ctx = click_context(sample_custom_command)
    required_option = None
    for param in sample_custom_command.params:
        if hasattr(param, "name") and param.name == "required_opt":
            required_option = param
            break

    assert required_option is not None
    opt_names, opt_help = _get_help_record(ctx, required_option)

    assert "**Required**" in opt_help


def test_get_help_record_default_value(click_context):
    """Test help record with default value."""
    ctx = click_context(sample_custom_command)
    count_option = None
    for param in sample_custom_command.params:
        if hasattr(param, "name") and param.name == "count":
            count_option = param
            break

    assert count_option is not None
    opt_names, opt_help = _get_help_record(ctx, count_option)

    assert ":default:" in opt_help
    assert "1" in opt_help


def test_format_options(click_context):
    """Test options formatting."""
    ctx = click_context(sample_custom_command)
    lines = list(_format_options(ctx))

    assert len(lines) > 0
    assert any(".. option::" in line for line in lines)
    assert any("--name" in line for line in lines)


def test_format_arguments(click_context):
    """Test arguments formatting."""
    ctx = click_context(sample_custom_command)
    lines = list(_format_arguments(ctx))

    assert len(lines) > 0
    assert any(".. option::" in line for line in lines)
    assert any("INPUT_FILE" in line for line in lines)


def test_format_envvars(click_context):
    """Test environment variables formatting."""
    from .conftest import backup

    ctx = click_context(backup)
    lines = list(_format_envvars(ctx))

    assert len(lines) > 0
    assert any(".. envvar::" in line for line in lines)
    assert any("DB_HOST" in line for line in lines)


def test_format_description_standard_command(click_context):
    """Test description formatting for standard command."""
    ctx = click_context(standard_command)
    lines = list(_format_description(ctx))

    assert len(lines) > 0
    assert any("Standard command without custom help" in line for line in lines)


def test_format_description_custom_command(click_context):
    """Test description formatting for custom command."""
    ctx = click_context(sample_custom_command)
    lines = list(_format_description(ctx))

    # Should contain custom content
    content = "\n".join(lines)
    assert "🚀 CUSTOM HEADER" in content
    assert "Test command with custom help" in content
    assert "📝 CUSTOM FOOTER" in content


def test_intercept_and_replace_super_get_help(click_context):
    """Test interception of super().get_help() calls."""
    ctx = click_context(sample_custom_command)
    result = _intercept_and_replace_super_get_help(ctx)

    assert isinstance(result, str)
    assert len(result) > 0
    # Should contain custom content but with description replaced
    assert "🚀 CUSTOM HEADER" in result


def test_intercept_standard_command(click_context):
    """Test interception with standard command (no custom get_help)."""
    ctx = click_context(standard_command)
    result = _intercept_and_replace_super_get_help(ctx)

    # Should return the standard help/description
    assert result == standard_command.help


def test_format_custom_help_as_description(click_context):
    """Test formatting custom help as description."""
    ctx = click_context(sample_custom_command)
    lines = list(_format_custom_help_as_description(ctx))

    content = "\n".join(lines)
    assert "🚀 CUSTOM HEADER" in content
    assert "Test command with custom help" in content


def test_parse_custom_help_sections():
    """Test parsing of custom help text sections."""
    help_text = dedent(
        """
    Custom header content
    
    Usage: mycommand [OPTIONS]
    
    Description text here.
    
    Options:
      --flag    A flag option
      --help    Show help
    
    Custom footer content
    """
    ).strip()

    sections = _parse_custom_help_sections(help_text)

    # Usage should be extracted
    assert "usage" in sections
    assert "mycommand [OPTIONS]" in sections["usage"]

    # Custom content should exclude Usage and Options
    assert "custom" in sections
    custom_content = sections["custom"]
    assert "Custom header content" in custom_content
    assert "Custom footer content" in custom_content
    assert "Usage:" not in custom_content
    assert "Options:" not in custom_content


def test_parse_custom_help_sections_no_standard_sections():
    """Test parsing help text without standard sections."""
    help_text = "Just some custom content without usage or options."

    sections = _parse_custom_help_sections(help_text)

    assert "custom" in sections
    assert sections["custom"] == help_text
    assert "usage" not in sections
