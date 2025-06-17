"""Custom Sphinx extension for documenting Click commands with custom get_help() methods.

This extension extends sphinx_click to properly handle custom Click commands
that override the get_help() method to provide custom help text while maintaining
the same formatting and structure as the standard sphinx_click plugin.

The extension automatically detects whether custom help text includes full formatting
(Usage and Options sections) and uses it entirely, or whether it should blend custom
content with standard sphinx_click formatting. This preserves the exact inline
structure that users intended without requiring any special markers or modifications.

Code adapted from sphinx_click (https://github.com/click-contrib/sphinx-click)
License: MIT (see LICENSE file for attribution)
"""

import functools
import inspect
import re
import typing as ty
from importlib import import_module

import click
import click.core
from docutils import nodes, statemachine
from docutils.parsers.rst import directives
from sphinx.util import logging
from sphinx.util import nodes as sphinx_nodes
from sphinx.util.docutils import SphinxDirective

LOG = logging.getLogger(__name__)

# Constants from sphinx_click
NESTED_FULL = "full"
NESTED_SHORT = "short"
NESTED_NONE = "none"
NestedT = ty.Literal["full", "short", "none", None]

# Comprehensive ANSI escape sequence regex that handles all common cases
ANSI_ESC_SEQ_RE = re.compile(
    r"\x1B(?:"
    r"\[[\d;]*m|"  # Color sequences (including 24-bit RGB)
    r"\[[\d;]*[ABCDEFGHJKSTfmsu]|"  # Cursor movement and other sequences
    r"\][\d;]*(?:\x07|\x1B\\)|"  # Operating System Command sequences
    r"[PX^_].*?(?:\x07|\x1B\\)|"  # Device Control Strings
    r"\[[?]?\d*[hlr]"  # Set/reset mode sequences
    r")",
    flags=re.MULTILINE,
)

_T_Formatter = ty.Callable[[click.Context], ty.Generator[str, None, None]]

# Unicode box drawing characters for detecting ASCII art
BOX_DRAWING_CHARS = set("┌┐└┘├┤┬┴┼─│┏┓┗┛┣┫┳┻╋━┃╭╮╰╯╞╡╤╧╪╱╲╳")
TREE_CHARS = set("└├─│")


def _has_box_drawing(text: str) -> bool:
    """Check if text contains box drawing characters."""
    return any(char in BOX_DRAWING_CHARS for char in text)


def _has_tree_structure(text: str) -> bool:
    """Check if text contains tree structure characters."""
    return any(char in TREE_CHARS for char in text)


def _looks_like_ascii_art(lines: ty.List[str]) -> bool:
    """
    Determine if a block of lines looks like ASCII art that should be in a code block.

    Returns True if:
    - Contains box drawing characters
    - Contains tree structure characters
    - Has consistent indentation suggesting structure
    - Multiple lines with special characters
    - Looks like a directory tree or table structure
    """
    if not lines:
        return False

    # Check for box drawing or tree characters
    art_lines = 0
    heavily_indented = 0

    for line in lines:
        if _has_box_drawing(line) or _has_tree_structure(line):
            art_lines += 1

        # Count heavily indented lines (likely part of structured content)
        stripped = line.lstrip()
        if stripped and len(line) - len(stripped) >= 4:  # 4+ spaces of indentation
            heavily_indented += 1

    # If any lines have special characters, it's likely ASCII art
    if art_lines >= 1:
        return True

    # If most lines are heavily indented and we have multiple lines, it's structured content
    if len(lines) >= 2 and heavily_indented >= len(lines) * 0.5:
        return True

    # Check for directory-like patterns (paths with slashes)
    directory_lines = 0
    for line in lines:
        stripped = line.strip()
        if "/" in stripped and (
            stripped.startswith("/") or "└" in line or "├" in line or "│" in line
        ):
            directory_lines += 1

    if directory_lines >= 2:
        return True

    return False


def _process_lines(event_name: str) -> ty.Callable[[_T_Formatter], _T_Formatter]:
    """Process lines decorator for event hooks."""

    def decorator(func: _T_Formatter) -> _T_Formatter:
        @functools.wraps(func)
        def process_lines(ctx: click.Context) -> ty.Generator[str, None, None]:
            lines = list(func(ctx))
            if "sphinx-click-env" in ctx.meta:
                ctx.meta["sphinx-click-env"].app.events.emit(event_name, ctx, lines)
            for line in lines:
                yield line

        return process_lines

    return decorator


