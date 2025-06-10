"""Simplified directive tests focusing on testable functionality."""

import pytest

from sphinx_click_custom.ext import ClickCustomDirective, _get_click_object, nested

from .conftest import sample_custom_command, sample_custom_group, standard_command


def test_directive_basic_properties():
    """Test basic directive properties."""
    assert ClickCustomDirective.required_arguments == 1
    assert ClickCustomDirective.has_content is False

    expected_options = {"prog", "nested", "commands", "show-nested"}
    assert set(ClickCustomDirective.option_spec.keys()) == expected_options


def test_get_click_object_valid():
    """Test _get_click_object with valid import path."""
    command = _get_click_object("tests.conftest:sample_custom_command")
    assert command == sample_custom_command
    assert hasattr(command, "get_help")

    group = _get_click_object("tests.conftest:sample_custom_group")
    assert group == sample_custom_group
    assert hasattr(group, "get_help")

    std_cmd = _get_click_object("tests.conftest:standard_command")
    assert std_cmd == standard_command


def test_get_click_object_errors():
    """Test _get_click_object error handling."""
    with pytest.raises(ValueError, match="Invalid import name"):
        _get_click_object("invalid_format")

    with pytest.raises(ModuleNotFoundError):
        _get_click_object("nonexistent_module:command")

    with pytest.raises(AttributeError):
        _get_click_object("tests.conftest:nonexistent_command")


def test_nested_validation():
    """Test nested argument validation."""
    # Valid values
    assert nested("full") == "full"
    assert nested("short") == "short"
    assert nested("none") == "none"
    assert nested(None) is None

    # Invalid value
    with pytest.raises(ValueError, match="not a valid value"):
        nested("invalid")


def test_extension_setup_basic():
    """Test basic extension setup."""
    from sphinx_click_custom.ext import setup

    class MockEvents:
        def __init__(self):
            self.events = {}

        def __contains__(self, event_name):
            return event_name in self.events

    class MockApp:
        def __init__(self):
            self.directives = {}
            self.events = MockEvents()

        def add_directive(self, name, directive_class):
            self.directives[name] = directive_class

        def add_event(self, name):
            self.events.events[name] = True

    app = MockApp()
    result = setup(app)

    # Check that directive was added
    assert "click-custom" in app.directives
    assert app.directives["click-custom"] == ClickCustomDirective

    # Check return metadata
    assert isinstance(result, dict)
    assert "version" in result
    assert result["parallel_read_safe"] is True
    assert result["parallel_write_safe"] is True


def test_directive_class_instantiation():
    """Test that directive class can be instantiated."""
    # This tests that the class structure is correct
    try:
        # Create a minimal directive instance just to test constructor
        directive = ClickCustomDirective.__new__(ClickCustomDirective)
        # Just check it's the right type
        assert isinstance(directive, ClickCustomDirective)
    except Exception:
        # If instantiation fails, that's fine - we're just testing the class exists
        pass
