"""Simplified integration tests."""

from sphinx_click_custom.ext import setup


def test_extension_loads(sphinx_app):
    """Test that the extension loads successfully."""
    # Extension should be loaded
    assert "sphinx_click_custom.ext" in sphinx_app.extensions


def test_extension_setup_function():
    """Test the setup function directly."""

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

    # Check directive was registered
    assert "click-custom" in app.directives

    # Check events were added
    expected_events = [
        "sphinx-click-process-description",
        "sphinx-click-process-usage",
        "sphinx-click-process-options",
        "sphinx-click-process-arguments",
        "sphinx-click-process-envvars",
        "sphinx-click-process-epilog",
    ]

    for event in expected_events:
        assert event in app.events.events

    # Check return value
    assert isinstance(result, dict)
    assert "version" in result
    assert "parallel_read_safe" in result
    assert "parallel_write_safe" in result


def test_module_imports():
    """Test that all module components can be imported."""
    # Test main module imports
    from sphinx_click_custom.ext import (
        ClickCustomDirective,
        _format_description,
        _format_help,
        _format_options,
        _format_usage,
        _get_click_object,
        setup,
    )

    # All imports should succeed
    assert ClickCustomDirective is not None
    assert _get_click_object is not None
    assert _format_help is not None
    assert _format_description is not None
    assert _format_usage is not None
    assert _format_options is not None
    assert setup is not None


def test_extension_constants():
    """Test that extension constants are defined."""
    from sphinx_click_custom.ext import NESTED_FULL, NESTED_NONE, NESTED_SHORT

    assert NESTED_FULL == "full"
    assert NESTED_SHORT == "short"
    assert NESTED_NONE == "none"