def _indent(text: str, level: int = 1) -> str:
    """Indent text by specified level."""
    prefix = " " * (4 * level)

    def prefixed_lines() -> ty.Generator[str, None, None]:
        for line in text.splitlines(True):
            yield (prefix + line if line.strip() else line)

    return "".join(prefixed_lines())


def _get_usage(ctx: click.Context) -> str:
    """Alternative, non-prefixed version of 'get_usage'."""
    formatter = ctx.make_formatter()
    pieces = ctx.command.collect_usage_pieces(ctx)
    formatter.write_usage(ctx.command_path, " ".join(pieces), prefix="")
    return formatter.getvalue().rstrip("\n")  # type: ignore


def _get_help_record(ctx: click.Context, opt: click.core.Option) -> ty.Tuple[str, str]:
    """Re-implementation of click.Opt.get_help_record.

    The variant of 'get_help_record' found in Click makes uses of slashes to
    separate multiple opts, and formats option arguments using upper case. This
    is not compatible with Sphinx's 'option' directive, which expects
    comma-separated opts and option arguments surrounded by angle brackets [1].

    [1] http://www.sphinx-doc.org/en/stable/domains.html#directive-option
    """

    def _write_opts(opts: ty.List[str]) -> str:
        rv, _ = click.formatting.join_options(opts)
        if not opt.is_flag and not opt.count:
            name = opt.name
            if opt.metavar:
                name = opt.metavar.lstrip("<[{($").rstrip(">]})$")
            rv += " <{}>".format(name)
        return rv  # type: ignore

    rv = [_write_opts(opt.opts)]
    if opt.secondary_opts:
        rv.append(_write_opts(opt.secondary_opts))

    out = []
    if opt.help:
        if opt.required:
            out.append("**Required** %s" % opt.help)
        else:
            out.append(opt.help)
    else:
        if opt.required:
            out.append("**Required**")

    extras = []

    # Handle show_default with proper type checking
    if opt.show_default is not None:
        show_default: ty.Union[bool, str] = opt.show_default
    elif ctx.show_default is not None:
        show_default = ctx.show_default
    else:
        show_default = False

    if isinstance(show_default, str):
        # Starting from Click 7.0 show_default can be a string. This is
        # mostly useful when the default is not a constant and
        # documentation thus needs a manually written string.
        extras.append(":default: ``%r``" % ANSI_ESC_SEQ_RE.sub("", show_default))
    elif show_default and opt.default is not None:
        extras.append(
            ":default: ``%s``"
            % (
                (
                    ", ".join(repr(d) for d in opt.default)
                    if isinstance(opt.default, (list, tuple))
                    else repr(opt.default)
                ),
            )
        )

    if isinstance(opt.type, click.Choice):
        extras.append(":options: %s" % " | ".join(str(x) for x in opt.type.choices))

    if extras:
        if out:
            out.append("")
        out.extend(extras)

    return ", ".join(rv), "\n".join(out)


def _get_click_object(import_name: str) -> click.Command:
    """Import and return a click object from a module path."""
    try:
        module_name, obj_name = import_name.rsplit(":", 1)
    except ValueError:
        raise ValueError(
            f"Invalid import name: {import_name}. Expected format: 'module:object'"
        )

    module = import_module(module_name)
    return getattr(module, obj_name)


