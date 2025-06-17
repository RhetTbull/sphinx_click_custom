"""Tests for ANSI escape sequence and ASCII art formatting."""

import pytest

from sphinx_click_custom.ext import ANSI_ESC_SEQ_RE, _format_help, _looks_like_ascii_art


def test_ansi_regex_24bit_colors():
    """Test that the ANSI regex handles 24-bit color codes."""
    text_with_24bit = (
        "\x1b[48;2;39;40;34mHello\x1b[38;2;248;248;242;48;2;39;40;34mWorld\x1b[0m"
    )

    # Should find the ANSI sequences
    matches = ANSI_ESC_SEQ_RE.findall(text_with_24bit)
    assert len(matches) >= 2

    # Should clean them properly
    cleaned = ANSI_ESC_SEQ_RE.sub("", text_with_24bit)
    assert "HelloWorld" in cleaned
    assert "\x1b[" not in cleaned


def test_box_drawing_detection():
    """Test ASCII art detection for box drawing characters."""
    box_text = """┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                              Title                              ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛"""

    lines = list(_format_help(box_text))

    # Should be wrapped in a code block
    assert ".. code-block:: text" in lines
    # Should contain the box characters properly indented
    assert any("┏━━━" in line for line in lines)
    assert any("┃" in line for line in lines)
    assert any("┗━━━" in line for line in lines)


def test_directory_tree_detection():
    """Test ASCII art detection for directory trees."""
    tree_text = """Files are organized as:

    /
    └── Photos
        ├── 2021
        │   ├── Family
        │   └── Travel
        └── 2022
            └── Work"""

    lines = list(_format_help(tree_text))

    # Should be wrapped in a code block
    assert ".. code-block:: text" in lines
    # Should contain tree characters
    assert any("└──" in line for line in lines)
    assert any("├──" in line for line in lines)
    assert any("│" in line for line in lines)


def test_mixed_content_formatting():
    """Test that mixed content (text + ASCII art) is handled correctly."""
    mixed_text = """This is regular text that should flow normally.

    Here's a directory structure:
    
        /home
        └── user
            ├── documents
            └── photos

And this is more regular text that should also flow normally."""

    lines = list(_format_help(mixed_text))

    # Should have regular text
    assert "This is regular text that should flow normally." in lines
    assert "And this is more regular text that should also flow normally." in lines

    # Should have code block for tree
    assert ".. code-block:: text" in lines
    assert any("└── user" in line for line in lines)


def test_looks_like_ascii_art_function():
    """Test the ASCII art detection function directly."""
    # Box drawing should be detected
    box_lines = [
        "┏━━━━━━━━━━━━━━━━━━━━━┓",
        "┃       Title       ┃",
        "┗━━━━━━━━━━━━━━━━━━━━━┛",
    ]
    assert _looks_like_ascii_art(box_lines) == True

    # Tree structure should be detected
    tree_lines = ["/", "└── folder", "    ├── file1", "    └── file2"]
    assert _looks_like_ascii_art(tree_lines) == True

    # Regular text should not be detected
    text_lines = [
        "This is regular text.",
        "Nothing special here.",
        "Just normal content.",
    ]
    assert _looks_like_ascii_art(text_lines) == False

    # Empty should not be detected
    assert _looks_like_ascii_art([]) == False


def test_ansi_with_tree_structure():
    """Test that ANSI sequences in tree structures are properly handled."""
    ansi_tree = """    \x1b[38;2;248;248;242;48;2;39;40;34m/\x1b[0m
    \x1b[38;2;248;248;242;48;2;39;40;34m└── Photos\x1b[0m
    \x1b[38;2;248;248;242;48;2;39;40;34m    ├── 2021\x1b[0m
    \x1b[38;2;248;248;242;48;2;39;40;34m    └── 2022\x1b[0m"""

    lines = list(_format_help(ansi_tree))

    # Should be in code block
    assert ".. code-block:: text" in lines

    # Should have ANSI sequences removed
    tree_lines = [line for line in lines if any(char in line for char in "└├")]
    assert all("\x1b[" not in line for line in tree_lines)

    # Should still have tree characters
    assert any("└── Photos" in line for line in lines)
    assert any("├── 2021" in line for line in lines)
