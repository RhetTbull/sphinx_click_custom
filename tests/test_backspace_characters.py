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
    """Test \\b characters that are not surrounded by blank lines.

    Note: Our current implementation removes all \\b characters, so this tests
    that the content flows naturally without bar mode formatting, even when
    \\b appears inline with other content.
    """
    text_with_inline_backspace = """Regular paragraph text.
\b
This would have been bar mode in original sphinx_click.
\b
Another line that would have been bar formatted.
More regular text continues here."""

    lines = list(_format_help(text_with_inline_backspace))

    # Should not have any bar mode formatting (no lines starting with "| ")
    bar_lines = [line for line in lines if line.startswith("| ")]
    assert len(bar_lines) == 0, f"Found unexpected bar mode lines: {bar_lines}"

    # All content should be present as regular text
    expected_content = [
        "Regular paragraph text.",
        "This would have been bar mode",
        "Another line that would have been bar formatted.",
        "More regular text continues here.",
    ]

    for content in expected_content:
        found = any(content in line for line in lines)
        assert found, f"Content '{content}' should be present as regular text"

    # Should not create any code blocks for this simple text
    code_blocks = [line for line in lines if ".. code-block::" in line]
    assert len(code_blocks) == 0, f"Unexpected code blocks: {code_blocks}"


def test_demonstrates_original_bar_mode_behavior():
    """Demonstrate what the original bar mode behavior would have looked like.

    This is a documentation test showing the difference between our current
    behavior (removing \\b) and the original sphinx_click bar mode behavior.
    """
    # This is what the input would look like
    original_input = """Some intro text.
\b
Line that would be bar formatted
Another bar formatted line
\b
Back to regular text."""

    # Our current implementation simply removes \\b characters
    current_lines = list(_format_help(original_input))

    # Verify no bar mode formatting
    bar_lines = [line for line in current_lines if line.startswith("| ")]
    assert len(bar_lines) == 0

    # Content should flow as regular text
    content_found = any(
        "Line that would be bar formatted" in line for line in current_lines
    )
    assert content_found, "Content should appear as regular text"

    # This documents the intentional change: we prioritize clean paragraph flow
    # over preserving the original Click bar mode formatting behavior