def _format_help(help_string: str) -> ty.Generator[str, None, None]:
    """Format help text by handling ANSI escape sequences and special formatting."""
    # First, clean ANSI escape sequences
    help_string = inspect.cleandoc(ANSI_ESC_SEQ_RE.sub("", help_string))

    # Split into lines for processing
    lines = statemachine.string2lines(help_string, tab_width=4, convert_whitespace=True)

    i = 0
    bar_enabled = False

    while i < len(lines):
        line = lines[i]

        # Handle bar mode (existing click functionality)
        if line == "\b":
            bar_enabled = True
            i += 1
            continue
        if line == "":
            bar_enabled = False

        # Apply bar formatting if enabled
        if bar_enabled:
            yield "| " + line
            i += 1
            continue

        # Check for ASCII art blocks - look for patterns that suggest structured content
        should_check_for_art = (
            _has_box_drawing(line)
            or _has_tree_structure(line)
            or (
                line.strip() and len(line) - len(line.lstrip()) >= 4
            )  # Heavy indentation
        )

        if should_check_for_art:
            # Collect consecutive lines that might be part of ASCII art
            art_lines = []
            j = i

            # Look ahead to find the extent of the ASCII art block
            while j < len(lines):
                current_line = lines[j]

                # Stop at empty lines that separate blocks
                if current_line.strip() == "":
                    break

                art_lines.append(current_line)
                j += 1

                # Continue collecting if the next line looks related
                if j < len(lines) and lines[j].strip():
                    next_line = lines[j]
                    # Continue if it has special chars, heavy indentation, or matches pattern
                    continues = (
                        _has_box_drawing(next_line)
                        or _has_tree_structure(next_line)
                        or (
                            len(next_line) - len(next_line.lstrip()) >= 4
                        )  # Consistent indentation
                    )
                    if not continues:
                        break

            # If this looks like ASCII art, format as code block
            if _looks_like_ascii_art(art_lines):
                yield ""
                yield ".. code-block:: text"
                yield ""
                for art_line in art_lines:
                    yield "    " + art_line
                yield ""
                i = j
                continue

        # Regular text line
        yield line
        i += 1

    yield ""


@_process_lines("sphinx-click-process-description")
def _format_description(ctx: click.Context) -> ty.Generator[str, None, None]:
    """Format the description for a given `click.Command`.

    We parse this as reStructuredText, allowing users to embed rich
    information in their help messages if they so choose.

    For custom commands with get_help() methods, we extract and format
    the custom content while preserving the structured layout.
    """
    # Check if this is a custom command with get_help method
    if hasattr(ctx.command, "get_help") and callable(getattr(ctx.command, "get_help")):
        yield from _format_custom_help_as_description(ctx)
    else:
        # Standard description formatting
        help_string = ctx.command.help or ctx.command.short_help
        if help_string:
            yield from _format_help(help_string)


@_process_lines("sphinx-click-process-usage")
def _format_usage(ctx: click.Context) -> ty.Generator[str, None, None]:
    """Format the usage for a `click.Command`."""
    yield ".. code-block:: shell"
    yield ""
    for line in _get_usage(ctx).splitlines():
        yield _indent(line)
    yield ""


def _format_option(
    ctx: click.Context, opt: click.core.Option
) -> ty.Generator[str, None, None]:
    """Format the output for a `click.core.Option`."""
    opt_help = _get_help_record(ctx, opt)

    yield ".. option:: {}".format(opt_help[0])
    if opt_help[1]:
        yield ""
        bar_enabled = False
        for line in statemachine.string2lines(
            ANSI_ESC_SEQ_RE.sub("", opt_help[1]), tab_width=4, convert_whitespace=True
        ):
            if line == "\b":
                bar_enabled = True
                continue
            if line == "":
                bar_enabled = False
            line = "| " + line if bar_enabled else line
            yield _indent(line)


@_process_lines("sphinx-click-process-options")
def _format_options(ctx: click.Context) -> ty.Generator[str, None, None]:
    """Format all `click.Option` for a `click.Command`."""
    # the hidden attribute is part of click 7.x only hence use of getattr
    params = [
        param
        for param in ctx.command.params
        if isinstance(param, click.core.Option) and not getattr(param, "hidden", False)
    ]

    for param in params:
        for line in _format_option(ctx, param):
            yield line
        yield ""


def _format_argument(arg: click.Argument) -> ty.Generator[str, None, None]:
    """Format the output of a `click.Argument`."""
    yield ".. option:: {}".format(arg.human_readable_name)
    yield ""
    yield _indent(
        "{} argument{}".format(
            "Required" if arg.required else "Optional", "(s)" if arg.nargs != 1 else ""
        )
    )
    # Subclasses of click.Argument may add a `help` attribute (like typer.main.TyperArgument)
    help = getattr(arg, "help", None)
    if help:
        yield ""
        help_string = ANSI_ESC_SEQ_RE.sub("", help)
        for line in _format_help(help_string):
            yield _indent(line)


