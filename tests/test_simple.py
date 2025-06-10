"""Simple tests for core functionality."""

import click
import pytest

from sphinx_click_custom.ext import _format_help, _get_click_object, setup


def test_get_click_object_simple():
    """Test importing click objects."""
    # Test with a real click command
    cmd = _get_click_object("tests.conftest:standard_command")
    assert isinstance(cmd, click.Command)
    assert cmd.name == "standard"  # Click command name is derived from function name


def test_format_help_simple():
    """Test basic help formatting."""
    help_text = "Simple help text"
    lines = list(_format_help(help_text))
    assert len(lines) >= 1
    assert lines[0] == "Simple help text"
    assert lines[-1] == ""  # Should end with empty line


def test_extension_setup():
    """Test extension setup function."""

    class MockApp:
        def __init__(self):
            self.directives = {}
            self.events = MockEvents()

        def add_directive(self, name, directive_class):
            self.directives[name] = directive_class

        def add_event(self, name):
            self.events.add_event(name)

    class MockEvents:
        def __init__(self):
            self.events = {}

        def add_event(self, name):
            self.events[name] = True

    app = MockApp()
    result = setup(app)

    # Check that directive was added
    assert "click-custom" in app.directives

    # Check return metadata
    assert "version" in result
    assert result["parallel_read_safe"] is True
    assert result["parallel_write_safe"] is True


def test_import_errors():
    """Test error handling for import issues."""
    with pytest.raises(ValueError):
        _get_click_object("invalid_format")

    with pytest.raises(ModuleNotFoundError):
        _get_click_object("nonexistent_module:command")

    with pytest.raises(AttributeError):
        _get_click_object("tests.conftest:nonexistent_command")
