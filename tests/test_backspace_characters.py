"""Test handling of \\b characters in help text."""

import pytest

from sphinx_click_custom.ext import _format_help


def test_backspace_character_removal():
    """Test that \\b characters are removed and don't trigger bar mode."""
    text_with_backspace = """Some text before.

\b

Example content that should be regular text.

More text after."""

    lines = list(_format_help(text_with_backspace))

    # Should not contain any bar mode lines (starting with "| ")
    bar_lines = [line for line in lines if line.startswith("| ")]
    assert len(bar_lines) == 0, f"Found unexpected bar mode lines: {bar_lines}"

    # Should contain the example content as regular text
    content_found = any("Example content" in line for line in lines)
    assert content_found, "Example content should be present as regular text"

    # Should not create code blocks for this simple text
    code_blocks = [line for line in lines if ".. code-block::" in line]
    assert len(code_blocks) == 0, f"Unexpected code blocks: {code_blocks}"


def test_backspace_with_file_examples():
    """Test \\b with file naming examples (like osxphotos uses)."""
    text_with_examples = """The edited version of the file must also be named following one of these two conventions:

\b

Original: IMG_1234.jpg, edited: IMG_E1234.jpg

Original: IMG_1234.jpg, original: IMG_1234_edited.jpg"""

    lines = list(_format_help(text_with_examples))

    # Should not have bar mode formatting
    bar_lines = [line for line in lines if line.startswith("| ")]
    assert len(bar_lines) == 0

    # Both example lines should be present as regular text
    example1_found = any("IMG_E1234.jpg" in line for line in lines)
    example2_found = any("IMG_1234_edited.jpg" in line for line in lines)

    assert example1_found, "First example should be present"
    assert example2_found, "Second example should be present"


def test_backspace_mixed_with_tree_structure():
    """Test that \\b removal doesn't interfere with tree structure detection."""
    text_with_mixed = """Some description.

\b

Regular text after backspace.

Directory structure:

    /
    └── folder
        ├── file1
        └── file2

More text."""

    lines = list(_format_help(text_with_mixed))

    # Should have exactly one code block (for the tree)
    code_blocks = [line for line in lines if ".. code-block:: text" in line]
    assert len(code_blocks) == 1, f"Expected 1 code block, got {len(code_blocks)}"

    # Should not have bar mode lines
    bar_lines = [line for line in lines if line.startswith("| ")]
    assert len(bar_lines) == 0

    # Regular text should be outside code block
    regular_text_found = any("Regular text after backspace" in line for line in lines)
    assert regular_text_found, "Regular text should be preserved"


def test_multiple_backspace_characters():
    """Test handling of multiple \\b characters."""
    text_with_multiple = """Text before.

\b

First section.

\b

Second section.

\b

Third section."""

    lines = list(_format_help(text_with_multiple))

    # All sections should be regular text, no bar mode
    bar_lines = [line for line in lines if line.startswith("| ")]
    assert len(bar_lines) == 0

    # All sections should be present
    sections = ["First section.", "Second section.", "Third section."]
    for section in sections:
        found = any(section in line for line in lines)
        assert found, f"Section '{section}' should be present"


def test_backspace_without_surrounding_blank_lines():
    """Test \\b characters that are adjacent to content (legitimate bar mode)."""
    text_with_inline_backspace = """Regular paragraph text.
\b
This should be bar formatted
This should also be bar formatted
\b
More regular text continues here."""

    lines = list(_format_help(text_with_inline_backspace))

    # Should have bar mode formatting for adjacent \b
    bar_lines = [line for line in lines if line.startswith("| ")]
    assert len(bar_lines) == 2, f"Expected 2 bar mode lines, got {len(bar_lines)}"

    # Check specific bar mode content
    assert "| This should be bar formatted" in bar_lines
    assert "| This should also be bar formatted" in bar_lines

    # Regular text should not be bar formatted
    regular_lines = [
        line for line in lines if not line.startswith("| ") and line.strip()
    ]
    assert "Regular paragraph text." in regular_lines
    assert "More regular text continues here." in regular_lines


def test_floating_vs_adjacent_backspace():
    """Test the difference between floating \\b (removed) and adjacent \\b (bar mode)."""

    # Floating \b should be removed (osxphotos style)
    floating_input = """Some intro text.

\b

This should be regular text.
More regular text."""

    floating_lines = list(_format_help(floating_input))
    bar_lines = [line for line in floating_lines if line.startswith("| ")]
    assert len(bar_lines) == 0, "Floating \\b should not trigger bar mode"

    # Adjacent \b should trigger bar mode (legitimate use)
    adjacent_input = """Some intro text.
\b
This should be bar formatted
Another bar formatted line
\b
Back to regular text."""

    adjacent_lines = list(_format_help(adjacent_input))
    bar_lines = [line for line in adjacent_lines if line.startswith("| ")]
    assert len(bar_lines) == 2, "Adjacent \\b should trigger bar mode"

    assert "| This should be bar formatted" in bar_lines
    assert "| Another bar formatted line" in bar_lines