@_process_lines("sphinx-click-process-arguments")
def _format_arguments(ctx: click.Context) -> ty.Generator[str, None, None]:
    """Format all `click.Argument` for a `click.Command`."""
    params = [x for x in ctx.command.params if isinstance(x, click.Argument)]

    for param in params:
        for line in _format_argument(param):
            yield line
        yield ""


def _format_envvar(
    param: ty.Union[click.core.Option, click.Argument, click.Parameter],
) -> ty.Generator[str, None, None]:
    """Format the envvars of a `click.Option` or `click.Argument`."""
    yield ".. envvar:: {}".format(param.envvar)
    yield "   :noindex:"
    yield ""
    if isinstance(param, click.Argument):
        param_ref = param.human_readable_name
    else:
        # if a user has defined an opt with multiple "aliases", always use the
        # first. For example, if '--foo' or '-f' are possible, use '--foo'.
        param_ref = param.opts[0]

    yield _indent("Provide a default for :option:`{}`".format(param_ref))


@_process_lines("sphinx-click-process-envars")
def _format_envvars(ctx: click.Context) -> ty.Generator[str, None, None]:
    """Format all envvars for a `click.Command`."""

    auto_envvar_prefix = ctx.auto_envvar_prefix
    if auto_envvar_prefix is not None:
        params = []
        for param in ctx.command.params:
            if not param.envvar and param.name:
                param.envvar = f"{auto_envvar_prefix}_{param.name.upper()}"
            params.append(param)
    else:
        params = [x for x in ctx.command.params if x.envvar]

    for param in params:
        yield ".. _{command_name}-{param_name}-{envvar}:".format(
            command_name=ctx.command_path.replace(" ", "-"),
            param_name=param.name,
            envvar=param.envvar,
        )
        yield ""
        for line in _format_envvar(param):
            yield line
        yield ""


@_process_lines("sphinx-click-process-epilog")
def _format_epilog(ctx: click.Context) -> ty.Generator[str, None, None]:
    """Format the epilog for a given `click.Command`.

    We parse this as reStructuredText, allowing users to embed rich
    information in their help messages if they so choose.
    """
    if ctx.command.epilog:
        yield from _format_help(ctx.command.epilog)


def _parse_custom_help_sections(help_text: str) -> ty.Dict[str, str]:
    """Parse custom help text to extract different sections."""
    sections = {}

    # Split by common section headers
    usage_match = re.search(r"Usage:\s*([^\n]+)", help_text, re.IGNORECASE)
    if usage_match:
        sections["usage"] = usage_match.group(1).strip()

    # Extract everything else as description/custom content
    # Remove the standard sections to get custom content
    custom_content = help_text

    # Remove Usage section (sphinx_click will handle this)
    custom_content = re.sub(r"Usage:[^\n]*\n?", "", custom_content, flags=re.IGNORECASE)

    # Remove Options section completely (sphinx_click will handle this)
    # This pattern matches from "Options:" to either double newline followed by text or end of string
    custom_content = re.sub(
        r"Options:.*?(?=\n\n\w|\Z)", "", custom_content, flags=re.DOTALL | re.IGNORECASE
    )

    # Clean up extra whitespace and normalize formatting
    custom_content = re.sub(r"\n\s*\n\s*\n+", "\n\n", custom_content.strip())

    # Remove excessive indentation that might cause blockquote formatting
    lines = custom_content.splitlines()
    processed_lines = []
    for line in lines:
        # Remove leading whitespace but preserve relative indentation
        processed_lines.append(line.strip())

    custom_content = "\n".join(processed_lines)

    if custom_content:
        sections["custom"] = custom_content

    return sections


