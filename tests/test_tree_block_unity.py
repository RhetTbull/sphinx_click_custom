"""Test that directory trees are kept in single code blocks."""

import pytest

from sphinx_click_custom.ext import _format_help


def test_directory_tree_single_block():
    """Test that directory trees with root directory stay in one code block."""
    tree_text = """Files are organized as follows:

    /
    └── Volumes
        └── Photos
            ├── 2021
            │   ├── Family
            │   └── Travel
            └── 2022
                ├── Family
                └── Travel

This explains the structure."""

    lines = list(_format_help(tree_text))

    # Should only have one code block
    code_block_count = lines.count(".. code-block:: text")
    assert code_block_count == 1, f"Expected 1 code block, got {code_block_count}"

    # Should contain both root and tree in the output
    output_text = "\n".join(lines)
    assert "/" in output_text
    assert "└── Volumes" in output_text
    assert "├── 2021" in output_text


def test_heavily_indented_content_with_empty_lines():
    """Test that heavily indented content with empty lines stays together."""
    indented_text = """Here's some configuration:

            option1 = value1
            option2 = value2
            
            option3 = value3
            option4 = value4

That's the configuration."""

    lines = list(_format_help(indented_text))

    # Should have one code block containing all the options
    code_block_count = lines.count(".. code-block:: text")
    assert code_block_count == 1

    # All options should be in the output
    output_text = "\n".join(lines)
    assert "option1 = value1" in output_text
    assert "option2 = value2" in output_text
    assert "option3 = value3" in output_text
    assert "option4 = value4" in output_text


def test_mixed_tree_and_text():
    """Test that tree structures are separated from regular text correctly."""
    mixed_text = """This is regular text that should flow normally.

    /
    └── folder
        ├── file1
        └── file2

And this is more regular text."""

    lines = list(_format_help(mixed_text))

    # Should have one code block
    code_block_count = lines.count(".. code-block:: text")
    assert code_block_count == 1

    # Regular text should be outside the code block
    assert "This is regular text that should flow normally." in lines
    assert "And this is more regular text." in lines

    # Tree should be in code block
    code_started = False
    found_tree_in_code = False
    for line in lines:
        if ".. code-block:: text" in line:
            code_started = True
            continue
        if code_started and "└── folder" in line:
            found_tree_in_code = True
            break

    assert found_tree_in_code, "Tree structure should be in code block"