def _intercept_and_generate_sphinx_formatted_help(
    ctx: click.Context,
) -> ty.Tuple[str, str, str]:
    """Intercept super().get_help() and replace with sphinx-formatted content.

    Returns:
        Tuple of (custom_content_before, custom_content_after, sphinx_formatted_help)
    """
    command = ctx.command

    if not (hasattr(command, "get_help") and callable(getattr(command, "get_help"))):
        return "", "", ""

    custom_content_before = ""
    custom_content_after = ""

    # Temporarily replace the parent class get_help method to capture calls and context
    original_super_get_help = None
    intercepted_calls = []

    try:
        # Get the parent class (click.Command)
        parent_class = command.__class__.__bases__[0]
        if hasattr(parent_class, "get_help"):
            original_super_get_help = parent_class.get_help

            # Create a marker that we can identify in the custom help output
            sphinx_marker = "<<<SPHINX_FORMATTED_CONTENT>>>"

            # Create a method that returns our marker
            def return_marker(self, ctx_inner):
                intercepted_calls.append(ctx_inner)
                return sphinx_marker

            # Temporarily replace the parent's get_help method
            parent_class.get_help = return_marker

            # Now call the custom get_help method
            custom_help = command.get_help(ctx)

            # Split the custom help by our marker to get before/after content
            parts = custom_help.split(sphinx_marker)
            if len(parts) >= 2:
                custom_content_before = parts[0].strip()
                custom_content_after = parts[1].strip() if len(parts) > 1 else ""
            else:
                # Marker not found, treat all as custom content
                custom_content_before = custom_help.strip()

            # Generate the sphinx-formatted help content for the intercepted context
            if intercepted_calls:
                intercepted_ctx = intercepted_calls[0]

                # Generate sphinx-formatted sections as a special marker
                # We'll handle this differently in the main function
                sphinx_formatted_help = "<<<SPHINX_SECTIONS>>>"
                return (
                    custom_content_before,
                    custom_content_after,
                    sphinx_formatted_help,
                )

    except Exception as e:
        LOG.warning(
            f"Failed to intercept super().get_help() for command {ctx.info_name}: {e}"
        )

    finally:
        # Always restore the original method
        if original_super_get_help and hasattr(
            command.__class__.__bases__[0], "get_help"
        ):
            command.__class__.__bases__[0].get_help = original_super_get_help

    return custom_content_before, custom_content_after, ""


def _intercept_and_replace_super_get_help(ctx: click.Context) -> str:
    """Intercept super().get_help() calls and replace appropriately.

    Returns:
        The custom help text with super().get_help() calls handled properly
    """
    command = ctx.command

    if not (hasattr(command, "get_help") and callable(getattr(command, "get_help"))):
        # No custom get_help method
        return command.help or command.short_help or ""

    # Get the custom help directly
    try:
        custom_help = command.get_help(ctx)
    except Exception as e:
        LOG.warning(f"Failed to get custom help for command {ctx.info_name}: {e}")
        return command.help or command.short_help or ""

    # Get just the description (not the full formatted help)
    standard_description = command.help or command.short_help or ""

    # Temporarily replace the parent class get_help method to return only description
    original_super_get_help = None

    try:
        # Get the parent class (click.Command)
        parent_class = command.__class__.__bases__[0]
        if hasattr(parent_class, "get_help"):
            original_super_get_help = parent_class.get_help

            # Create a method that returns only the description instead of full help
            def return_description_only(self, ctx_inner):
                return standard_description

            # Temporarily replace the parent's get_help method
            parent_class.get_help = return_description_only

            # Now call the custom get_help method, which will get description inline
            custom_help = command.get_help(ctx)

            return custom_help

    except Exception as e:
        LOG.warning(
            f"Failed to intercept super().get_help() for command {ctx.info_name}: {e}"
        )

    finally:
        # Always restore the original method
        if original_super_get_help and hasattr(
            command.__class__.__bases__[0], "get_help"
        ):
            command.__class__.__bases__[0].get_help = original_super_get_help

    # Fallback to standard approach
    return standard_description


def _format_subcommands(
    ctx: click.Context, commands: ty.Optional[ty.List[str]] = None
) -> ty.Generator[str, None, None]:
    """Format subcommands for a click.Group."""
    multicommand = ctx.command
    if not isinstance(multicommand, click.Group):
        return

    for name in multicommand.list_commands(ctx):
        if commands is not None and name not in commands:
            continue

        command = multicommand.get_command(ctx, name)
        if command is None or command.hidden:
            continue

        short_help = command.get_short_help_str(limit=50)
        yield f":{name}: {short_help}"


def _format_custom_help_as_description(
    ctx: click.Context,
) -> ty.Generator[str, None, None]:
    """Format custom help text as description using interception approach."""
    command = ctx.command

    # Check if this is a custom command with get_help method
    if hasattr(command, "get_help") and callable(getattr(command, "get_help")):
        try:
            # Use the interception approach
            intercepted_help = _intercept_and_replace_super_get_help(ctx)

            if intercepted_help.strip():
                # Parse to remove any remaining usage/options sections
                sections = _parse_custom_help_sections(intercepted_help)
                processed_text = sections.get("custom", intercepted_help)

                if processed_text.strip():
                    yield from _format_help(processed_text)
                    return

        except Exception as e:
            LOG.warning(f"Failed to get custom help for command {ctx.info_name}: {e}")

    # Fallback to standard description if no custom help or processing failed
    help_string = ctx.command.help or ctx.command.short_help
    if help_string:
        yield from _format_help(help_string)


def _format_command_custom(
    ctx: click.Context,
    nested: NestedT,
    commands: ty.Optional[ty.List[str]] = None,
) -> ty.Generator[str, None, None]:
    """Format the output of `click.Command` with custom help support."""
    if ctx.command.hidden:
        return

    # Check if we should use intercepted sphinx formatting
    if hasattr(ctx.command, "get_help") and callable(getattr(ctx.command, "get_help")):
        try:
            before, after, sphinx_help = _intercept_and_generate_sphinx_formatted_help(
                ctx
            )

            if sphinx_help:  # Interception was successful
                # Custom content before the standard help
                if before:
                    yield from _format_help(before)

                yield ".. program:: {}".format(ctx.command_path)

                # Check if we need to generate sphinx sections
                if sphinx_help == "<<<SPHINX_SECTIONS>>>":
                    # Generate the standard sphinx sections

                    # Description (just the docstring, not full help)
                    help_text = ctx.command.help or ctx.command.short_help
                    if help_text:
                        yield from _format_help(help_text)

                    # Usage section
                    for line in _format_usage(ctx):
                        yield line

                    # Options section
                    lines = list(_format_options(ctx))
                    if lines:
                        yield ".. rubric:: Options"
                        yield ""
                        for line in lines:
                            yield line
                else:
                    # Use the provided sphinx-formatted help content
                    yield from _format_help(sphinx_help)

                # Custom content after the standard help
                if after:
                    yield from _format_help(after)

                # Handle nested commands even for custom commands
                if nested not in (NESTED_FULL, NESTED_NONE):
                    if nested == NESTED_SHORT and isinstance(ctx.command, click.Group):
                        lines = list(_format_subcommands(ctx, commands))
                        if lines:
                            yield ".. rubric:: Commands"
                            yield ""
                            for line in lines:
                                yield line

                return

        except Exception as e:
            LOG.warning(
                f"Failed to use intercepted formatting for command {ctx.info_name}: {e}"
            )

    # Fallback to standard sphinx_click formatting with custom description
    # description - use custom description formatting
    for line in _format_description(ctx):
        yield line

    yield ".. program:: {}".format(ctx.command_path)

    # usage
    for line in _format_usage(ctx):
        yield line

    # options
    lines = list(_format_options(ctx))
    if lines:
        # we use rubric to provide some separation without exploding the table
        # of contents
        yield ".. rubric:: Options"
        yield ""

    for line in lines:
        yield line

    # arguments
    lines = list(_format_arguments(ctx))
    if lines:
        yield ".. rubric:: Arguments"
        yield ""

    for line in lines:
        yield line

    # environment variables
    lines = list(_format_envvars(ctx))
    if lines:
        yield ".. rubric:: Environment variables"
        yield ""

    for line in lines:
        yield line

    # epilog
    for line in _format_epilog(ctx):
        yield line

    # if we're nesting commands, we need to do this slightly differently
    if nested in (NESTED_FULL, NESTED_NONE):
        return

    # Handle nested commands for NESTED_SHORT
    if nested == NESTED_SHORT and isinstance(ctx.command, click.Group):
        lines = list(_format_subcommands(ctx, commands))
        if lines:
            yield ".. rubric:: Commands"
            yield ""
            for line in lines:
                yield line


def nested(argument: ty.Optional[str]) -> NestedT:
    """Validate nested argument values."""
    values = (NESTED_FULL, NESTED_SHORT, NESTED_NONE, None)

    if argument not in values:
        raise ValueError(
            "%s is not a valid value for ':nested:'; allowed values: %s"
            % (argument, directives.format_values(values))
        )

    return ty.cast(NestedT, argument)


class ClickCustomDirective(SphinxDirective):
    """Sphinx directive for documenting Click commands with custom help methods."""

    has_content = False
    required_arguments = 1
    option_spec = {
        "prog": directives.unchanged_required,
        "nested": nested,
        "commands": directives.unchanged,
        "show-nested": directives.flag,
    }

    def _generate_nodes(
        self,
        name: str,
        command: click.Command,
        parent: ty.Optional[click.Context],
        nested: NestedT,
        env,
        commands: ty.Optional[ty.List[str]] = None,
    ) -> ty.List[nodes.section]:
        """Generate the relevant Sphinx nodes.

        Format a `click.Group` or `click.Command`.

        :param name: Name of command, as used on the command line
        :param command: Instance of `click.Group` or `click.Command`
        :param parent: Instance of `click.Context`, or None
        :param nested: The granularity of subcommand details.
        :param commands: Display only listed commands or skip the section if
            empty
        :returns: A list of nested docutil nodes
        """
        ctx = click.Context(command, info_name=name, parent=parent)

        if command.hidden:
            return []

        # Title
        section = nodes.section(
            "",
            nodes.title(text=name),
            ids=[nodes.make_id(ctx.command_path)],
            names=[nodes.fully_normalize_name(ctx.command_path)],
        )

        # Summary
        source_name = ctx.command_path
        result = statemachine.StringList()

        ctx.meta["sphinx-click-env"] = env
        lines = _format_command_custom(ctx, nested, commands)

        for line in lines:
            LOG.debug(line)
            result.append(line, source_name)

        sphinx_nodes.nested_parse_with_titles(self.state, result, section)

        # Handle nested commands for NESTED_FULL
        if nested == NESTED_FULL and isinstance(command, click.Group):
            subsections = self._generate_nested_nodes(ctx, nested, commands, env)
            section.extend(subsections)

        return [section]

    def _generate_nested_nodes(
        self,
        ctx: click.Context,
        nested: NestedT,
        commands: ty.Optional[ty.List[str]],
        env,
    ) -> ty.List[nodes.section]:
        """Generate nodes for nested subcommands."""
        nodes_list = []
        multicommand = ctx.command

        if not isinstance(multicommand, click.Group):
            return nodes_list

        for name in multicommand.list_commands(ctx):
            if commands is not None and name not in commands:
                continue

            command = multicommand.get_command(ctx, name)
            if command is None or command.hidden:
                continue

            # Generate documentation for this subcommand
            subsections = self._generate_nodes(name, command, ctx, nested, env)
            nodes_list.extend(subsections)

        return nodes_list

    def run(self) -> ty.List[nodes.section]:
        """Generate documentation nodes for the click command."""
        env = self.state.document.settings.env

        import_name = self.arguments[0]

        try:
            command = _get_click_object(import_name)
        except Exception as e:
            LOG.error(f"Failed to import click object '{import_name}': {e}")
            return []

        if not isinstance(command, click.Command):
            LOG.error(f"Object '{import_name}' is not a Click command")
            return []

        if "prog" not in self.options:
            raise self.error(":prog: must be specified")

        prog_name = self.options["prog"]
        show_nested = "show-nested" in self.options
        nested = self.options.get("nested")

        if show_nested:
            if nested:
                raise self.error(
                    "':nested:' and ':show-nested:' are mutually exclusive"
                )
            else:
                nested = NESTED_FULL if show_nested else NESTED_SHORT

        commands = None
        if self.options.get("commands"):
            commands = [
                command.strip() for command in self.options["commands"].split(",")
            ]

        return self._generate_nodes(prog_name, command, None, nested, env, commands)


def setup(app):
    """Set up the Sphinx extension."""
    app.add_directive("click-custom", ClickCustomDirective)

    # Add the same events as sphinx_click for compatibility
    # Only add events if they don't already exist (in case sphinx_click is also loaded)
    events_to_add = [
        "sphinx-click-process-description",
        "sphinx-click-process-usage",
        "sphinx-click-process-options",
        "sphinx-click-process-arguments",
        "sphinx-click-process-envvars",
        "sphinx-click-process-epilog",
    ]

    for event_name in events_to_add:
        if event_name not in app.events.events:
            app.add_event(event_name)

    return {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
